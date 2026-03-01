"""
Database and other Flask extensions initialization.
This module prevents circular imports by keeping extensions separate.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
