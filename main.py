# SYNTAX: imports from the fastapi package.
# FUNCTION: FastAPI = the app object itself; Depends = dependency injection
#           mechanism (used for get_db below); HTTPException = how we
#           deliberately return specific error status codes.
from fastapi import FastAPI, Depends, HTTPException


# SYNTAX: Session is SQLAlchemy's session type, imported here only for a
#         type hint (db: Session) — it doesn't create anything by itself.
from sqlalchemy.orm import Session


# FUNCTION: reusing the SAME models.py from the CLI project — the database
#           layer doesn't know or care that it's being called from an API
#           now instead of a CLI. This is the "layers" payoff mentioned
#           in the task.
from models import Note, Category, SessionLocal


# FUNCTION: our Pydantic contracts — what's valid to send in, and what
#           shape gets sent back out.
from schemas import NoteCreate, NoteOut, NoteUpdate, CategoryCreate, CategoryOut


# SYNTAX: FastAPI() creates the actual application object.
# FUNCTION: `app` is what uvicorn looks for when you run
#           `uvicorn main:app --reload` — everything below attaches
#           endpoints onto this one object.
app = FastAPI()


def get_db():
    # SYNTAX: this is a GENERATOR function because it uses `yield` instead
    #         of `return`. FastAPI's Depends() system specifically knows
    #         how to run code before AND after the yield, wrapping around
    #         whatever endpoint function uses this dependency.
    # FUNCTION: creates a brand-new database session for THIS request only.
    #           `yield db` hands that session to the endpoint function.
    #           Once the endpoint finishes (success OR error), execution
    #           resumes here and the `finally` block closes the session —
    #           guaranteeing every request cleans up after itself and
    #           never leaks an open connection.
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================================================
# NOTES ENDPOINTS
# ============================================================================


# SYNTAX: @app.post(...) is a decorator — it registers the function below
#         it to run whenever a POST request hits this path.
# FUNCTION: this line IS the REST principle from Day 8 made literal: the
#           URL ("/notes") names the RESOURCE, the method (post) names
#           the ACTION. status_code=201 = "Created", the correct code for
#           a successful creation (not the default 200).
@app.post("/notes", response_model=NoteOut, status_code=201)
def create_note(note: NoteCreate, db: Session = Depends(get_db)):
    # SYNTAX: `note: NoteCreate` — FastAPI automatically parses the
    #         incoming JSON body into a NoteCreate object, VALIDATING it
    #         against that schema before this function body even runs.
    #         `db: Session = Depends(get_db)` — FastAPI calls get_db()
    #         for us and injects the resulting session as `db`.
    # FUNCTION: if the client sends invalid data (e.g. category_id as
    #           text), FastAPI rejects it automatically with a 422 error —
    #           we never even have to check for that ourselves here.


    # SYNTAX: note.dict() turns the validated Pydantic object into a plain
    #         Python dict; **note.dict() unpacks that dict as keyword
    #         arguments into Note(...).
    # FUNCTION: builds a new SQLAlchemy Note object from the validated
    #           input — same object-construction step as the CLI's
    #           add_note() function.
    db_note = Note(**note.dict())


    db.add(db_note)     # stage the insert (not yet permanent)
    db.commit()          # FUNCTION: make it permanent — same ACID
                          # atomicity concept from Day 2.
    db.refresh(db_note)  # SYNTAX: reloads db_note's attributes from the DB.
                          # FUNCTION: pulls back the database-generated
                          # fields (id, created_at) so the response
                          # includes them.
    return db_note
    # FUNCTION: FastAPI converts this SQLAlchemy object into NoteOut JSON
    #           automatically, because of response_model=NoteOut above.


@app.get("/notes", response_model=list[NoteOut])
def list_notes(search: str | None = None, db: Session = Depends(get_db)):
    # SYNTAX: `search: str | None = None` — an optional query parameter.
    #         FastAPI reads this from the URL as ?search=... automatically,
    #         because it's a plain function parameter, not part of the path.
    # FUNCTION: this is the Day 8 answer to "why is search a query param,
    #           not part of the path" — GET /notes still means "the notes
    #           collection"; search just filters what comes back.
    query = db.query(Note)
    if search:
        # SYNTAX: Note.title.contains(search) builds a SQL LIKE clause.
        # FUNCTION: same filtering logic as the CLI's search_notes().
        query = query.filter(Note.title.contains(search))
    return query.order_by(Note.created_at.desc()).all()


@app.get("/notes/{note_id}", response_model=NoteOut)
def get_note(note_id: int, db: Session = Depends(get_db)):
    # SYNTAX: {note_id} in the decorator path binds directly to the
    #         note_id parameter below — FastAPI extracts it from the URL
    #         and converts it to an int automatically.
    # FUNCTION: fetches ONE specific note by id — the REST equivalent of
    #           GET /notes/5 from Day 8's table.
    note = db.query(Note).filter(Note.id == note_id).first()
    if not note:
        # SYNTAX: raise HTTPException(...) immediately stops the function
        #         and sends this response instead.
        # FUNCTION: explicit 404 status code — communicating the outcome
        #           through the STATUS CODE, exactly as Day 8 emphasized,
        #           not just via the response body text.
        raise HTTPException(status_code=404, detail="Note not found")
    return note


@app.delete("/notes/{note_id}")
def delete_note(note_id: int, db: Session = Depends(get_db)):
    note = db.query(Note).filter(Note.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")


    # FUNCTION: stage the deletion — this line was MISSING in the original
    #           task's sample code. Without it, commit() below would have
    #           nothing to actually delete.
    db.delete(note)
    db.commit()
    return {"message": "Note deleted"}


@app.patch("/notes/{note_id}", response_model=NoteOut)
def update_note(note_id: int, note: NoteUpdate, db: Session = Depends(get_db)):
    # FUNCTION: this is the PATCH-vs-PUT distinction from Day 8, in code.
    db_note = db.query(Note).filter(Note.id == note_id).first()
    if not db_note:
        raise HTTPException(status_code=404, detail="Note not found")


    # SYNTAX: note.dict(exclude_unset=True) returns ONLY the fields the
    #         client actually included in their request JSON — any field
    #         left out entirely is excluded, not included as None.
    # FUNCTION: this is what makes it a true PARTIAL update. Without
    #           exclude_unset=True, every omitted field would default to
    #           None and OVERWRITE the existing value — which is the PUT
    #           "replace everything" behavior, not PATCH's "only change
    #           what I sent" behavior.
    for field, value in note.dict(exclude_unset=True).items():
        # SYNTAX: setattr(obj, field_name, value) sets an attribute on an
        #         object dynamically, using a string for the field name.
        # FUNCTION: applies each provided field's new value onto the
        #           existing note object.
        setattr(db_note, field, value)


    db.commit()
    db.refresh(db_note)
    return db_note


# ============================================================================
# CATEGORIES ENDPOINTS
# ============================================================================


@app.post("/categories", response_model=CategoryOut, status_code=201)
def create_category(category: CategoryCreate, db: Session = Depends(get_db)):
    db_category = Category(**category.dict())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category


@app.get("/categories", response_model=list[CategoryOut])
def list_categories(db: Session = Depends(get_db)):
    return db.query(Category).all()


@app.delete("/categories/{category_id}")
def delete_category(category_id: int, db: Session = Depends(get_db)):
    # FUNCTION: same pattern as delete_note — fetch, check existence,
    #           delete, commit. Consistency in pattern is the whole point
    #           of "you now have the pattern, apply it" from the task.
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    db.delete(category)
    db.commit()
    return {"message": "Category deleted"}
