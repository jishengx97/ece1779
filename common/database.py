from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import database_exists, create_database

DATABASE_URL = "mysql+pymysql://root:ece1779pass@127.0.0.1/ece1779project"

engine = create_engine(DATABASE_URL, execution_options={"isolation_level": "READ COMMITTED"})
if not database_exists(engine.url):
    create_database(engine.url)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def init_db():
    from . import models
    Base.metadata.create_all(bind=engine)