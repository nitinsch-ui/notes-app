# SYNTAX: import — pulls specific names out of the sqlalchemy package.
# FUNCTION: these are the building blocks used to describe our tables as classes.
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey

# SYNTAX: importing from the .orm submodule specifically.
# FUNCTION: declarative_base = parent class our tables inherit from;
#           relationship = links two tables in Python; sessionmaker = builds
#           our "connection to the database" object.
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

# SYNTAX: func lets us call real SQL functions (like NOW()) from Python.
# FUNCTION: used below so the DATABASE stamps the creation time, not Python.
from sqlalchemy.sql import func

# SYNTAX: calling declarative_base() returns a class to inherit from.
# FUNCTION: Base is the shared parent that makes SQLAlchemy treat Category
#           and Note as real database tables, not just plain Python classes.
Base = declarative_base()


class Category(Base):
    # SYNTAX: __tablename__ is a special attribute SQLAlchemy looks for.
    # FUNCTION: names the real SQL table "categories" — like CREATE TABLE categories.
    __tablename__ = 'categories'

    # SYNTAX: Column(Integer, primary_key=True) declares a column and its type.
    # FUNCTION: id uniquely identifies each category row; primary_key=True
    #           makes the database auto-generate it and index it automatically.
    id = Column(Integer, primary_key=True)

    # SYNTAX: String(50) = VARCHAR(50); unique=True adds a uniqueness constraint.
    # FUNCTION: stores the category's actual name, e.g. "Work".
    name = Column(String(50), unique=True)

    # SYNTAX: relationship() is NOT a real column — it's a Python-only link.
    # FUNCTION: lets us write some_category.notes to get every Note pointing
    #           back at this category, without writing SQL by hand.
    notes = relationship("Note", back_populates="category")


class Note(Base):
    # FUNCTION: represents the "many" side of the one-to-many relationship.
    __tablename__ = 'notes'

    id = Column(Integer, primary_key=True)

    # SYNTAX: String has a length cap; Text does not.
    # FUNCTION: title is short/searchable, content holds the full note body.
    title = Column(String(200))
    content = Column(Text)

    # SYNTAX: ForeignKey('categories.id') creates a real enforced constraint.
    # FUNCTION: THE actual foreign key column — this single value can only
    #           point at ONE category, which is why it lives on notes and
    #           not on categories (one category -> many notes).
    category_id = Column(Integer, ForeignKey('categories.id'))

    # SYNTAX: server_default=func.now() — default value computed by the DB itself.
    # FUNCTION: auto-timestamps every note on creation, used later for sorting newest-first.
    created_at = Column(DateTime, server_default=func.now())

    # SYNTAX: mirror relationship, pointing the other direction.
    # FUNCTION: lets us write some_note.category — but note: the FIRST time
    #           this is accessed without being pre-loaded, it silently fires
    #           a new query (lazy loading) — the root cause of N+1 bugs later.
    category = relationship("Category", back_populates="notes")


# SYNTAX: create_engine(url) returns an Engine — the core DB connection object.
# FUNCTION: connects our code to a real notes.db file (created if missing).
engine = create_engine('sqlite:///notes.db', echo=False)

# SYNTAX: Base.metadata.create_all(engine) is a method call against the
#         metadata SQLAlchemy tracked from every class defined under Base.
# FUNCTION: runs the equivalent of CREATE TABLE for both tables — safe to
#           call every run, since it skips tables that already exist.
Base.metadata.create_all(engine)

# SYNTAX: sessionmaker(bind=engine) returns a class; calling it creates an instance.
# FUNCTION: session is our "open conversation" with the database, used by
#           every function we'll add in later commits.
Session = sessionmaker(bind=engine)
session = Session()

print("Models created, database connected successfully.")

