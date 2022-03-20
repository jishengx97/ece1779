

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

class MemcachePoolResizeConfig(Base):
    # This table has one and only one entry. managerapp will 
    # ensure this at start and crash the app if this table
    # contains more than one entry.
    __tablename__ = 'memcache_pool_resize_configuration'
    id = Column(
        Integer, 
        primary_key=True,
        autoincrement=True
    )
    resize_mode = Column(
        String(120), # either "Maunal" or "Automatic"
        nullable=False
    )
    max_missrate_threshold = Column(
        Float,
        nullable=False
    )
    min_missrate_threshold = Column(
        Float,
        nullable=False
    )
    expand_ratio = Column(
        Float,
        nullable=False
    )
    shrink_ratio = Column(
        Float,
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
        String(120, collation='utf8_bin'),
        nullable=False,
        unique=True,
        index=True
    )
    file_location = Column(
        String(500),
        nullable=False,
    )