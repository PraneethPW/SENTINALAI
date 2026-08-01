from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from app.core.config import get_settings

raw_url = get_settings().postgres_url
# Railway and Neon commonly expose `postgresql://`; explicitly select the
# installed psycopg v3 driver instead of SQLAlchemy's psycopg2 default.
if raw_url.startswith("postgresql://"):
    url = raw_url.replace("postgresql://", "postgresql+psycopg://", 1)
elif raw_url.startswith("postgres://"):
    url = raw_url.replace("postgres://", "postgresql+psycopg://", 1)
else:
    url = raw_url
engine = create_engine(url, connect_args={"check_same_thread": False} if url.startswith("sqlite") else {})
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

class Base(DeclarativeBase): pass

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()
