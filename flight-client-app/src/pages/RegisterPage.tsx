import { zodResolver } from "@hookform/resolvers/zod";
import PersonAddAltIcon from "@mui/icons-material/PersonAddAlt";
import { Box, Button, Link, Paper, Stack, TextField, Typography } from "@mui/material";
import { useMutation } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { Link as RouterLink, useNavigate } from "react-router-dom";
import { z } from "zod";
import { ApiErrorSnackbar } from "../components/ApiErrorSnackbar";
import { useAuth } from "../context/AuthContext";
import { register as registerUser } from "../services/auth";

const schema = z
  .object({
    firstname: z.string().min(1, "Required"),
    lastname: z.string().min(1, "Required"),
    email: z.string().email("Enter a valid email"),
    password: z.string().min(6, "Password must be at least 6 characters"),
    confirmPassword: z.string(),
  })
  .refine((value) => value.password === value.confirmPassword, {
    path: ["confirmPassword"],
    message: "Passwords do not match",
  });

type FormValues = z.infer<typeof schema>;

export const RegisterPage = () => {
  const navigate = useNavigate();
  const { setAuth } = useAuth();
  const { register, handleSubmit, formState } = useForm<FormValues>({
    resolver: zodResolver(schema),
  });

  const mutation = useMutation({
    mutationFn: registerUser,
    onSuccess: (data) => {
      setAuth(data.token, data.user);
      navigate("/flights", { replace: true });
    },
  });

  return (
    <Box sx={{ minHeight: "100vh", display: "grid", placeItems: "center", px: 2 }}>
      <Paper sx={{ width: "100%", maxWidth: 460, p: 4 }}>
        <Stack spacing={2}>
          <ApiErrorSnackbar error={mutation.error} />
          <Stack direction="row" spacing={1} alignItems="center">
            <PersonAddAltIcon />
            <Typography variant="h5" fontWeight={700}>
              Create Account
            </Typography>
          </Stack>
          <TextField
            label="First name"
            fullWidth
            {...register("firstname")}
            error={!!formState.errors.firstname}
            helperText={formState.errors.firstname?.message}
          />
          <TextField
            label="Last name"
            fullWidth
            {...register("lastname")}
            error={!!formState.errors.lastname}
            helperText={formState.errors.lastname?.message}
          />
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
          <TextField
            label="Confirm password"
            type="password"
            fullWidth
            {...register("confirmPassword")}
            error={!!formState.errors.confirmPassword}
            helperText={formState.errors.confirmPassword?.message}
          />
          <Button
            variant="contained"
            size="large"
            onClick={handleSubmit((values) =>
              mutation.mutate({
                firstname: values.firstname,
                lastname: values.lastname,
                email: values.email,
                password: values.password,
                role: "user",
              }),
            )}
            disabled={mutation.isPending}
          >
            {mutation.isPending ? "Creating..." : "Create account"}
          </Button>
          <Typography variant="body2">
            Already registered? <Link component={RouterLink} to="/login">Login</Link>
          </Typography>
        </Stack>
      </Paper>
    </Box>
  );
};

