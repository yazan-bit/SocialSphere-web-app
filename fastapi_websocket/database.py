from sqlalchemy import MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine,AsyncSession




DATA_BASE_URL = 'postgresql+asyncpg://postgres:thyk1032000@localhost:5432/django_DB'


engine = create_async_engine(
    DATA_BASE_URL,
    echo=True,
    pool_size=10,
    max_overflow=20
    )
metadata = MetaData()


AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_ = AsyncSession,
    expire_on_commit=False,
    autoflush=False
)


async def get_async_db():
    async with AsyncSessionLocal() as db:
        yield db


Base = declarative_base()