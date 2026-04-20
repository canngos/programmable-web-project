import { Box, Button, Stack, Typography } from "@mui/material";
import { Link as RouterLink } from "react-router-dom";

export const NotFoundPage = () => {
  return (
    <Box sx={{ minHeight: "100vh", display: "grid", placeItems: "center", px: 2 }}>
      <Stack spacing={2} alignItems="center">
        <Typography variant="h3" fontWeight={800}>
          404
        </Typography>
        <Typography>Page not found.</Typography>
        <Button component={RouterLink} to="/flights" variant="contained">
          Back to flights
        </Button>
      </Stack>
    </Box>
  );
};

