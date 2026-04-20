# Flight Client App

Web client for the Flight Management System API, implemented with React + Vite + TypeScript + MUI.

This client supports end-to-end passenger workflows: account creation/login, flight search, multi-passenger booking, booking detail/ticket inspection, cancellation, payment, and profile updates.

## Stack

- React 19 + TypeScript
- Vite
- MUI (Material UI)
- React Router
- TanStack React Query
- React Hook Form + Zod
- Axios

## API Resources and Methods Used

| Resource | Method | Used for |
| --- | --- | --- |
| `/api/users/register` | `POST` | User registration |
| `/api/users/login` | `POST` | User login and token retrieval |
| `/api/users/me` | `GET` | Load profile data |
| `/api/users/me` | `PATCH` | Update profile data |
| `/api/flights/airports` | `GET` | Origin/destination dropdowns |
| `/api/flights/search` | `GET` | Filtered flight search |
| `/api/bookings/availability` | `GET` | Seat availability checks in booking wizard |
| `/api/bookings/` | `POST` | Create booking with one or more passengers |
| `/api/bookings/` | `GET` | Booking list |
| `/api/bookings/{id}` | `GET` | Booking details with ticket rows |
| `/api/bookings/{id}` | `DELETE` | Booking cancellation |
| `/api/payments/` | `POST` | Booking payment |

## Prerequisites

- Node.js 20 or newer
- Backend services running (Flask + DB + NGINX)
- API reachable at `http://localhost:8080` (default setup in this project)

## Installation and Setup

From `flight-client-app`:

```bash
npm install
```

Create `.env` in this folder:

```bash
VITE_API_BASE_URL=http://localhost:8080
```

## Run (Development)

```bash
npm run dev
```

Open the local URL shown by Vite (typically `http://localhost:5173`).

## Build and Lint

```bash
npm run lint
npm run build
npm run preview
```

## Main Features

1. **Authentication**
   - Register and login pages with form validation
   - JWT persisted in local storage and applied to API requests
   - Protected routes for authenticated pages

2. **Flight search**
   - Search by origin, destination, departure date, and arrival date
   - Flight cards show route, times, status, and base price

3. **Booking wizard (multi-step)**
   - Step 1: Flight confirmation
   - Step 2: Multi-passenger input (1-10 passengers)
   - Step 3: Review and confirm
   - Seats are assigned only after availability checks (`/api/bookings/availability`)
   - One booking can include multiple tickets for different people

4. **Bookings page**
   - Booking cards with status and ticket count
   - Clickable booking card opens detail dialog
   - Detail dialog shows ticket table (passenger, passport, seat, class, price)
   - Cancel and pay actions available in both card and detail view

5. **Profile**
   - Profile fetch and update with validation and feedback

## Sources and Credits

The implementation uses official documentation and APIs from:

- React docs: [https://react.dev/](https://react.dev/)
- Vite docs: [https://vite.dev/](https://vite.dev/)
- MUI docs: [https://mui.com/material-ui/](https://mui.com/material-ui/)
- TanStack React Query docs: [https://tanstack.com/query/latest](https://tanstack.com/query/latest)
- React Hook Form docs: [https://react-hook-form.com/](https://react-hook-form.com/)
- Zod docs: [https://zod.dev/](https://zod.dev/)
- Axios docs: [https://axios-http.com/docs/intro](https://axios-http.com/docs/intro)

No external template code was copied directly beyond standard library/framework usage patterns.
