CREATE TABLE "users" (
  "id" UUID PRIMARY KEY,
  "firstName" varchar NOT NULL,
  "lastName" varchar NOT NULL,
  "email" varchar UNIQUE NOT NULL,
  "password_hash" varchar NOT NULL,
  "role" varchar,
  "created_at" timestamp,
  "updated_at" timestamp
);

CREATE TABLE "flights" (
  "id" UUID PRIMARY KEY,
  "flight_code" varchar UNIQUE,
  "origin_airport" varchar,
  "destination_airport" varchar,
  "departure_time" timestamp,
  "arrival_time" timestamp,
  "base_price" decimal,
  "status" varchar,
  "created_at" timestamp,
  "updated_at" timestamp
);

CREATE TABLE "bookings" (
  "id" UUID PRIMARY KEY,
  "user_id" UUID,
  "flight_id" UUID,
  "total_price" decimal,
  "status" varchar,
  "created_at" timestamp,
  "updated_at" timestamp
);

CREATE TABLE "tickets" (
  "id" UUID PRIMARY KEY,
  "booking_id" UUID,
  "passenger_name" varchar,
  "passenger_passport_num" varchar,
  "seat_number" varchar,
  "flight_id" UUID,
  "price" decimal,
  "created_at" timestamp,
  "updated_at" timestamp,
  "class" enum
);

COMMENT ON COLUMN "users"."role" IS 'admin or customer';

COMMENT ON COLUMN "flights"."flight_code" IS 'e.g. AY123';

COMMENT ON COLUMN "flights"."status" IS 'scheduled, delayed, cancelled';

COMMENT ON COLUMN "bookings"."status" IS 'RESERVED, CONFIRMED, CANCELLED';

COMMENT ON COLUMN "tickets"."class" IS 'Economy, Business, First';

ALTER TABLE "bookings" ADD FOREIGN KEY ("user_id") REFERENCES "users" ("id");

ALTER TABLE "bookings" ADD FOREIGN KEY ("flight_id") REFERENCES "flights" ("id");

ALTER TABLE "tickets" ADD FOREIGN KEY ("booking_id") REFERENCES "bookings" ("id");

ALTER TABLE "tickets" ADD FOREIGN KEY ("flight_id") REFERENCES "flights" ("id");
