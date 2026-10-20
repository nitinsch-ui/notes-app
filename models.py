import os
import sqlite3

from sqlalchemy import create_engine, event, Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy.sql import func


Base = declarative_base()


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True)

    notes = relationship("Note", back_populates="category")


class Note(Base):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True)
    title = Column(String(200))
    content = Column(Text)
    category_id = Column(Integer, ForeignKey("categories.id"))
    created_at = Column(DateTime, server_default=func.now())

    category = relationship("Category", back_populates="notes")


@event.listens_for(Engine, "connect")
def _enable_sqlite_foreign_keys(dbapi_connection, connection_record):
    # SQLite ignores FOREIGN KEY constraints unless enabled on every connection.
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///notes.db")

engine = create_engine(DATABASE_URL, echo=False)
Base.metadata.create_all(engine)

SessionLocal = sessionmaker(bind=engine)
