from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import oracledb
import os

Base = declarative_base()

def create_production_engine():
    engine = create_engine(
        "oracle+oracledb://",
        creator=oracle_connection_factory
    )
    return engine

def oracle_connection_factory():
    DATABASE_USERNAME = os.getenv("DATABASE_USERNAME")
    DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")
    DATABASE_DSN = os.getenv("DATABASE_DSN")
    return oracledb.connect(
        user=DATABASE_USERNAME,
        password=DATABASE_PASSWORD,
         dsn=DATABASE_DSN
    )


def create_development_engine():
    engine = create_engine("sqlite://", echo=True, connect_args={"check_same_thread": False})
    return engine

if os.getenv("RUNNING_ENVIRONMENT") == "development":
    engine = create_development_engine()
else:
    engine = create_production_engine()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

if os.getenv("RUNNING_ENVIRONMENT") == "development":
    init_db()

# DB 세션 의존성
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 