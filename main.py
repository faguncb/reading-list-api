from typing import Annotated, Optional
from fastapi import FastAPI, HTTPException, Query, Depends
from sqlmodel import Field, Session, SQLModel, create_engine, select

# --- 1. Database Setup ---
# SQLite is a single file, perfect for beginners[reference:6]

sqlite_file_name = "books.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

# check_same_thread=False is needed for SQLite to work with FastAPI's async nature[reference:7]
connect_args = {"check_same_thread" : False}
engine = create_engine(sqlite_url, connect_args=connect_args)

# --- 2. Define the Data Model (The Table) ---
# table=True tells SQLModel this class represents a database table[reference:8]

class Book(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    author: str
    status: str = Field(default="want_to_read") # e.g., "want_to_read", "reading", "read"

# --- 3. Create the Database Tables ---
# This runs once when the app starts to ensure the table exists[reference:9]

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

# --- 4. Dependency Injection for Database Sessions ---
# This ensures every request gets its own clean database session[reference:10]

def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]

# --- 5. Create the FastAPI App ---
app = FastAPI(title="Reading List API")

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

# --- 5.1 Show the root directory ---
@app.get("/")
def root():
    return {"message": "Reading List API is running. Go to /docs to explore."}

# --- 6. API Endpoints (CRUD) ---

# GET all books
@app.get("/books", response_model=list[Book])
def read_books(session: SessionDep, status: Optional[str] = Query(default = None)):
    query = select(Book)
    if status:
        query = query.where(Book.status == status)
    books = session.exec(query).all()
    return books

# POST a new book
@app.post("/books", response_model=Book, status_code=201)
def create_book(book: Book, session: SessionDep):
    session.add(book)
    session.commit()
    session.refresh(book)
    return book

# GET a single book by ID
@app.get("/books/{book_id}", response_model=Book)
def read_book(book_id: int, session: SessionDep):
    book = session.get(Book, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book


# PATCH (update) a book's status
@app.patch("/books/{book_id}", response_model=Book)
def update_book_status(book_id: int, status: str, session:SessionDep):
    book = session.get(Book, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    book.status = status
    session.add(book)
    session.commit()
    session.refresh(book)
    return book

# DELETE a book
@app.delete("/books/{book_id}", status_code=204)
def delete_book(book_id: int, session: SessionDep):
    book = session.get(Book, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    session.delete(book)
    session.commit()
    return None




