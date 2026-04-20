import { Navigate, Route, Routes } from "react-router-dom";
import { AppShell } from "./components/AppShell";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { BookingWizardPage } from "./pages/BookingWizardPage";
import { BookingsPage } from "./pages/BookingsPage";
import { FlightsPage } from "./pages/FlightsPage";
import { LoginPage } from "./pages/LoginPage";
import { NotFoundPage } from "./pages/NotFoundPage";
import { PaymentPage } from "./pages/PaymentPage";
import { ProfilePage } from "./pages/ProfilePage";
import { RegisterPage } from "./pages/RegisterPage";
import { AdminPanelPage } from "./pages/AdminPanelPage";

function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <AppShell />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="/flights" replace />} />
        <Route path="flights" element={<FlightsPage />} />
        <Route path="book/new" element={<BookingWizardPage />} />
        <Route path="bookings" element={<BookingsPage />} />
        <Route path="bookings/:bookingId/pay" element={<PaymentPage />} />
        <Route path="profile" element={<ProfilePage />} />
        <Route path="admin" element={<AdminPanelPage />} />
      </Route>
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}

export default App;
