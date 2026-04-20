import { apiClient } from "../lib/apiClient";

export const processPayment = async (payload: {
  booking_number: string;
  credit_card_number: string;
  security_code: string;
}) => {
  const response = await apiClient.post("/api/payments/", payload);
  return response.data as { message: string; status?: string };
};

