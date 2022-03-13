from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import database_exists, create_database

DATABASE_URL = "mysql+pymysql://root:ece1779pass@ece1779project.ctx9tvih2qlf.us-east-1.rds.amazonaws.com:3306/ece1779project"
 

engine = create_engine(DATABASE_URL, echo=True)
if not database_exists(engine.url):
    create_database(engine.url)

SessionLocal = sessionmaker(autocommit=False, autoflush=True, bind=engine)

Base = declarative_base()

def init_db():
    from . import models
    Base.metadata.create_all(bind=engine)