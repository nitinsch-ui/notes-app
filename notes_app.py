from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import declarative_base, relationship, sessionmaker, joinedload
from sqlalchemy.sql import func

# Declarative Base: standard SQLAlchemy setup. Every ORM model class inherits
# from this Base so SQLAlchemy can track and map them to database tables.
Base = declarative_base()


class Category(Base):
    __tablename__ = 'categories'

    # Primary key columns are auto-incrementing integers by default in SQLite.
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True)

    # Relationship (Parent side): 'notes' is a Python attribute (not a DB column).
    # back_populates links it to Note.category so both sides update dynamically.
    notes = relationship("Note", back_populates="category")


class Note(Base):
    __tablename__ = 'notes'

    id = Column(Integer, primary_key=True)
    title = Column(String(200))
    content = Column(Text)

    # Foreign Key: actual column stored in the database pointing to categories.id.
    category_id = Column(Integer, ForeignKey('categories.id'))

    # server_default=func.now() lets the SQL database set the timestamp upon insert,
    # avoiding potential timezone mismatches from local Python time.
    created_at = Column(DateTime, server_default=func.now())

    # Relationship (Child side): allows direct access to the linked Category object (e.g., note.category.name).
    category = relationship("Category", back_populates="notes")


# Database Setup: create_engine defines connection details; create_all builds missing tables.
engine = create_engine('sqlite:///notes.db', echo=False)
Base.metadata.create_all(engine)

# Session Setup: sessionmaker manages database connections and transactions.
Session = sessionmaker(bind=engine)
session = Session()

print("Models created, database connected successfully.")


def add_category():
    """Prompts for a category name and saves it, handling duplicate name errors."""
    name = input("Category name: ").strip()

    if not name:
        print("Name can't be empty.")
        return

    category = Category(name=name)
    session.add(category)

    # Unit of Work Pattern: session.add() stages changes; session.commit() flushes
    # and executes the INSERT inside a single atomic transaction.
    try:
        session.commit()
        print(f"Added category: {name}")
    except IntegrityError:
        # If a DB constraint fails (e.g., duplicate unique name), rollback clears
        # the pending failed changes so future session operations don't fail.
        session.rollback()
        print(f"Category '{name}' already exists.")


def add_note():
    """Lists categories, gets user input, and links a new Note to the selected Category ID."""
    categories = session.query(Category).all()

    if not categories:
        print("No categories yet — add one first.")
        return

    print("Existing categories:")
    for c in categories:
        print(f"  {c.id}: {c.name}")

    try:
        cat_id = int(input("Category id: "))
    except ValueError:
        print("That's not a valid id.")
        return

    title = input("Title: ").strip()
    content = input("Content: ").strip()

    note = Note(title=title, content=content, category_id=cat_id)
    session.add(note)
    session.commit()
    print("Note added.")


def list_notes():
    """Fetches notes sorted newest-first. Uses eager loading to prevent N+1 query overhead."""
    # N+1 Optimization: joinedload performs an SQL JOIN under the hood to fetch Note
    # and Category together in 1 query, rather than triggering 1 query for notes
    # plus N extra queries every time note.category is accessed.
    notes = (
        session.query(Note)
        .options(joinedload(Note.category))
        .order_by(Note.created_at.desc())
        .all()
    )

    if not notes:
        print("No notes yet.")
        return

    for n in notes:
        cat_name = n.category.name if n.category else "Uncategorized"
        print(f"[{n.id}] {n.title}  —  category: {cat_name}  (created {n.created_at})")


def search_notes():
    """Performs a substring search against note titles using SQL LIKE."""
    keyword = input("Search keyword (in title): ").strip()

    # Note.title.contains(k) translates to: WHERE notes.title LIKE '%k%'
    results = session.query(Note).filter(Note.title.contains(keyword)).all()

    if not results:
        print("No matches.")
        return

    for n in results:
        print(f"[{n.id}] {n.title}")


def delete_note():
    """Look up a note by primary key ID and remove it."""
    try:
        note_id = int(input("Note id to delete: "))
    except ValueError:
        print("That's not a valid id.")
        return

    # session.get() is optimized for primary key lookups; returns None if missing.
    note = session.get(Note, note_id)

    if note is None:
        print("No note with that id.")
        return

    session.delete(note)
    session.commit()
    print("Deleted.")


def menu():
    """Main CLI loop for routing user operations."""
    while True:
        print("\n--- Notes App ---")
        print("1) Add category")
        print("2) Add note")
        print("3) List notes (newest first)")
        print("4) Search notes by title")
        print("5) Delete note")
        print("6) Quit")

        choice = input("> ").strip()

        if choice == "1":
            add_category()
        elif choice == "2":
            add_note()
        elif choice == "3":
            list_notes()
        elif choice == "4":
            search_notes()
        elif choice == "5":
            delete_note()
        elif choice == "6":
            print("Bye!")
            break
        else:
            print("Not a valid option, try again.")


# Standard entry-point check: ensures main execution code only runs when executed directly.
if __name__ == "__main__":
    menu()