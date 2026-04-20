import { checkSeatAvailability } from "../services/bookings";

const randomSeat = () => {
  const row = Math.floor(Math.random() * 30) + 1;
  const letters = ["A", "B", "C", "D", "E", "F"];
  const letter = letters[Math.floor(Math.random() * letters.length)];
  return `${row}${letter}`;
};

/**
 * Picks `count` distinct seat codes that are currently available on the flight
 * according to GET /api/bookings/availability.
 */
export async function pickUniqueAvailableSeats(
  flightId: string,
  count: number,
): Promise<string[]> {
  if (count < 1 || count > 10) {
    throw new Error("Passenger count must be between 1 and 10.");
  }
  const picked: string[] = [];
  const tried = new Set<string>();
  const maxAttempts = 80 * count;

  for (let attempts = 0; attempts < maxAttempts && picked.length < count; attempts += 1) {
    const candidate = randomSeat();
    if (tried.has(candidate)) continue;
    tried.add(candidate);

    const available = await checkSeatAvailability({
      flight_id: flightId,
      seat_num: candidate,
    });
    if (available && !picked.includes(candidate)) {
      picked.push(candidate);
    }
  }

  if (picked.length < count) {
    throw new Error("Could not find enough available seats for this flight.");
  }
  return picked;
}
