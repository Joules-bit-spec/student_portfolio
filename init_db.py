#!/usr/bin/env python
"""
Initialize/Reset the database with the updated schema.
Run this script once to create tables with the new profile_picture column.
"""
import os
from app import app, db

def init_database():
    """Create all database tables."""
    with app.app_context():
        # Remove old databases if they exist
        db_paths = [
            'portfolio.db',  # Root directory (old location)
            os.path.join('instance', 'portfolio.db')  # Instance folder (new location)
        ]
        
        for db_path in db_paths:
            if os.path.exists(db_path):
                os.remove(db_path)
                print(f"Removed old database: {db_path}")
        
        # Create all tables
        db.create_all()
        print("✓ Database initialized successfully!")
        print("✓ All tables created with the new schema (including profile_picture column)")

if __name__ == '__main__':
    init_database()
