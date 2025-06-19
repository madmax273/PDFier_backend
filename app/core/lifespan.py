from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.database.connection import connect_to_mongo, close_mongo_connection

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Context Manager for FastAPI application lifespan events.
    Ensures MongoDB connection is established on startup and closed on shutdown.
    """
    # Startup event
    await connect_to_mongo()
    yield # Application will run and handle requests here
    # Shutdown event
    await close_mongo_connection()