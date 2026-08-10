# SYNTAX: standard SQLAlchemy imports.
# FUNCTION: same building blocks used in the Day 7 CLI app — the DB layer
#           itself doesn't change at all when moving to an API.
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy.sql import func


# FUNCTION: shared parent class that makes SQLAlchemy treat Category/Note
#           as real database tables.
Base = declarative_base()


class Category(Base):
    __tablename__ = 'categories'


    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True)


    # SYNTAX: relationship() is a Python-only link, not a real column.
    # FUNCTION: lets us write some_category.notes to get every related Note.
    notes = relationship("Note", back_populates="category")


class Note(Base):
    __tablename__ = 'notes'


    id = Column(Integer, primary_key=True)
    title = Column(String(200))
    content = Column(Text)


    # FUNCTION: the real foreign key — this is the "many" side of the
    #           one-to-many relationship (many notes -> one category each).
    category_id = Column(Integer, ForeignKey('categories.id'))


    # SYNTAX: server_default=func.now() — the DATABASE computes this value.
    # FUNCTION: auto-timestamps each note; used for sorting newest-first.
    created_at = Column(DateTime, server_default=func.now())


    category = relationship("Category", back_populates="notes")


# SYNTAX: create_engine(url) builds the core connection object.
# FUNCTION: connects to the same notes.db file your CLI app already uses —
#           you can run the CLI and the API against the SAME data.
engine = create_engine('sqlite:///notes.db', echo=False)


# FUNCTION: creates the tables if they don't already exist — safe to call
#           every time the app starts.
Base.metadata.create_all(engine)


# SYNTAX: sessionmaker(bind=engine) returns a CLASS (a factory), not an
#         actual session instance.
# FUNCTION: unlike the CLI app (which made ONE shared session for its whole
#           run), the API needs a FRESH session per incoming request — so
#           here we only export the factory. main.py calls SessionLocal()
#           fresh, once per request, via the get_db() dependency.
SessionLocal = sessionmaker(bind=engine)
