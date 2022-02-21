

from sqlalchemy import Column, Integer, Float, String, Time
from .database import Base

class MemcacheConfig(Base):
    # This table has one and only one entry. frontendapp will 
    # ensure this at start and crash the app if this table
    # contains more than one entry.
    __tablename__ = 'memcache_configuration'
    id = Column(
        Integer, 
        primary_key=True,
        autoincrement=True
    )
    capacity_in_mb = Column(
        Float,
        nullable=False
    )
    replacement_policy = Column(
        String(120),
        nullable=False
    )

class MemcacheStats(Base):
    __tablename__ = 'memcache_stats'
    id = Column(
        Integer, 
        primary_key=True,
        autoincrement=True
    )
    num_items = Column(
        Integer,
        nullable=False
    )
    total_size = Column(
        Float,
        nullable=False
    )
    num_requests_served = Column(
        Integer,
        nullable=False
    )
    miss_rate = Column(
        Float,
        nullable=False
    )
    hit_rate = Column(
        Float,
        nullable=False
    )
    stats_timestamp = Column(
        Time,
        nullable=False
    )

class KeyAndFileLocation(Base):
    # key is unique, and file location is not.
    __tablename__ = 'key_and_file_location'
    id = Column(
        Integer, 
        primary_key=True,
        autoincrement=True
    )
    key = Column(
        String(120),
        nullable=False,
        unique=True,
        index=True
    )
    file_location = Column(
        String(500),
        nullable=False,
    )