from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import database_exists, create_database
from decouple import config

database_username = config('RDS_DATABASE_USERNAME')
database_password = config('RDS_DATABASE_PASSWORD')
database_endpoint = config('RDS_DATABASE_ENDPOINT')
database_port = config('RDS_DATABASE_PORT')
database_name = config('RDS_DATABASE_NAME')
DATABASE_URL = "mysql+pymysql://" + database_username + ":" + database_password + "@" + database_endpoint + ":" + database_port + "/" + database_name
 

engine = create_engine(DATABASE_URL, echo=True)
if not database_exists(engine.url):
    create_database(engine.url)

SessionLocal = sessionmaker(autocommit=False, autoflush=True, bind=engine)

Base = declarative_base()

def init_db():
    from . import models
    Base.metadata.create_all(bind=engine)