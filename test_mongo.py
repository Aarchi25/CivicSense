import asyncio
import certifi
from motor.motor_asyncio import AsyncIOMotorClient
from backend.config import get_settings


async def main():
    settings = get_settings()

    client = AsyncIOMotorClient(
        settings.mongodb_uri,
        tlsCAFile=certifi.where(),
        serverSelectionTimeoutMS=10000,
    )

    try:
        result = await client.admin.command("ping")
        print("MongoDB connected successfully:", result)
    except Exception as e:
        print("MongoDB connection failed:", repr(e))
    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(main())