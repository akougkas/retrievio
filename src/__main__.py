import asyncio
from .session import RetrievIOSession

async def main():
    session = RetrievIOSession()
    await session.start()

if __name__ == "__main__":
    asyncio.run(main()) 