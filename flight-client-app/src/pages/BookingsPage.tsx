import CloseIcon from "@mui/icons-material/Close";
import PaymentsIcon from "@mui/icons-material/Payments";
import {
  Alert,
  Box,
  Button,
  Card,
  CardActionArea,
  CardActions,
  CardContent,
  CircularProgress,
  Dialog,
  DialogContent,
  DialogTitle,
  IconButton,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { ApiErrorSnackbar } from "../components/ApiErrorSnackbar";
import { useAuth } from "../context/AuthContext";
import { formatDateTimeDdMmYyyy } from "../lib/formatDate";
import { cancelBooking, getBookingById, getMyBookings } from "../services/bookings";
import { getFlightsByIds } from "../services/flights";
import type { Booking, Flight } from "../types";

const formatPrice = (value: number | string) => Number(value).toFixed(2);

function flightRouteLabel(flight: Flight | undefined): string | null {
  if (!flight?.origin_airport || !flight?.destination_airport) {
    return null;
  }
  return `${flight.origin_airport} → ${flight.destination_airport}`;
}

export const BookingsPage = () => {
  const queryClient = useQueryClient();
  const { token, user } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const paymentMessage = (location.state as { paymentMessage?: string } | null)?.paymentMessage;
  const [detailBookingId, setDetailBookingId] = useState<string | null>(null);

  const bookingsQuery = useQuery({
    queryKey: ["bookings", user?.id],
    queryFn: getMyBookings,
    enabled: Boolean(token),
  });

  const detailQuery = useQuery({
    queryKey: ["booking", user?.id, detailBookingId],
    queryFn: () => getBookingById(detailBookingId!),
    enabled: Boolean(token && detailBookingId),
  });

  const flightIdsForLookup = useMemo(() => {
    const ids = new Set<string>();
    bookingsQuery.data?.forEach((b) => ids.add(b.flight_id));
    const detailFid = detailQuery.data?.flight_id;
    if (detailFid) ids.add(detailFid);
    return [...ids];
  }, [bookingsQuery.data, detailQuery.data?.flight_id]);

  const flightIdsKey = useMemo(() => [...flightIdsForLookup].sort().join(","), [flightIdsForLookup]);

  const flightsLookupQuery = useQuery({
    queryKey: ["flights-for-bookings", user?.id, flightIdsKey],
    queryFn: () => getFlightsByIds(flightIdsForLookup),
    enabled: flightIdsForLookup.length > 0,
  });

  const flightById = flightsLookupQuery.data ?? new Map<string, Flight>();

  const cancelMutation = useMutation({
    mutationFn: cancelBooking,
    onSuccess: (_void, cancelledId) => {
      queryClient.invalidateQueries({ queryKey: ["bookings"] });
      queryClient.removeQueries({ queryKey: ["booking", cancelledId] });
      setDetailBookingId((current) => (current === cancelledId ? null : current));
    },
  });

  const payBooking = (booking: Booking) => {
    navigate(`/bookings/${booking.id}/pay`);
  };

  const detailBooking = detailQuery.data;

  const pageError =
    bookingsQuery.error ??
    detailQuery.error ??
    cancelMutation.error ??
    flightsLookupQuery.error;

  return (
    <Stack spacing={2.5}>
      <ApiErrorSnackbar error={pageError} />
      <Typography variant="h5" fontWeight={700}>
        My Bookings
      </Typography>
      {paymentMessage && <Alert severity="success">{paymentMessage}</Alert>}
      {bookingsQuery.isLoading && <CircularProgress />}

      {bookingsQuery.data?.map((booking) => {
        const flight = flightById.get(booking.flight_id);
        const route = flightRouteLabel(flight);
        return (
        <Card key={booking.id} variant="outlined">
          <CardActionArea onClick={() => setDetailBookingId(booking.id)}>
            <CardContent>
              <Typography fontWeight={700}>Booking #{booking.id.slice(0, 8)}…</Typography>
              {flightsLookupQuery.isLoading && !flight && (
                <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                  Loading flight…
                </Typography>
              )}
              {route && (
                <Typography variant="body1" fontWeight={600} sx={{ mt: 0.5 }}>
                  {route}
                </Typography>
              )}
              <Typography variant="body2" color="text.secondary">
                Flight {flight?.flight_code ?? booking.flight_id}
                {flight?.departure_time && (
                  <> · Departs {formatDateTimeDdMmYyyy(flight.departure_time)}</>
                )}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Status: {booking.booking_status}
              </Typography>
              {typeof booking.ticket_count === "number" && (
                <Typography variant="body2" color="text.secondary">
                  Tickets: {booking.ticket_count}
                </Typography>
              )}
              <Typography sx={{ mt: 1 }}>Total: EUR {formatPrice(booking.total_price)}</Typography>
              <Typography variant="caption" color="primary" sx={{ display: "block", mt: 1 }}>
                Tap for details and tickets
              </Typography>
            </CardContent>
          </CardActionArea>
          <CardActions sx={{ px: 2, pb: 2, pt: 0, justifyContent: "flex-end", gap: 1 }}>
            <Button
              size="small"
              variant="outlined"
              color="error"
              onClick={(e) => {
                e.stopPropagation();
                cancelMutation.mutate(booking.id);
              }}
              disabled={
                cancelMutation.isPending ||
                booking.booking_status === "cancelled" ||
                booking.booking_status === "paid"
              }
            >
              Cancel
            </Button>
            <Button
              size="small"
              startIcon={<PaymentsIcon />}
              variant="contained"
              onClick={(e) => {
                e.stopPropagation();
                payBooking(booking);
              }}
              disabled={booking.booking_status === "paid" || booking.booking_status === "cancelled"}
            >
              Pay
            </Button>
          </CardActions>
        </Card>
        );
      })}

      {bookingsQuery.data && bookingsQuery.data.length === 0 && (
        <Alert severity="info">You do not have any bookings yet.</Alert>
      )}

      <Dialog
        fullWidth
        maxWidth="md"
        open={Boolean(detailBookingId)}
        onClose={() => setDetailBookingId(null)}
        aria-labelledby="booking-detail-title"
      >
        <DialogTitle id="booking-detail-title" sx={{ pr: 6 }}>
          Booking details
          <IconButton
            aria-label="close"
            onClick={() => setDetailBookingId(null)}
            sx={{ position: "absolute", right: 8, top: 8 }}
          >
            <CloseIcon />
          </IconButton>
        </DialogTitle>
        <DialogContent dividers>
          {detailQuery.isLoading && (
            <Stack alignItems="center" py={4}>
              <CircularProgress />
            </Stack>
          )}
          {detailBooking && (
            <Stack spacing={2}>
              <Box>
                <Typography variant="caption" color="text.secondary">
                  Booking ID
                </Typography>
                <Typography variant="body2" sx={{ wordBreak: "break-all" }}>
                  {detailBooking.id}
                </Typography>
              </Box>
              {(() => {
                const flight = flightById.get(detailBooking.flight_id);
                if (flightsLookupQuery.isLoading && !flight) {
                  return (
                    <Typography variant="body2" color="text.secondary">
                      Loading flight details…
                    </Typography>
                  );
                }
                if (!flight) return null;
                return (
                <Box
                  sx={{
                    p: 2,
                    borderRadius: 1,
                    bgcolor: "action.hover",
                    border: 1,
                    borderColor: "divider",
                  }}
                >
                  <Typography variant="caption" color="text.secondary">
                    Route
                  </Typography>
                  <Typography variant="h6" fontWeight={700}>
                    {flight.origin_airport} → {flight.destination_airport}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {flight.flight_code}
                    {flight.departure_time && flight.arrival_time && (
                      <>
                        {" · "}
                        {formatDateTimeDdMmYyyy(flight.departure_time)} –{" "}
                        {formatDateTimeDdMmYyyy(flight.arrival_time)}
                      </>
                    )}
                  </Typography>
                </Box>
                );
              })()}
              <Stack direction={{ xs: "column", sm: "row" }} spacing={2} flexWrap="wrap">
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    Flight ID
                  </Typography>
                  <Typography variant="body2" sx={{ wordBreak: "break-all" }}>
                    {detailBooking.flight_id}
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    Status
                  </Typography>
                  <Typography variant="body2">{detailBooking.booking_status}</Typography>
                </Box>
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    Total
                  </Typography>
                  <Typography variant="body2">EUR {formatPrice(detailBooking.total_price)}</Typography>
                </Box>
              </Stack>
              {detailBooking.created_at && (
                <Typography variant="body2" color="text.secondary">
                  Created: {formatDateTimeDdMmYyyy(detailBooking.created_at)}
                </Typography>
              )}

              <Typography variant="subtitle1" fontWeight={700} sx={{ pt: 1 }}>
                Tickets ({detailBooking.tickets?.length ?? 0})
              </Typography>
              {detailBooking.tickets && detailBooking.tickets.length > 0 ? (
                <Table size="small" sx={{ border: 1, borderColor: "divider", borderRadius: 1 }}>
                  <TableHead>
                    <TableRow>
                      <TableCell>Passenger</TableCell>
                      <TableCell>Passport</TableCell>
                      <TableCell>Seat</TableCell>
                      <TableCell>Class</TableCell>
                      <TableCell align="right">Price</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {detailBooking.tickets.map((t) => (
                      <TableRow key={t.id}>
                        <TableCell>{t.passenger_name}</TableCell>
                        <TableCell>{t.passenger_passport_num}</TableCell>
                        <TableCell>{t.seat_num}</TableCell>
                        <TableCell>{t.seat_class}</TableCell>
                        <TableCell align="right">EUR {formatPrice(t.price)}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              ) : (
                <Typography variant="body2" color="text.secondary">
                  No ticket rows returned for this booking.
                </Typography>
              )}

              <Stack direction="row" spacing={1} justifyContent="flex-end" sx={{ pt: 2 }}>
                <Button
                  variant="outlined"
                  color="error"
                  onClick={() => cancelMutation.mutate(detailBooking.id)}
                  disabled={
                    cancelMutation.isPending ||
                    detailBooking.booking_status === "cancelled" ||
                    detailBooking.booking_status === "paid"
                  }
                >
                  Cancel booking
                </Button>
                <Button
                  variant="contained"
                  startIcon={<PaymentsIcon />}
                  onClick={() => payBooking(detailBooking)}
                  disabled={detailBooking.booking_status === "paid" || detailBooking.booking_status === "cancelled"}
                >
                  Pay
                </Button>
              </Stack>
            </Stack>
          )}
        </DialogContent>
      </Dialog>
    </Stack>
  );
};
