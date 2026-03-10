from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from pydantic import BaseModel
from typing import List

# =====================
# DATABASE
# =====================
DATABASE_URL = "sqlite:///./items.db"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()


# =====================
# MODEL DATABASE
# =====================
class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    description = Column(String)


Base.metadata.create_all(bind=engine)


# =====================
# PYDANTIC SCHEMA
# =====================
class ItemResponse(BaseModel):
    id: int
    name: str
    description: str

    class Config:
        orm_mode = True


# =====================
# FASTAPI
# =====================
app = FastAPI()


# Dependency database
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# =====================
# DUMMY DATA (AGAR ADA DATA)
# =====================
db = SessionLocal()
if db.query(Item).count() == 0:
    db.add_all([
        Item(name="Laptop", description="Laptop gaming"),
        Item(name="Mouse", description="Mouse wireless")
    ])
    db.commit()
db.close()


# =====================
# ENDPOINT
# =====================

# GET /items/
@app.get("/items/", response_model=List[ItemResponse])
def get_items(db: Session = Depends(get_db)):
    items = db.query(Item).all()
    return items


# GET /items/{id}
@app.get("/items/{item_id}", response_model=ItemResponse)
def get_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(Item).filter(Item.id == item_id).first()

    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")

    return item