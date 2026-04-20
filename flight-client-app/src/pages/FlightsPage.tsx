import FlightIcon from "@mui/icons-material/Flight";
import {
  Alert,
  Button,
  Card,
  CardActions,
  CardContent,
  Chip,
  CircularProgress,
  Divider,
  Stack,
  Typography,
} from "@mui/material";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { ApiErrorSnackbar } from "../components/ApiErrorSnackbar";
import { FlightSearchForm } from "../components/FlightSearchForm";
import { formatDateTimeDdMmYyyy } from "../lib/formatDate";
import { listAirports, searchFlights, type FlightSearchFilters } from "../services/flights";
import type { Flight } from "../types";

const formatPrice = (value: number | string) => Number(value).toFixed(2);

export const FlightsPage = () => {
  const navigate = useNavigate();
  const [filters, setFilters] = useState<FlightSearchFilters>({});

  const airportsQuery = useQuery({
    queryKey: ["airports"],
    queryFn: listAirports,
  });

  const flightsQuery = useQuery({
    queryKey: ["flights", filters],
    queryFn: () => searchFlights(filters),
  });

  const startBooking = (flight: Flight) => {
    navigate("/book/new", { state: { flight } });
  };

  const pageError = airportsQuery.error ?? flightsQuery.error;

  return (
    <Stack spacing={2.5}>
      <ApiErrorSnackbar error={pageError} />
      <Typography variant="h5" fontWeight={700}>
        Search Flights
      </Typography>
      <FlightSearchForm airports={airportsQuery.data ?? []} onSubmit={setFilters} />
      {flightsQuery.isLoading && <CircularProgress />}
      {flightsQuery.data?.map((flight) => (
        <Card key={flight.id}>
          <CardContent>
            <Stack direction="row" spacing={1} alignItems="center" mb={1}>
              <FlightIcon color="primary" />
              <Typography fontWeight={700}>{flight.flight_code}</Typography>
              <Chip size="small" label={flight.status} />
            </Stack>
            <Typography>
              {flight.origin_airport} to {flight.destination_airport}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Departure: {formatDateTimeDdMmYyyy(flight.departure_time)}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Arrival: {formatDateTimeDdMmYyyy(flight.arrival_time)}
            </Typography>
            <Divider sx={{ my: 1 }} />
            <Typography fontWeight={700}>Base price: EUR {formatPrice(flight.base_price)}</Typography>
          </CardContent>
          <CardActions>
            <Button variant="contained" onClick={() => startBooking(flight)}>
              Book this flight
            </Button>
          </CardActions>
        </Card>
      ))}
      {flightsQuery.data && flightsQuery.data.length === 0 && (
        <Alert severity="info">No flights found with the selected filters.</Alert>
      )}
    </Stack>
  );
};

