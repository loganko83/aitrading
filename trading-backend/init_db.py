#!/usr/bin/env python
"""
Database initialization script
Creates all tables from SQLAlchemy models
"""

from app.database.base import Base, engine, is_sqlite
from app.core.config import settings

# Import all models to ensure they're registered
from app.models import *  # noqa

def init_database():
    """Initialize database with all tables"""
    print(f"Initializing database: {settings.DATABASE_URL}")
    print(f"Database type: {'SQLite' if is_sqlite else 'PostgreSQL'}")

    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("All tables created successfully!")

        # List created tables
        print("\nCreated tables:")
        for table in Base.metadata.sorted_tables:
            print(f"   - {table.name}")

    except Exception as e:
        print(f"Error creating tables: {e}")
        raise

if __name__ == "__main__":
    init_database()
