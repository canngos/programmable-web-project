# PWP SPRING 2026
# PROJECT NAME: Flight Management System (FMS)

## Group information
- Student 1. Tuukka Palovaara, t6patu01@student.oulu.fi
- Student 2. Shane Dalumura Hettige, sdalumur25@student.oulu.fi
- Student 3. Can Baturlar, cbaturla25@student.oulu.fi

## Running The Project

### System Requirements
- Docker and Docker Compose
- Python 3.11+
- Git

### Setup
1. Clone repository:
```bash
git clone https://github.com/ShaneKavinda/programmable-web-project.git
cd programmable-web-project
```

2. Start services:
```bash
docker compose -f ticket_management_system/docker-compose.yml up -d
```

3. Local migration commands:
```bash
# Windows
set FLASK_APP=ticket_management_system
set DATABASE_URL=postgresql://flask_user:flask_password@localhost:5432/flask_db

# Linux/Mac
export FLASK_APP=ticket_management_system
export DATABASE_URL=postgresql://flask_user:flask_password@localhost:5432/flask_db

# Upgrade using package-local migration directory
flask db --directory ticket_management_system/migrations upgrade
```

### Quick Start
1. Start:
```bash
docker compose -f ticket_management_system/docker-compose.yml up -d
```
2. API:
- `http://localhost:5000`
- Swagger: `http://localhost:5000/apidocs/`
3. Populate sample data:
```bash
docker compose -f ticket_management_system/docker-compose.yml exec flask-app python -m ticket_management_system.populate_db
```
4. Stop:
```bash
docker compose -f ticket_management_system/docker-compose.yml down
```

### Common Commands
```bash
# Logs
docker compose -f ticket_management_system/docker-compose.yml logs -f

# DB shell
docker compose -f ticket_management_system/docker-compose.yml exec postgres psql -U flask_user -d flask_db

# Build/update
docker compose -f ticket_management_system/docker-compose.yml up -d --build
```

## Project Structure (ROA)
All application code, Docker definitions, and migrations are under `ticket_management_system/`.

```text
/programmable-web-project/
├── .env
├── init.sql
├── requirements.txt
├── ticket_management_system/
│   ├── __init__.py
│   ├── app.py
│   ├── api.py
│   ├── extensions.py
│   ├── exceptions.py
│   ├── models.py
│   ├── utils.py
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── entrypoint.sh
│   ├── populate_db.py
│   ├── migrations/
│   │   └── versions/
│   ├── resources/
│   │   ├── root.py
│   │   ├── users.py
│   │   ├── flights.py
│   │   ├── bookings.py
│   │   ├── user_service.py
│   │   ├── flight_service.py
│   │   ├── booking_service.py
│   │   ├── flight_schemas.py
│   │   └── booking_schemas.py
│   ├── swagger_specs/
│   │   ├── airports_list.yml
│   │   ├── flight_add.yml
│   │   ├── flight_search.yml
│   │   ├── user_list.yml
│   │   ├── user_login.yml
│   │   ├── user_me.yml
│   │   └── user_register.yml
│   └── static/
│       └── schema/
└── tests/
```
