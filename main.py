from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import Base, engine
from admin_routes.teamanagement import admin
from admin_routes.requests import admin_request_router
from user_routes.users import user_router
from user_routes.requests import request_router
# Create all tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Infrastructure API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(admin)
app.include_router(admin_request_router)
app.include_router(user_router)
app.include_router(request_router)



@app.get("/")
def root():
    return {"message": "Infrastructure API is running"}