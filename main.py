from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import logging
from database import Base, engine
from admin_routes.teamanagement import admin
from admin_routes.requests import admin_request_router
from admin_routes.aws_credentials import aws_credentials_router
from user_routes.users import user_router
from user_routes.requests import request_router

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
logger.info("Application starting...")

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
app.include_router(aws_credentials_router)
app.include_router(user_router)
app.include_router(request_router)



@app.on_event("startup")
async def startup_event():
    logger.info("FastAPI application started successfully")
    logger.info(f"Database: {engine.url}")
    logger.info("CORS enabled for: http://localhost:3000, http://127.0.0.1:3000")


@app.get("/")
def root():
    return {"message": "Infrastructure API is running"}


@app.get("/health")
def health_check():
    """Health check endpoint to verify API is running."""
    return {
        "status": "healthy",
        "service": "InfraUtomater API",
        "version": "1.0",
        "database": "connected" if engine else "error"
    }


@app.get("/api/v1/health")
def api_health_check():
    """API-prefixed health check."""
    return health_check()