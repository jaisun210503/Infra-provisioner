from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from auth.auth import get_current_admin_user
from database import get_db
from models import Team, User
from schemas import TeamCreate, TeamUpdate, TeamResponse, AddMemberRequest, UserResponse

admin = APIRouter(prefix="/api/v1/admin", tags=["Admin"])


@admin.get("/users", response_model=List[UserResponse])
def get_all_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    users = db.query(User).filter(User.is_admin == False).all()
    return users


@admin.post("/teams", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
def create_team(
    teamcreate: TeamCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    # Check if team already exists
    existing = db.query(Team).filter(Team.name == teamcreate.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Team name already exists")

    # Create new team
    db_team = Team(
        name=teamcreate.name,
        description=teamcreate.description,
        created_by=current_user.id
    )

    db.add(db_team)
    db.commit()
    db.refresh(db_team)
    return db_team


@admin.get("/teams", response_model=List[TeamResponse])
def get_teams(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    # Return all teams
    teams = db.query(Team).limit(100).offset(0).all()
    return teams


@admin.get("/teams/{team_id}", response_model=TeamResponse)
def get_by_id(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    # Fetch team by ID
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return team


@admin.put("/teams/{team_id}", response_model=TeamResponse)
def update_team(
    team_id: int,
    details: TeamUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    

    if details.name is not None:
        # Check if new name already taken by another team
        existing = db.query(Team).filter(Team.name == details.name, Team.id != team_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Team name already taken")
        team.name = details.name

    if details.description is not None:
        team.description = details.description

    db.commit()
    db.refresh(team)


    return team


@admin.delete("/teams/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_team(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    # Fetch team
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    # Delete team
    db.delete(team)
    db.commit()
    return None


@admin.post("/teams/{team_id}/members", status_code=status.HTTP_201_CREATED)
def add_member_to_team(
    team_id: int,
    member: AddMemberRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    # Check team exists
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    # Check user exists
    user = db.query(User).filter(User.id == member.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if already in team
    if user.team_id == team_id:
        raise HTTPException(status_code=400, detail="User already in this team")

    # Add user to team
    user.team_id = team_id
    db.commit()
    return {"message": f"User {member.user_id} added to team {team_id}"}


@admin.delete("/teams/{team_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_member_from_team(
    team_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    # Find user in this team
    user = db.query(User).filter(User.id == user_id, User.team_id == team_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found in this team")

    # Remove from team
    user.team_id = None
    db.commit()
    return None