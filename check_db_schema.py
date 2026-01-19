#!/usr/bin/env python3
"""Check current database schema and add missing columns."""

import sqlite3
import os
from database import get_engine
from models import SpeciesDB
from sqlmodel import SQLModel

def check_schema():
    """Check current database schema."""
    db_path = 'tunisia_parks.db'
    if not os.path.exists(db_path):
        print('Database file not found')
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check species table columns
    cursor.execute("PRAGMA table_info(species)")
    columns = cursor.fetchall()
    print('Current species table columns:')
    for col in columns:
        col_name, col_type, nullable, default, pk = col[1], col[2], col[3], col[4], col[5]
        print(f'  {col_name}: {col_type} (nullable: {nullable == 0}, pk: {pk})')

    # Check if new columns exist
    column_names = [col[1] for col in columns]
    missing_columns = []

    if 'danger_level' not in column_names:
        missing_columns.append('danger_level')
    if 'emergency_protocol' not in column_names:
        missing_columns.append('emergency_protocol')

    if missing_columns:
        print(f'\nMissing columns: {missing_columns}')
        print('Adding missing columns...')

        # Add missing columns
        for col in missing_columns:
            if col == 'danger_level':
                cursor.execute("ALTER TABLE species ADD COLUMN danger_level TEXT")
                print('Added danger_level column')
            elif col == 'emergency_protocol':
                cursor.execute("ALTER TABLE species ADD COLUMN emergency_protocol TEXT")
                print('Added emergency_protocol column')

        conn.commit()
        print('Database schema updated successfully!')
    else:
        print('\nAll required columns are present.')

    conn.close()

def force_recreate_tables():
    """Force recreate all tables (for development/testing)."""
    print('Force recreating all tables...')
    engine = get_engine()

    # Drop all tables
    SQLModel.metadata.drop_all(engine)
    print('Dropped all tables')

    # Recreate all tables
    SQLModel.metadata.create_all(engine)
    print('Recreated all tables')

    print('Database schema completely refreshed!')

if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == '--recreate':
        force_recreate_tables()
    else:
        check_schema()
