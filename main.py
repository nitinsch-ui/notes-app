from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from models import Note, Category, SessionLocal
from schemas import NoteCreate, NoteOut, NoteUpdate, CategoryCreate, CategoryOut


app = FastAPI(title="Notes API")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_category_exists(db: Session, category_id: int):
    if db.get(Category, category_id) is None:
        raise HTTPException(status_code=422, detail=f"Category {category_id} does not exist")


# ---------------------------------------------------------------------------
# Notes
# ---------------------------------------------------------------------------

@app.post("/notes", response_model=NoteOut, status_code=201)
def create_note(note: NoteCreate, db: Session = Depends(get_db)):
    ensure_category_exists(db, note.category_id)
    db_note = Note(**note.model_dump())
    db.add(db_note)
    db.commit()
    db.refresh(db_note)
    return db_note


@app.get("/notes", response_model=list[NoteOut])
def list_notes(search: str | None = None, db: Session = Depends(get_db)):
    query = db.query(Note)
    if search:
        query = query.filter(Note.title.contains(search))
    return query.order_by(Note.created_at.desc()).all()


@app.get("/notes/{note_id}", response_model=NoteOut)
def get_note(note_id: int, db: Session = Depends(get_db)):
    note = db.get(Note, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note


@app.patch("/notes/{note_id}", response_model=NoteOut)
def update_note(note_id: int, note: NoteUpdate, db: Session = Depends(get_db)):
    db_note = db.get(Note, note_id)
    if not db_note:
        raise HTTPException(status_code=404, detail="Note not found")

    # exclude_unset: only fields the client sent are changed (PATCH, not PUT).
    updates = note.model_dump(exclude_unset=True)
    if updates.get("category_id") is not None:
        ensure_category_exists(db, updates["category_id"])

    for field, value in updates.items():
        setattr(db_note, field, value)

    db.commit()
    db.refresh(db_note)
    return db_note


@app.delete("/notes/{note_id}")
def delete_note(note_id: int, db: Session = Depends(get_db)):
    note = db.get(Note, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    db.delete(note)
    db.commit()
    return {"message": "Note deleted"}


# ---------------------------------------------------------------------------
# Categories
# ---------------------------------------------------------------------------

@app.post("/categories", response_model=CategoryOut, status_code=201)
def create_category(category: CategoryCreate, db: Session = Depends(get_db)):
    db_category = Category(**category.model_dump())
    db.add(db_category)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail=f"Category '{category.name}' already exists")
    db.refresh(db_category)
    return db_category


@app.get("/categories", response_model=list[CategoryOut])
def list_categories(db: Session = Depends(get_db)):
    return db.query(Category).all()


@app.delete("/categories/{category_id}")
def delete_category(category_id: int, db: Session = Depends(get_db)):
    category = db.get(Category, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    # Refuse rather than cascade, so deleting a category never silently deletes notes.
    note_count = db.query(Note).filter(Note.category_id == category_id).count()
    if note_count:
        raise HTTPException(
            status_code=409,
            detail=f"Category has {note_count} note(s); delete or move them first",
        )

    db.delete(category)
    db.commit()
    return {"message": "Category deleted"}
