import SearchIcon from "@mui/icons-material/Search";
import { Box, Button, MenuItem, Paper, Stack, TextField } from "@mui/material";
import { useForm } from "react-hook-form";
import type { FlightSearchFilters } from "../services/flights";

type Props = {
  airports: string[];
  onSubmit: (values: FlightSearchFilters) => void;
};

export const FlightSearchForm = ({ airports, onSubmit }: Props) => {
  const { register, handleSubmit } = useForm<FlightSearchFilters>({
    defaultValues: {
      page: 1,
      per_page: 10,
    },
  });

  return (
    <Paper sx={{ p: 2.5, mb: 3 }}>
      <Stack direction={{ xs: "column", md: "row" }} spacing={2}>
        <Box sx={{ flex: 1 }}>
          <TextField select fullWidth label="Origin airport" {...register("origin_airport")}>
            <MenuItem value="">All</MenuItem>
            {airports.map((airport) => (
              <MenuItem key={airport} value={airport}>
                {airport}
              </MenuItem>
            ))}
          </TextField>
        </Box>
        <Box sx={{ flex: 1 }}>
          <TextField select fullWidth label="Destination airport" {...register("destination_airport")}>
            <MenuItem value="">All</MenuItem>
            {airports.map((airport) => (
              <MenuItem key={airport} value={airport}>
                {airport}
              </MenuItem>
            ))}
          </TextField>
        </Box>
        <Box sx={{ flex: 1 }}>
          <TextField
            fullWidth
            label="Departure date"
            type="date"
            InputLabelProps={{ shrink: true }}
            inputProps={{ lang: "en-GB" }}
            {...register("departure_date")}
          />
        </Box>
        <Box sx={{ minWidth: { md: 140 } }}>
          <Button
            fullWidth
            variant="contained"
            startIcon={<SearchIcon />}
            onClick={handleSubmit(onSubmit)}
            sx={{ height: "100%" }}
          >
            Search
          </Button>
        </Box>
      </Stack>
    </Paper>
  );
};

