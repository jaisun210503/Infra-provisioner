#!/usr/bin/env python3
"""
Script to create test users with known passwords.
Usage: python create_test_user.py
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from models import User, Team
from auth.auth import hash_password

def create_or_reset_user(username: str, email: str, password: str, is_admin: bool = False, team_id: int = None):
    """Create a new user or reset password if user exists."""
    db = SessionLocal()
    try:
        # Check if user exists
        user = db.query(User).filter(User.username == username).first()

        if user:
            print(f"User '{username}' already exists. Resetting password...")
            user.password_hash = hash_password(password)
            user.email = email
            user.is_admin = is_admin
            user.team_id = team_id
            db.commit()
            print(f"✓ Password reset for user: {username}")
        else:
            print(f"Creating new user: {username}")
            new_user = User(
                username=username,
                email=email,
                password_hash=hash_password(password),
                is_admin=is_admin,
                team_id=team_id
            )
            db.add(new_user)
            db.commit()
            print(f"✓ Created user: {username}")

        print(f"  Email: {email}")
        print(f"  Password: {password}")
        print(f"  Admin: {is_admin}")
        print(f"  Team ID: {team_id}")
        print()

    except Exception as e:
        print(f"✗ Error: {str(e)}")
        db.rollback()
    finally:
        db.close()

def main():
    print("=" * 60)
    print("InfraUtomater - Test User Creation")
    print("=" * 60)
    print()

    # Create/reset admin user
    create_or_reset_user(
        username="admin",
        email="admin@example.com",
        password="admin123",
        is_admin=True,
        team_id=None
    )

    # Check if Team 1 exists
    db = SessionLocal()
    team = db.query(Team).filter(Team.id == 1).first()
    db.close()

    # Create/reset regular user
    create_or_reset_user(
        username="testuser",
        email="test@example.com",
        password="test123",
        is_admin=False,
        team_id=1 if team else None
    )

    print("=" * 60)
    print("Test users ready! You can now log in with:")
    print()
    print("Admin User:")
    print("  Username: admin")
    print("  Password: admin123")
    print()
    print("Regular User:")
    print("  Username: testuser")
    print("  Password: test123")
    print("=" * 60)

if __name__ == "__main__":
    main()
