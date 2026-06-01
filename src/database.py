"""Database models and ORM setup"""

from sqlalchemy import create_engine, Column, String, DateTime, Integer, Text, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
from src.logger import get_logger

logger = get_logger(__name__)

Base = declarative_base()

class User(Base):
    """User model"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String(255), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    api_key = Column(String(255), unique=True, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class GeneratedContent(Base):
    """Store generated content"""
    __tablename__ = "generated_content"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    content_type = Column(String(50), nullable=False)
    prompt = Column(Text, nullable=False)
    output = Column(Text, nullable=True)
    model_used = Column(String(255), nullable=False)
    processing_time = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class UserQuery(Base):
    """Store user queries for history"""
    __tablename__ = "user_queries"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    query_type = Column(String(50), nullable=False)
    query_text = Column(Text, nullable=False)
    response = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Database:
    """Database connection manager"""
    
    def __init__(self, db_url=None):
        """Initialize database"""
        self.db_url = db_url or os.getenv("DATABASE_URL", "sqlite:///aais.db")
        self.engine = create_engine(self.db_url)
        self.SessionLocal = sessionmaker(bind=self.engine)
        self._init_db()
    
    def _init_db(self):
        """Initialize database tables"""
        try:
            Base.metadata.create_all(self.engine)
            logger.info("Database initialized")
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    def get_session(self):
        """Get database session"""
        return self.SessionLocal()
    
    def close(self):
        """Close database connection"""
        self.engine.dispose()

db = Database()
