from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import os
from dotenv import load_dotenv

load_dotenv()

# Подключение к базе данных контента
CONTENT_DATABASE_URL = os.getenv("CONTENT_DATABASE_URL")
content_engine = create_engine(CONTENT_DATABASE_URL, connect_args={"check_same_thread": False})

ContentSessionLocal: sessionmaker[Session] = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=content_engine
)

ContentBase = declarative_base()