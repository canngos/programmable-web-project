export type UserRole = "admin" | "user";

export type User = {
  id: string;
  firstname: string;
  lastname: string;
  email: string;
  role: UserRole;
};

export type AuthResponse = {
  user: User;
  token: string;
  message?: string;
};

export type Flight = {
  id: string;
  flight_code: string;
  origin_airport: string;
  destination_airport: string;
  departure_time: string;
  arrival_time: string;
  base_price: number | string;
  status: string;
};

export type PassengerInput = {
  passenger_name: string;
  passenger_passport_num: string;
  seat_num: string;
  seat_class: "economy" | "business" | "first";
};

export type Booking = {
  id: string;
  user_id: string;
  flight_id: string;
  total_price: number | string;
  booking_status: "booked" | "paid" | "cancelled" | "refunded";
  ticket_count?: number;
  created_at?: string;
  flight?: Flight;
  tickets?: Array<{
    id: string;
    passenger_name: string;
    passenger_passport_num: string;
    seat_num: string;
    seat_class: string;
    price: number | string;
    created_at?: string;
  }>;
  updated_at?: string;
};

export type PaginatedResponse<T> = {
  items?: T[];
  data?: T[];
  bookings?: T[];
  flights?: T[];
  pagination?: {
    page: number;
    per_page: number;
    total_pages: number;
    total_items: number;
    has_next: boolean;
    has_prev: boolean;
    next_page: number | null;
    prev_page: number | null;
  };
  page?: number;
  per_page?: number;
  total?: number;
  total_pages?: number;
};
