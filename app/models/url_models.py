import secrets
import string
from datetime import datetime, timedelta

from sqlalchemy import Column, Integer, Text, String, DateTime, func, Boolean

from app import Base


class URL(Base):
    __tablename__ = "urls"

    id = Column(Integer, primary_key=True, index=True)
    original_url = Column(Text, nullable=False)
    short_code = Column(String(50), unique=True, index=True, nullable=False)
    custom_alias = Column(String(50), unique=True, index=True, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)
    clicks = Column(Integer, default=0)

    def generate_short_code(self, length: int = 6):
        """Generate random short code"""
        characters = string.ascii_letters + string.digits
        return ''.join(secrets.choice(characters) for _ in range(length))

    def set_expiration(self, days: int):
        """Set expirations date"""
        if days:
            self.expires_at = datetime.utcnow() + timedelta(days=days)


class Click(Base):
    __tablename__ = "clicks"
    id = Column(Integer, primary_key=True, index=True)
    url_id = Column(Integer, index=True, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    ip_address = Column(String(45), nullable=False)
    user_agent = Column(Text, nullable=True)
    country = Column(String(2), nullable=True)
    referrer = Column(Text, nullable=True)
