"""
MongoDB Database Connection Module
Handles async connection to MongoDB using Motor
"""

import os
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Database configuration
MONGODB_URI = os.getenv("MONGODB_URI")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "expense_tracker")


class DatabaseConnection:
    """
    Singleton class for MongoDB connection
    Ensures only one database connection throughout the app
    """
    _instance = None
    _client = None
    _db = None
    
    def __new__(cls):
        """Create singleton instance"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize database connection"""
        if self._client is None:
            self._client = AsyncIOMotorClient(MONGODB_URI)
            self._db = self._client[MONGODB_DB_NAME]
            logger.info(f"MongoDB connection initialized to database: {MONGODB_DB_NAME}")
    
    @property
    def db(self):
        """Get database instance"""
        return self._db
    
    @property
    def client(self):
        """Get client instance"""
        return self._client
    
    async def close(self):
        """Close database connection"""
        if self._client:
            self._client.close()
            logger.info("MongoDB connection closed")
    
    async def ping(self):
        """Test database connection"""
        try:
            await self._client.admin.command('ping')
            return True
        except Exception as e:
            logger.error(f"Database ping failed: {e}")
            return False


# Create a single database instance
db_connection = DatabaseConnection()


async def get_database():
    """
    Get database instance (for dependency injection)
    """
    return db_connection.db


async def test_connection():
    """
    Test MongoDB connection
    """
    logger.info("Testing MongoDB connection...")
    
    if not MONGODB_URI:
        logger.error("MONGODB_URI not found in environment variables")
        logger.error("Make sure your .env file is configured correctly")
        return False
    
    logger.info(f"Connecting to MongoDB: {MONGODB_URI[:50]}...")
    
    try:
        # Test ping
        is_connected = await db_connection.ping()
        
        if is_connected:
            logger.info("MongoDB connection successful")
            logger.info(f"Connected to database: {MONGODB_DB_NAME}")
            
            # List existing collections
            collections = await db_connection.db.list_collection_names()
            if collections:
                logger.info(f"Existing collections: {', '.join(collections)}")
            else:
                logger.info("No collections yet (database is empty)")
            
            return True
        else:
            logger.error("MongoDB connection failed")
            return False
            
    except Exception as e:
        logger.error(f"Connection error: {e}")
        return False


# For easy testing
if __name__ == "__main__":
    import asyncio
    asyncio.run(test_connection())