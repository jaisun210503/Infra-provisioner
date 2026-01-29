#!/usr/bin/env python3
"""
System health check script.
Verifies database, users, and configuration.
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

def check_environment():
    print("Checking environment variables...")
    encryption_key = os.getenv("CREDENTIALS_ENCRYPTION_KEY")
    if encryption_key:
        print("  ✓ CREDENTIALS_ENCRYPTION_KEY is set")
    else:
        print("  ✗ CREDENTIALS_ENCRYPTION_KEY is NOT set")
    print()

def check_database():
    print("Checking database...")
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

    from database import SessionLocal, engine
    from models import User, Team

    try:
        db = SessionLocal()

        # Check tables exist
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"  ✓ Database tables: {', '.join(tables)}")

        # Check users
        users = db.query(User).all()
        print(f"  ✓ Total users: {len(users)}")
        for user in users:
            print(f"    - {user.username} (Admin: {user.is_admin})")

        # Check teams
        teams = db.query(Team).all()
        print(f"  ✓ Total teams: {len(teams)}")
        for team in teams:
            print(f"    - {team.name}")

        db.close()
        print("  ✓ Database connection successful")
    except Exception as e:
        print(f"  ✗ Database error: {str(e)}")
    print()

def check_ports():
    print("Checking if ports are available...")
    import socket

    def is_port_in_use(port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', port)) == 0

    if is_port_in_use(8000):
        print("  ✓ Port 8000 is IN USE (backend should be running)")
    else:
        print("  ✗ Port 8000 is FREE (backend NOT running)")

    if is_port_in_use(3000):
        print("  ✓ Port 3000 is IN USE (frontend should be running)")
    else:
        print("  ✗ Port 3000 is FREE (frontend NOT running)")
    print()

def main():
    print("=" * 60)
    print("InfraUtomater System Health Check")
    print("=" * 60)
    print()

    check_environment()
    check_database()
    check_ports()

    print("=" * 60)
    print("Health check complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()
