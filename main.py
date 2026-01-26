from fastapi import FastAPI
from database import Base, engine
from admin_routes.teamanagement import admin
from admin_routes.requests import admin_request_router
from user_routes.users import user_router
from user_routes.requests import request_router
# Create all tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Infrastructure API")

# Include routers
app.include_router(admin)
app.include_router(admin_request_router)
app.include_router(user_router)
app.include_router(request_router)



@app.get("/")
def root():
    return {"message": "Infrastructure API is running"}