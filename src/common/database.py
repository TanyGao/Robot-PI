from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

class Device(Base):
    __tablename__ = "devices"
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    device_type = Column(String, default="raspberry_pi")
    status = Column(String, default="offline")
    last_seen = Column(DateTime, default=datetime.utcnow)

class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
    user_input = Column(Text, nullable=False)
    ai_response = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

# 创建异步会话工厂
engine = create_async_engine("sqlite+aiosqlite:///data/robot.db")
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def get_async_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session