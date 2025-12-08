import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME", "carribulus_db")

class Database:
    client: AsyncIOMotorClient = None
    db = None

    async def connect(self):
        # Add connectTimeoutMS=5000 to fail faster if network is bad
        self.client = AsyncIOMotorClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        try:
            # Force a connection to verify it works
            await self.client.admin.command('ping')
            self.db = self.client[DB_NAME]
            print(f"Connected to MongoDB Atlas successfully.")
        except Exception as e:
            print(f"Failed to connect to MongoDB: {e}")
            raise e

    async def close(self):
        if self.client:
            self.client.close()
            print("Disconnected from MongoDB.")

    async def get_session(self, session_id: str):
        if self.db is None:
            raise Exception("Database not initialized")
        return await self.db.sessions.find_one({"session_id": session_id})

    async def save_session(self, session_data: dict):
        if self.db is None:
            raise Exception("Database not initialized")
        await self.db.sessions.update_one(
            {"session_id": session_data["session_id"]},
            {"$set": session_data},
            upsert=True
        )

db = Database()
