# Project Setup Instructions

## 📋 Prerequisites

### System Requirements
- **Docker** and **Docker Compose** installed
- **Python 3.11+** (for local development commands)
- **Git** (for version control)

### Verify Installation
```bash
docker --version
docker-compose --version
python --version
git --version
```

## 🚀 Quick Start (One-Command Setup)

```bash
# Run the setup script (if available)
./setup.sh

# Or manually follow the steps below
```

## 🔧 Manual Setup

### 1. Clone and Navigate
```bash
git clone <repository-url>
cd <project-directory>
```

### 2. Environment Configuration
```bash
# Create environment file from template
cp .env.example .env

# Edit the .env file with your preferences
# Default values (can be changed):
# POSTGRES_DB=flask_db
# POSTGRES_USER=flask_user
# POSTGRES_PASSWORD=flask_password
# FLASK_ENV=development
```

### 3. Database Setup
```bash
# Start PostgreSQL database only
docker-compose up -d postgres

# Wait for database to be ready (5-10 seconds)
sleep 10

# Verify database is running
docker-compose ps
```

### 4. Initialize Database Migrations
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

### 5. Start the Application
```bash
# Start all services (Flask app + PostgreSQL)
docker-compose up -d

# View logs
docker-compose logs -f flask-app
```

### 6. Verify Installation
```bash
# Check if services are running
docker-compose ps

# Test API endpoint
curl http://localhost:5000/
# Expected: {"message":"Flask PostgreSQL API",...}

# Check database tables
docker-compose exec postgres psql -U flask_user -d flask_db -c "\dt"
# Should show: alembic_version, users, bookings
```

## 📁 Project Structure

```
.
├── app.py              # Main Flask application
├── models.py           # Database models (User, Booking)
├── routes.py           # API routes and endpoints
├── Dockerfile          # Flask app container definition
├── docker-compose.yml  # Multi-container setup
├── requirements.txt    # Python dependencies
├── .env               # Environment variables (create from .env.example)
├── migrations/         # Database migrations (auto-generated)
│   ├── versions/      # Migration files
│   ├── env.py         # Alembic configuration
│   └── alembic.ini    # Migration settings
└── README.md          # This file
```

## 🗄️ Database Management

### Common Database Commands
```bash
# Access PostgreSQL shell
docker-compose exec postgres psql -U flask_user -d flask_db

# List all tables
\dt

# Describe table structure
\d users
\d bookings

# Run SQL query
SELECT * FROM users;
```

### Migration Workflow
When you modify models (`models.py`):
```bash
# Generate new migration
flask db migrate -m "Description of changes"

# Apply migration
flask db upgrade

# Rollback if needed
flask db downgrade
```

## 🔄 Development Workflow

### Starting Development
```bash
# Start all services in detached mode
docker-compose up -d

# Follow logs
docker-compose logs -f flask-app

# Stop services
docker-compose down
```

### Adding Dependencies
```bash
# Add to requirements.txt
echo "new-package==1.0.0" >> requirements.txt

# Rebuild Docker image
docker-compose build --no-cache flask-app
docker-compose up -d
```

### Code Changes
```bash
# The app automatically reloads on code changes
# Changes to models.py require new migrations
```

## 🐛 Troubleshooting

### Common Issues

#### 1. "Database connection failed"
```bash
# Check if PostgreSQL is running
docker-compose ps

# Check PostgreSQL logs
docker-compose logs postgres

# Test connection manually
docker-compose exec postgres psql -U flask_user -d flask_db -c "SELECT 1;"
```

#### 2. "No changes in schema detected" during migration
```bash
# Drop all tables and start fresh
docker-compose down -v
docker-compose up -d postgres
sleep 5
rm -rf migrations
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

#### 3. "Port already in use"
```bash
# Check what's using port 5000
netstat -ano | findstr :5000  # Windows
lsof -i :5000                 # Linux/Mac

# Or change port in docker-compose.yml
# Update: "5000:5000" to "5001:5000"
```

#### 4. Docker Build Errors
```bash
# Clean build cache
docker-compose build --no-cache

# Remove all Docker artifacts
docker system prune -a
```

### Reset Everything
```bash
# Complete reset (WARNING: Deletes all data!)
docker-compose down -v
rm -rf migrations
docker system prune -f

# Start fresh
docker-compose up -d --build
```

## 📊 API Endpoints

### Available Endpoints
- `GET /` - API information
- `GET /users` - List all users
- `POST /users` - Create new user
- `GET /bookings` - List all bookings  
- `POST /bookings` - Create new booking

### Testing API
```bash
# Using curl
curl http://localhost:5000/users
curl -X POST http://localhost:5000/users \
  -H "Content-Type: application/json" \
  -d '{"firstname":"John","lastname":"Doe","email":"john@example.com","password_hash":"hash123","role":1}'

# Using Python
python -c "
import requests
response = requests.get('http://localhost:5000/users')
print(response.json())
"
```

## 🔧 Development Tools

### Useful Docker Commands
```bash
# View running containers
docker ps

# View logs
docker-compose logs -f
docker-compose logs flask-app
docker-compose logs postgres

# Execute commands in container
docker-compose exec flask-app python -c "print('Hello')"
docker-compose exec postgres psql -U flask_user -d flask_db

# Rebuild specific service
docker-compose build flask-app
docker-compose up -d flask-app
```

### Database Backup/Restore
```bash
# Backup database
docker-compose exec postgres pg_dump -U flask_user flask_db > backup.sql

# Restore database
cat backup.sql | docker-compose exec -T postgres psql -U flask_user flask_db
```

## 🧪 Testing

### Running Tests
```bash
# Run tests inside container
docker-compose exec flask-app python -m pytest tests/

# Or run locally (if dependencies installed)
pytest tests/
```

### Adding Test Data
```bash
# Insert sample data via SQL
docker-compose exec postgres psql -U flask_user -d flask_db -c "
INSERT INTO users (firstname, lastname, email, password_hash, role) 
VALUES ('Test', 'User', 'test@example.com', 'hash123', 1);
"
```

## 📈 Monitoring

### Check Resource Usage
```bash
# Docker resource usage
docker stats

# Container logs
docker-compose logs --tail=100 flask-app

# Database size
docker-compose exec postgres psql -U flask_user -d flask_db -c "
SELECT pg_size_pretty(pg_database_size('flask_db'));
"
```

## 🔐 Security Notes

### Important Security Practices
1. **Never commit `.env` file** to version control
2. Use strong passwords in production
3. Change default credentials before deployment
4. Enable HTTPS in production
5. Regularly update dependencies

### Production Deployment Checklist
- [ ] Update all default passwords
- [ ] Set `FLASK_ENV=production`
- [ ] Configure proper CORS settings
- [ ] Set up SSL/TLS certificates
- [ ] Configure database backups
- [ ] Set up monitoring and logging
- [ ] Update Docker security settings

## 🤝 Contributing

### Development Process
1. Create feature branch: `git checkout -b feature-name`
2. Make changes and test
3. Create migrations if models changed
4. Run tests: `pytest tests/`
5. Commit changes: `git commit -m "Description"`
6. Push branch: `git push origin feature-name`
7. Create pull request

### Code Style
- Follow PEP 8 for Python code
- Use meaningful variable names
- Add docstrings to functions
- Write unit tests for new features

## 📚 Additional Resources

### Documentation
- [Flask Documentation](https://flask.palletsprojects.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Docker Documentation](https://docs.docker.com/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

### Useful Commands Reference
```bash
# See this help
cat README.md | less

# View all Docker containers
docker ps -a

# View Docker images
docker images

# Clean unused Docker resources
docker system prune
```

---

## 🆘 Need Help?

### Common Solutions
- Check logs: `docker-compose logs`
- Restart services: `docker-compose restart`
- Rebuild: `docker-compose up -d --build`
- Reset database: `docker-compose down -v`

---

**Note:** This setup assumes development environment. For production deployment, additional configuration is required including security hardening, SSL certificates, and proper monitoring setup.