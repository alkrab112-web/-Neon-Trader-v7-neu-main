import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os

# MongoDB connection (using the same settings as server.py)
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/neon_trader')
db_name = os.environ.get('DB_NAME', 'neon_trader')

async def check_mongodb():
    """Check if MongoDB is accessible"""
    try:
        print(f"Attempting to connect to MongoDB at {mongo_url}")
        client = AsyncIOMotorClient(mongo_url, serverSelectionTimeoutMS=5000)
        
        # Try to ping the database
        await client.admin.command('ping')
        print("✅ MongoDB connection successful!")
        
        # Try to access the database
        db = client[db_name]
        collection_names = await db.list_collection_names()
        print(f"✅ Database '{db_name}' is accessible")
        print(f"📦 Collections: {collection_names if collection_names else 'None found'}")
        
        # Try to count users
        user_count = await db.users.count_documents({})
        print(f"👥 Users in database: {user_count}")
        
        client.close()
        return True
        
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(check_mongodb())