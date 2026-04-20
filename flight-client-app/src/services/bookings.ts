import { apiClient } from "../lib/apiClient";
import type { Booking, PaginatedResponse, PassengerInput } from "../types";

/** Create a booking that may include multiple passenger tickets. */
export const createBooking = async (payload: {
  flight_id: string;
  passengers: PassengerInput[];
}): Promise<Booking> => {
  const response = await apiClient.post("/api/bookings/", payload);
  const data = response.data as { booking?: Booking; message?: string };
  if (data.booking) {
    return data.booking;
  }
  return response.data as unknown as Booking;
};

/** List the authenticated user's bookings. */
export const getMyBookings = async (): Promise<Booking[]> => {
  const response = await apiClient.get("/api/bookings/");
  const data = response.data as PaginatedResponse<Booking>;
  return data.bookings ?? data.items ?? data.data ?? [];
};

/** Fetch one booking with full ticket details. */
export const getBookingById = async (bookingId: string): Promise<Booking> => {
  const response = await apiClient.get(`/api/bookings/${bookingId}`);
  const data = response.data as { booking?: Booking };
  if (data.booking) {
    return data.booking;
  }
  return response.data as unknown as Booking;
};

/** Cancel one booking by id. */
export const cancelBooking = async (bookingId: string): Promise<void> => {
  await apiClient.delete(`/api/bookings/${bookingId}`);
};

/** Check if a seat is available on a specific flight. */
export const checkSeatAvailability = async (params: {
  flight_id: string;
  seat_num: string;
}): Promise<boolean> => {
  const response = await apiClient.get("/api/bookings/availability", {
    params,
  });
  const data = response.data as { available?: boolean };
  return Boolean(data.available);
};

