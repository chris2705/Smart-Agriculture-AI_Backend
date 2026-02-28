from passlib.context import CryptContext
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

try:
    print("Testing Passlib...")
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    hash = pwd_context.hash("password123")
    print(f"Hash created: {hash[:10]}...")
    print("Passlib OK")
except Exception as e:
    print(f"Passlib FAILED: {e}")

try:
    print("Testing DB...")
    SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_app.db"
    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    print("DB Connection OK")
    db.close()
except Exception as e:
    print(f"DB FAILED: {e}")
