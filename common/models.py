

from sqlalchemy import Column, Integer, Float, String, Sequence
from .database import Base

class MemcacheConfig(Base):
    # This table has one and only one entry. frontendapp will 
    # ensure this at start and crash the app if this table
    # contains more than one entry.
    __tablename__ = 'memcache_configuration'
    id = Column(
        Integer, 
        Sequence('user_id_seq'),
        primary_key=True
    )
    capacity_in_mb = Column(
        Float,
        nullable=False
    )
    replacement_policy = Column(
        String(120),
        nullable=False
    )