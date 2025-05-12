from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import oracledb
import os

DATABASE_USERNAME = os.getenv("DATABASE_USERNAME")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")
DATABASE_DSN = os.getenv("DATABASE_DSN")

def oracle_connection_factory():
    return oracledb.connect(
        user=DATABASE_USERNAME,
        password=DATABASE_PASSWORD,
         dsn=DATABASE_DSN
    )

engine = create_engine(
    "oracle+oracledb://",
    creator=oracle_connection_factory
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# DB 세션 의존성
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 