from fastapi import FastAPI
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from contextlib import asynccontextmanager
import os
import logging
from pathlib import Path

# Import routes and database utilities.
# Prefer package-style imports (when running from repo root) but fall back to local imports
# so the server can be started from the `backend/` directory during local development.
try:
    # When running from repo root (recommended): `python -m uvicorn backend.server:app`
    from backend.routes import router as api_router
    from backend.database import initialize_database
except Exception:
    # When running from inside backend/ (legacy instructions): `uvicorn server:app`
    from routes import router as api_router
    from database import initialize_database

# Load environment variables
ROOT_DIR = Path(__file__).parent
# Only load .env locally. Render and other platforms provide env vars directly.
if os.getenv("RENDER") is None:
    load_dotenv(ROOT_DIR / ".env")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Cloudinary configuration
import cloudinary

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True
)
logger.info(f"Cloudinary ready: {cloudinary.config().cloud_name}")


# MongoDB setup
mongo_url = os.getenv("MONGO_URL")
if not mongo_url:
    raise ValueError("❌ MONGO_URL not found in environment variables.")

db_name = os.getenv("DB_NAME", "medicapsoia")
client = AsyncIOMotorClient(mongo_url)
db = client[db_name]

# Define FastAPI lifespan (startup + shutdown)
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle events for startup and shutdown"""
    try:
        # Startup tasks
        await initialize_database()
        logger.info("🚀 Student Exchange Programs API started successfully")
        yield
    except Exception as e:
        logger.error(f"❌ Failed to initialize database: {e}")
        yield
    finally:
        # Shutdown tasks
        client.close()
        logger.info("📪 Database connection closed")

# Initialize FastAPI app
app = FastAPI(
    title="Student Exchange Programs API",
    description="API for managing international student exchange programs at Medi-Caps University",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=[
        "https://io.medicaps.ac.in",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "*"  # Fallback for development
    ],
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include routes
app.include_router(api_router)

# Root endpoint
@app.get("/api/")
async def root():
    return {"message": "Student Exchange Programs API - Medi-Caps University"}

# Port configuration for deployment
if __name__ == "__main__":
    import uvicorn
    # Get port from environment variable (Render provides this)
    # Default to 8000 for local development
    port = int(os.getenv("PORT", 8000))
    logger.info(f"🚀 Starting server on port {port}")
    
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=port,
        reload=False  # Don't use reload in production
    )
