import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from passlib.context import CryptContext
import uuid
from datetime import datetime

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# MongoDB connection (using the same settings as server.py)
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/neon_trader')
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'neon_trader')]

async def create_test_user():
    """Create a test user for development"""
    try:
        # Check if user already exists
        existing_user = await db.users.find_one({"email": "test@example.com"})
        if existing_user:
            print("Test user already exists!")
            return
        
        # Create test user
        user_data = {
            "id": str(uuid.uuid4()),
            "email": "test@example.com",
            "username": "testuser",
            "hashed_password": pwd_context.hash("testpassword123"),
            "is_active": True,
            "two_factor_enabled": False,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # Insert user
        await db.users.insert_one(user_data)
        print("Test user created successfully!")
        print("Email: test@example.com")
        print("Password: testpassword123")
        
        # Create default portfolio
        portfolio_data = {
            "id": str(uuid.uuid4()),
            "user_id": user_data["id"],
            "total_balance": 10000.0,
            "available_balance": 10000.0,
            "invested_balance": 0.0,
            "daily_pnl": 0.0,
            "total_pnl": 0.0,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        await db.portfolios.insert_one(portfolio_data)
        print("Default portfolio created successfully!")
        
    except Exception as e:
        print(f"Error creating test user: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(create_test_user())