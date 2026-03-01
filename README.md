# PWP SPRING 2026
# PROJECT NAME: Flight Management System (FMS)
# Group information
* Student 1. Tuukka Palovaara, t6patu01@student.oulu.fi
* Student 2. Shane Dalumura Hettige, sdalumur25@student.oulu.fi
* Student 3. Can Baturlar, cbaturla25@student.oulu.fi

## HOW TO - Running the Project

### System Requirements
- **Docker** and **Docker Compose** installed
- **Python 3.11+** (for local development commands)
- **Git** (for version control)

### Setup
1. **Download and install Git**

2. **Clone the git repository using the following command**
    ```bash
    git clone https://github.com/ShaneKavinda/programmable-web-project.git
    cd programmable-web-project
    ```

3. **Database Setup**
    ```bash
    # Build and start PostgreSQL database only
    docker-compose up -d postgres

    # Wait for database to be ready (5-10 seconds)
    sleep 10

    # Verify database is running
    docker-compose ps

    # Set environment variables (Windows)
    set FLASK_APP=app.py
    set DATABASE_URL=postgresql://flask_user:flask_password@localhost:5432/flask_db

    # Set environment variables (Linux/Mac)
    export FLASK_APP=app.py
    export DATABASE_URL=postgresql://flask_user:flask_password@localhost:5432/flask_db

    # Run the database migrations
    flask db upgrade

    # Start the flask-app container
    docker compose up -d
    ```

4. **Creating a new migration (When needed; optional)**

    Initializing the first database migration (already done. No need to do it for a second time)

    ```bash
        # Set environment variables (Windows)
        set FLASK_APP=app.py
        set DATABASE_URL=postgresql://flask_user:flask_password@localhost:5432/flask_db

        # Set environment variables (Linux/Mac)
        export FLASK_APP=app.py
        export DATABASE_URL=postgresql://flask_user:flask_password@localhost:5432/flask_db

        # Initialize Alembic migrations (run once)
        flask db init

        # Generate initial migration
        flask db migrate -m "Initial migration"

        # Apply migration to database
        flask db upgrade
    ```

    From second migration onwards:
    ```bash
        # Make sure the database container is running 
        docker-compose up -d postgres

        # Set environment variables (Windows)
        set FLASK_APP=app.py
        set DATABASE_URL=postgresql://flask_user:flask_password@localhost:5432/flask_db

        # Set environment variables (Linux/Mac)
        export FLASK_APP=app.py
        export DATABASE_URL=postgresql://flask_user:flask_password@localhost:5432/flask_db

        # Make sure the database is up-to-date
        flask db upgrade

        # Create the new database migration file
        flask db migrate -m "New migration"

        # Upgrade the database to run the new migration
        flask db upgrade

        # run the docker compose command to make sure the new migration file is copied to the flask app container
        docker compose build 

        # Finally, run the flask app 
        doocker compose up -d
    ```

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
   # Make sure the containers are running
   docker ps
   # Run the following command on the terminal to execute it within the docker container
   docker-compose exec flask-app python populate_db.py
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
- **Database URL**: `postgresql://flask_user:flask_password@postgres:5432/flask_db` (configured in `.env`)
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
- If `populate_db.py` fails, try changing `DATABASE_URL` in `.env` (substitute `postgres` with `localhost`)
- If port 5000 is in use, change it in `docker-compose.yml`
- For complete reset: `docker-compose down -v` then restart



