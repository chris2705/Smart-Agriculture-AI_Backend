from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.models import User

SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_app.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def list_users():
    db = SessionLocal()
    try:
        users = db.query(User).all()
        print(f"{'ID':<5} {'Full Name':<20} {'Email':<30}")
        print("-" * 60)
        for user in users:
            print(f"{user.id:<5} {user.full_name:<20} {user.email:<30}")
    finally:
        db.close()

if __name__ == "__main__":
    list_users()
