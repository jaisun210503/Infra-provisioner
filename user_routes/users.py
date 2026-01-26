from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

from database import get_db
from models import User, Team
from schemas import UserCreate, UserResponse, Token, TeamResponse
from typing import List
from auth.auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

user_router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])



                                                                                                                                                    
@user_router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)                                                    
def register(user_data: UserCreate, db: Session = Depends(get_db)):                                                                                                                                                                                                        
      existing_email = db.query(User).filter(User.email == user_data.email).first()                                                                   
      if existing_email:                                                                                                                              
          raise HTTPException(status_code=400, detail="Email already exists")                                                                         
                                                                                                                                                      
                                                                                                                   
      existing_username = db.query(User).filter(User.username == user_data.username).first()                                                          
      if existing_username:                                                                                                                           
          raise HTTPException(status_code=400, detail="Username already exists")                                                                      
                                                                                                                                                      
                                                                                                              
      hashed_password = hash_password(user_data.password)                                                                                             
      user = User(                                                                                                                                    
          username=user_data.username,                                                                                                    
          email=user_data.email,                                                                                                                      
          password_hash=hashed_password                                                                                                               
      )                                                                                                                                               
                                                                                                                                                      
      db.add(user)                                                                                                                                    
      db.commit()                                                                                                                                     
      db.refresh(user)                                                                                                                     
      return user  

@user_router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):

    user = db.query(User).filter(User.username == form_data.username).first()


    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )


    if not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )


    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )

    # 5. Return token
    return {"access_token": access_token, "token_type": "bearer"}


@user_router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@user_router.get("/me/team", response_model=TeamResponse)
def get_my_team(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):                                                     
      # Check if user is in a team                                                                                                                    
      if not current_user.team_id:                                                                                                                    
          raise HTTPException(status_code=404, detail="You are not in a team")                                                                        
                                                                                                                                                      
      team = db.query(Team).filter(Team.id == current_user.team_id).first()                                                                           
      return team    

@user_router.get("/me/team/members", response_model=List[UserResponse])
def get_my_team_members(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
        if not current_user.team_id:                                                                                                                    
          raise HTTPException(status_code=404, detail="You are not in a team")  
        members=db.query(User).filter(User.team_id == current_user.team_id).all()
        return members