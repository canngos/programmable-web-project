import { Alert, Snackbar } from "@mui/material";
import { useMemo, useState } from "react";
import { getApiErrorMessage } from "../lib/apiClient";

type Props = {
  /** First non-nullish error wins (merge in parent with `??`). */
  error: unknown | null | undefined;
};

export function ApiErrorSnackbar({ error }: Props) {
  const [dismissedError, setDismissedError] = useState<unknown>(null);
  const message = useMemo(() => {
    if (error == null) return "";
    return getApiErrorMessage(error);
  }, [error]);
  const open = Boolean(message) && error !== dismissedError;

  return (
    <Snackbar
      open={open}
      autoHideDuration={12_000}
      onClose={(_event, reason) => {
        if (reason === "clickaway") return;
        setDismissedError(error);
      }}
      anchorOrigin={{ vertical: "top", horizontal: "center" }}
    >
      <Alert
        severity="error"
        variant="filled"
        onClose={() => setDismissedError(error)}
        sx={{ width: "100%", maxWidth: 560, alignItems: "center" }}
      >
        {message}
      </Alert>
    </Snackbar>
  );
}
