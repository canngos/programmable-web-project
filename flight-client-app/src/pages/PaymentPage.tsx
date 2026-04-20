import CreditCardIcon from "@mui/icons-material/CreditCard";
import LockIcon from "@mui/icons-material/Lock";
import {
  Alert,
  Button,
  Card,
  CardContent,
  CircularProgress,
  InputAdornment,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { ApiErrorSnackbar } from "../components/ApiErrorSnackbar";
import { getBookingById } from "../services/bookings";
import { processPayment } from "../services/payments";

const formatPrice = (value: number | string) => Number(value).toFixed(2);

export const PaymentPage = () => {
  const { bookingId = "" } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [creditCardNumber, setCreditCardNumber] = useState("");
  const [securityCode, setSecurityCode] = useState("");
  const [validationMessage, setValidationMessage] = useState<string | null>(null);

  const bookingQuery = useQuery({
    queryKey: ["booking", bookingId],
    queryFn: () => getBookingById(bookingId),
    enabled: Boolean(bookingId),
  });

  const paymentMutation = useMutation({
    mutationFn: processPayment,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["bookings"] });
      queryClient.invalidateQueries({ queryKey: ["booking", bookingId] });
      navigate("/bookings", {
        replace: true,
        state: { paymentMessage: data.message ?? "Payment successful. Booking confirmed." },
      });
    },
  });

  const submitPayment = () => {
    setValidationMessage(null);
    if (!bookingId) {
      setValidationMessage("Invalid booking.");
      return;
    }
    if (!/^\d{16}$/.test(creditCardNumber)) {
      setValidationMessage("Credit card number must be 16 digits.");
      return;
    }
    if (!/^\d{3}$/.test(securityCode)) {
      setValidationMessage("Security code must be 3 digits.");
      return;
    }
    paymentMutation.mutate({
      booking_number: bookingId,
      credit_card_number: creditCardNumber,
      security_code: securityCode,
    });
  };

  const booking = bookingQuery.data;
  const cannotPay = booking?.booking_status === "paid" || booking?.booking_status === "cancelled";

  return (
    <Stack spacing={2.5} maxWidth={520}>
      <ApiErrorSnackbar error={paymentMutation.error ?? bookingQuery.error} />
      <Typography variant="h5" fontWeight={700}>
        Payment
      </Typography>
      <Card variant="outlined">
        <CardContent>
          {bookingQuery.isLoading && <CircularProgress />}
          {booking && (
            <Stack spacing={1.2}>
              <Typography variant="body2" color="text.secondary">
                Booking ID
              </Typography>
              <Typography variant="body2" sx={{ wordBreak: "break-all" }}>
                {booking.id}
              </Typography>
              <Typography variant="body2">Status: {booking.booking_status}</Typography>
              <Typography fontWeight={700}>Total amount: EUR {formatPrice(booking.total_price)}</Typography>
              {cannotPay && (
                <Alert severity="warning">
                  This booking cannot be paid because it is already {booking.booking_status}.
                </Alert>
              )}
            </Stack>
          )}
        </CardContent>
      </Card>

      {validationMessage && <Alert severity="warning">{validationMessage}</Alert>}

      <TextField
        label="Credit card number"
        placeholder="16 digits"
        value={creditCardNumber}
        onChange={(e) => setCreditCardNumber(e.target.value.replace(/\D/g, "").slice(0, 16))}
        inputProps={{ inputMode: "numeric", maxLength: 16 }}
        InputProps={{
          startAdornment: (
            <InputAdornment position="start">
              <CreditCardIcon sx={{ color: "text.secondary" }} />
            </InputAdornment>
          ),
        }}
        fullWidth
        disabled={paymentMutation.isPending || bookingQuery.isLoading || cannotPay}
      />
      <TextField
        label="Security code"
        placeholder="3 digits"
        value={securityCode}
        onChange={(e) => setSecurityCode(e.target.value.replace(/\D/g, "").slice(0, 3))}
        inputProps={{ inputMode: "numeric", maxLength: 3 }}
        InputProps={{
          startAdornment: (
            <InputAdornment position="start">
              <LockIcon sx={{ color: "text.secondary" }} />
            </InputAdornment>
          ),
        }}
        fullWidth
        disabled={paymentMutation.isPending || bookingQuery.isLoading || cannotPay}
      />
      <Stack direction="row" spacing={1} justifyContent="flex-end">
        <Button onClick={() => navigate("/bookings")} disabled={paymentMutation.isPending}>
          Cancel
        </Button>
        <Button
          variant="contained"
          onClick={submitPayment}
          disabled={paymentMutation.isPending || bookingQuery.isLoading || cannotPay}
        >
          {paymentMutation.isPending ? "Processing..." : "Pay now"}
        </Button>
      </Stack>
    </Stack>
  );
};
