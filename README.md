# PWP SPRING 2026
# PROJECT NAME
# Group information
* Student 1. Tuukka Palovaara, t6patu01@student.oulu.fi
* Student 2. Shane Dalumura Hettige, sdalumur25@student.oulu.fi
* Student 3. Can Baturlar, cbaturla25@student.oulu.fi

## HOWTO - Running the Project

### Prerequisites
- Docker and Docker Compose installed
- Python 3.11+ (for populate script)

### Quick Start

1. **Start the Application**
   ```bash
   docker-compose up -d
   ```

2. **Access the API**
   - Main API: `http://localhost:5000`
   - Test endpoint: `http://localhost:5000/`

3. **Populate Database (Optional)**
   ```bash
   python populate_db.py
   ```
   This creates sample data including users, flights, bookings, and tickets.
   
   **Test credentials after population:**
   - Admin: `admin@flightsystem.com` / `admin123`
   - User: `john.doe@example.com` / `password123`

4. **Stop the Application**
   ```bash
   docker-compose down
   ```

### Database Connection Info
- **JDBC URL**: `jdbc:postgresql://localhost:5432/flask_db`
- **Username**: `flask_user`
- **Password**: `flask_password` (configured in `.env`)

### Common Commands
```bash
# View logs
docker-compose logs -f

# Access database shell
docker-compose exec postgres psql -U flask_user -d flask_db

# Apply database migrations
flask db upgrade

# Rebuild after code changes
docker-compose up -d --build
```

### Troubleshooting
- If `populate_db.py` fails, ensure `DATABASE_URL` in `.env` uses `localhost` not `postgres`
- If port 5000 is in use, change it in `docker-compose.yml`
- For complete reset: `docker-compose down -v` then restart

📖 **For detailed setup instructions, see `instructions.md`**


