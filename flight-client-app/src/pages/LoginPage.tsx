import { zodResolver } from "@hookform/resolvers/zod";
import LockOpenIcon from "@mui/icons-material/LockOpen";
import { Box, Button, Link, Paper, Stack, TextField, Typography } from "@mui/material";
import { useMutation } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { Link as RouterLink, useNavigate } from "react-router-dom";
import { z } from "zod";
import { ApiErrorSnackbar } from "../components/ApiErrorSnackbar";
import { useAuth } from "../context/AuthContext";
import { login } from "../services/auth";

const schema = z.object({
  email: z.string().email("Enter a valid email"),
  password: z.string().min(6, "Password must be at least 6 characters"),
});

type FormValues = z.infer<typeof schema>;

export const LoginPage = () => {
  const navigate = useNavigate();
  const { setAuth } = useAuth();
  const { register, handleSubmit, formState } = useForm<FormValues>({
    resolver: zodResolver(schema),
  });

  const mutation = useMutation({
    mutationFn: login,
    onSuccess: (data) => {
      setAuth(data.token, data.user);
      navigate("/flights", { replace: true });
    },
  });

  return (
    <Box sx={{ minHeight: "100vh", display: "grid", placeItems: "center", px: 2 }}>
      <Paper sx={{ width: "100%", maxWidth: 430, p: 4 }}>
        <Stack spacing={2}>
          <ApiErrorSnackbar error={mutation.error} />
          <Stack direction="row" spacing={1} alignItems="center">
            <LockOpenIcon />
            <Typography variant="h5" fontWeight={700}>
              Flight Client Login
            </Typography>
          </Stack>
          <TextField
            label="Email"
            type="email"
            fullWidth
            {...register("email")}
            error={!!formState.errors.email}
            helperText={formState.errors.email?.message}
          />
          <TextField
            label="Password"
            type="password"
            fullWidth
            {...register("password")}
            error={!!formState.errors.password}
            helperText={formState.errors.password?.message}
          />
          <Button
            variant="contained"
            size="large"
            onClick={handleSubmit((values) => mutation.mutate(values))}
            disabled={mutation.isPending}
          >
            {mutation.isPending ? "Logging in..." : "Login"}
          </Button>
          <Typography variant="body2">
            No account? <Link component={RouterLink} to="/register">Create one here</Link>
          </Typography>
        </Stack>
      </Paper>
    </Box>
  );
};

