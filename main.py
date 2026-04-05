from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from pydantic import BaseModel
from typing import List
import jwt
from passlib.context import CryptContext

# =====================
# CONFIG
# =====================
SECRET_KEY = "secret123"
ALGORITHM = "HS256"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

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
# MODEL
# =====================
class Item(Base):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    description = Column(String)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True)
    password = Column(String)
    role = Column(String)

Base.metadata.create_all(bind=engine)

# =====================
# RESET DB (UNTUK TEST)
# =====================
def reset_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

# =====================
# SCHEMA
# =====================
class ItemCreate(BaseModel):
    name: str
    description: str

class ItemResponse(BaseModel):
    id: int
    name: str
    description: str

    class Config:
        orm_mode = True

class UserCreate(BaseModel):
    username: str
    password: str
    role: str

class Login(BaseModel):
    username: str
    password: str

# =====================
# APP
# =====================
app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# =====================
# AUTH FUNCTION
# =====================
def hash_password(password):
    return pwd_context.hash(password)

def verify_password(plain, hashed):
    return pwd_context.verify(plain, hashed)

def create_token(data: dict):
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(authorization: str = Header(None), db: Session = Depends(get_db)):
    if authorization is None:
        raise HTTPException(status_code=401, detail="No token")

    try:
        token = authorization.split(" ")[1]  # ambil Bearer token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user = db.query(User).filter(User.username == payload["username"]).first()
        return user
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

def get_admin(user: User = Depends(get_current_user)):
    if user.role != "admin":
        raise HTTPException(status_code=403)
    return user

# =====================
# AUTH ENDPOINT
# =====================
@app.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = User(
        username=user.username,
        password=hash_password(user.password),
        role=user.role
    )
    db.add(db_user)
    db.commit()
    return {"message": "registered"}

@app.post("/login")
def login(user: Login, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()

    if not db_user or not verify_password(user.password, db_user.password):
        raise HTTPException(status_code=401)

    token = create_token({"username": db_user.username, "role": db_user.role})
    return {"access_token": token}

# =====================
# CRUD ENDPOINT
# =====================
@app.post("/items/", response_model=ItemResponse)
def create_item(item: ItemCreate, db: Session = Depends(get_db)):
    new_item = Item(name=item.name, description=item.description)
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    return new_item

@app.get("/items/", response_model=List[ItemResponse])
def get_items(db: Session = Depends(get_db)):
    return db.query(Item).all()

@app.put("/items/{item_id}")
def update_item(item_id: int, item: ItemCreate, db: Session = Depends(get_db)):
    db_item = db.query(Item).filter(Item.id == item_id).first()
    db_item.name = item.name
    db_item.description = item.description
    db.commit()
    return {"message": "updated"}

@app.delete("/items/{item_id}")
def delete_item(item_id: int, db: Session = Depends(get_db), user: User = Depends(get_admin)):
    db_item = db.query(Item).filter(Item.id == item_id).first()
    db.delete(db_item)
    db.commit()
    return {"message": "deleted"}

# =====================
# TESTING (PYTEST)
# =====================
client = TestClient(app)

def test_register_and_login():
    reset_db()

    res = client.post("/register", json={
        "username": "admin",
        "password": "123",
        "role": "admin"
    })
    assert res.status_code == 200

    res = client.post("/login", json={
        "username": "admin",
        "password": "123"
    })
    assert res.status_code == 200
    assert "access_token" in res.json()

def test_crud_items():
    reset_db()

    res = client.post("/items/", json={
        "name": "Laptop",
        "description": "Gaming"
    })
    assert res.status_code == 200
    item_id = res.json()["id"]

    res = client.get("/items/")
    assert res.status_code == 200

    res = client.put(f"/items/{item_id}", json={
        "name": "Updated",
        "description": "Updated Desc"
    })
    assert res.status_code == 200

def test_rbac_access_denied():
    reset_db()

    client.post("/register", json={
        "username": "user",
        "password": "123",
        "role": "user"
    })

    login = client.post("/login", json={
        "username": "user",
        "password": "123"
    })

    token = login.json()["access_token"]

    res = client.post("/items/", json={
        "name": "Mouse",
        "description": "Gaming"
    })
    item_id = res.json()["id"]

    res = client.delete(
        f"/items/{item_id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert res.status_code == 403










# from fastapi import FastAPI, Depends, HTTPException
# from sqlalchemy import create_engine, Column, Integer, String
# from sqlalchemy.orm import sessionmaker, declarative_base, Session
# from pydantic import BaseModel
# from typing import List

# # =====================
# # DATABASE
# # =====================
# DATABASE_URL = "sqlite:///./items.db"

# engine = create_engine(
#     DATABASE_URL, connect_args={"check_same_thread": False}
# )

# SessionLocal = sessionmaker(bind=engine)

# Base = declarative_base()


# # =====================
# # MODEL DATABASE
# # =====================
# class Item(Base):
#     __tablename__ = "items"

#     id = Column(Integer, primary_key=True, index=True)
#     name = Column(String)
#     description = Column(String)


# Base.metadata.create_all(bind=engine)


# # =====================
# # PYDANTIC SCHEMA
# # =====================
# class ItemResponse(BaseModel):
#     id: int
#     name: str
#     description: str

#     class Config:
#         orm_mode = True


# # =====================
# # FASTAPI
# # =====================
# app = FastAPI()


# # Dependency database
# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()


# # =====================
# # DUMMY DATA (AGAR ADA DATA)
# # =====================
# db = SessionLocal()
# if db.query(Item).count() == 0:
#     db.add_all([
#         Item(name="Laptop", description="Laptop gaming"),
#         Item(name="Mouse", description="Mouse wireless")
#     ])
#     db.commit()
# db.close()


# # =====================
# # ENDPOINT
# # =====================

# # GET /items/
# @app.get("/items/", response_model=List[ItemResponse])
# def get_items(db: Session = Depends(get_db)):
#     items = db.query(Item).all()
#     return items


# # GET /items/{id}
# @app.get("/items/{item_id}", response_model=ItemResponse)
# def get_item(item_id: int, db: Session = Depends(get_db)):
#     item = db.query(Item).filter(Item.id == item_id).first()

#     if item is None:
#         raise HTTPException(status_code=404, detail="Item not found")

#     return item