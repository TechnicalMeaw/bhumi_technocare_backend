from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from urllib.parse import quote_plus
from ..src import config

settings = config.settings


SQLALCHEMY_DATABASE_URL = (f'postgresql://{settings.database_username}:%s@{settings.database_hostname}:{settings.database_port}/{settings.database_name}' % quote_plus (settings.database_password))


engine = create_engine(SQLALCHEMY_DATABASE_URL, 
                       pool_pre_ping=True,
                       pool_size=10,      # Adjust pool size according to your needs
                       max_overflow=20,   # Number of connections that can be created beyond the pool_size
                       pool_timeout=30,   # Timeout for getting a connection from the pool
                       pool_recycle=1800  # Recycle connections after a certain time to prevent stale connections
                       )


SessionLocal = sessionmaker(autoflush = False, autocommit = False, bind = engine)

Base = declarative_base()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
