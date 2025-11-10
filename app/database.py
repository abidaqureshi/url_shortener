from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession, create_async_engine

from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager, asynccontextmanager
import os
from decouple import config

from app import Base

DATABASE_URL = f"postgresql+asyncpg://{config('DB_USERNAME')}:{config('DB_PASSWORD')}@{config('DB_HOST')}:{config('DB_PORT')}/{config('DB_NAME')}"

# For different databases:
# PostgresSQL: postgresql+asyncpg://user:pass@localhost/dbname
# SQLite: sqlite+aiosqlite:///./url_shortener.db
# MySQL: mysql+asyncmy://user:pass@localhost/dbname

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # Log SQL queries (disable in production)
    future=True,  # User SQLAlchemy 2.0 Style
    pool_size=10,
    max_overflow=20
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(engine,
                                       class_=AsyncSession,
                                       expire_on_commit=False,
                                       autocommit=False,
                                       autoflush=False)


@asynccontextmanager
async def get_db():
    """Context manager for database sessions"""
    session = AsyncSessionLocal()
    try:
        print("PostgresSQL db connected")
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


async def db_dependency() -> AsyncSession:
    async with get_db() as session:
        yield session


async def create_tables():
    """Create all tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def check_db_connection():
    """Test database connection"""
    try:
        async with get_db() as db:
            result = await db.execute(text("SELECT 1"))
            return result.scalar() == 1
    except Exception as e:
        print(f"Database connection error: {e}")
        return False
