from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload

from models import Category, Note, SessionLocal


session = SessionLocal()


def add_category():
    """Prompts for a category name and saves it, handling duplicate name errors."""
    name = input("Category name: ").strip()

    if not name:
        print("Name can't be empty.")
        return

    session.add(Category(name=name))

    try:
        session.commit()
        print(f"Added category: {name}")
    except IntegrityError:
        # Roll back the failed INSERT so the session stays usable.
        session.rollback()
        print(f"Category '{name}' already exists.")


def add_note():
    """Lists categories, gets user input, and links a new Note to the selected category."""
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

    if session.get(Category, cat_id) is None:
        print(f"No category with id {cat_id}.")
        return

    title = input("Title: ").strip()
    content = input("Content: ").strip()

    session.add(Note(title=title, content=content, category_id=cat_id))
    session.commit()
    print("Note added.")


def list_notes():
    """Lists notes newest-first, loading each note's category in the same query."""
    # joinedload fetches notes and categories in one JOIN instead of 1 + N queries.
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
    """Substring search on note titles."""
    keyword = input("Search keyword (in title): ").strip()

    results = session.query(Note).filter(Note.title.contains(keyword)).all()

    if not results:
        print("No matches.")
        return

    for n in results:
        print(f"[{n.id}] {n.title}")


def delete_note():
    """Deletes a note by id."""
    try:
        note_id = int(input("Note id to delete: "))
    except ValueError:
        print("That's not a valid id.")
        return

    note = session.get(Note, note_id)

    if note is None:
        print("No note with that id.")
        return

    session.delete(note)
    session.commit()
    print("Deleted.")


def menu():
    """Main CLI loop."""
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


if __name__ == "__main__":
    menu()
