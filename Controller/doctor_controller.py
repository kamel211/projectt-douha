# ================== main_doctors.py ==================
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
from typing import Optional
from jose import jwt, JWTError
from datetime import datetime, timedelta

# ---------------- Database setup ----------------
DATABASE_URL = "postgresql+psycopg2://username:password@localhost:5432/yourdb"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------------- Models ----------------
class Doctor(Base):
    __tablename__ = "doctors"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    first_name = Column(String(50))
    last_name = Column(String(50))
    role = Column(String(20))
    hashed_password = Column(String(200))
    phone_number = Column(String(20))
    appointments = Column(Text, default="[]")  # تخزين المواعيد كـ JSON نصي
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

# ---------------- Security & JWT ----------------
bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = "mysecretkey"
ALGORITHM = "HS256"
blacklisted_tokens = set()
MAX_BCRYPT_BYTES = 72
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/doctors/login")

def create_access_token(username: str, user_id: int, expires_delta: Optional[timedelta] = None):
    expire = datetime.utcnow() + (expires_delta or timedelta(hours=2))
    payload = {"sub": username, "id": user_id, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str):
    if token in blacklisted_tokens:
        raise HTTPException(status_code=401, detail="Session expired. Please login again.")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token")
        return username
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ---------------- Schemas ----------------
class CreateDoctorRequest(BaseModel):
    username: str
    email: EmailStr
    first_name: str
    last_name: str
    password: str
    role: str
    phone_number: str

class LoginDoctorRequest(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: str

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

class UpdateDoctorRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[EmailStr] = None

# ---------------- CRUD Functions ----------------
def register_doctor(request: CreateDoctorRequest, db: Session):
    if len(request.password.encode('utf-8')) > MAX_BCRYPT_BYTES:
        raise HTTPException(status_code=400, detail="Password too long, max 72 bytes")

    existing = db.query(Doctor).filter(
        (Doctor.username == request.username) | (Doctor.email == request.email)
    ).first()
    if existing:
        if existing.username == request.username:
            raise HTTPException(status_code=400, detail="Username already exists")
        else:
            raise HTTPException(status_code=400, detail="Email already exists")

    hashed_password = bcrypt_context.hash(request.password[:MAX_BCRYPT_BYTES])
    new_doctor = Doctor(
        username=request.username,
        email=request.email,
        first_name=request.first_name,
        last_name=request.last_name,
        role=request.role,
        phone_number=request.phone_number,
        hashed_password=hashed_password
    )
    db.add(new_doctor)
    db.commit()
    db.refresh(new_doctor)
    return {"message": "Doctor registered successfully", "doctor_id": new_doctor.id}

def login_doctor(request_data: LoginDoctorRequest, db: Session):
    if not request_data.username and not request_data.email:
        raise HTTPException(status_code=400, detail="يجب إدخال البريد الإلكتروني أو اسم المستخدم")

    query = db.query(Doctor)
    if request_data.username:
        doctor = query.filter(Doctor.username == request_data.username).first()
    else:
        doctor = query.filter(Doctor.email == request_data.email).first()

    if not doctor or not bcrypt_context.verify(request_data.password, doctor.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid username/email or password")
    if not doctor.is_active:
        raise HTTPException(status_code=400, detail="الحساب غير مفعل. يرجى التواصل مع الإدارة.")

    token = create_access_token(doctor.username, doctor.id)
    return {
        "message": f"Welcome Dr. {doctor.first_name}!",
        "access_token": token,
        "token_type": "bearer",
        "doctor_id": doctor.id,
        "doctor_data": {
            "username": doctor.username,
            "email": doctor.email,
            "full_name": f"{doctor.first_name} {doctor.last_name}",
            "role": doctor.role,
            "appointments": doctor.appointments
        }
    }

def logout_doctor(token: str):
    blacklisted_tokens.add(token)
    return {"message": "Logged out successfully"}

def change_password_doctor(request_data: ChangePasswordRequest, current_user: Doctor, db: Session):
    if not bcrypt_context.verify(request_data.old_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Old password is incorrect")
    if bcrypt_context.verify(request_data.new_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="New password must be different from old password")

    current_user.hashed_password = bcrypt_context.hash(request_data.new_password[:MAX_BCRYPT_BYTES])
    db.commit()
    return {"message": "Password changed successfully ✅"}

def update_doctor_profile(update_data: UpdateDoctorRequest, current_user: Doctor, db: Session):
    if update_data.first_name: current_user.first_name = update_data.first_name
    if update_data.last_name: current_user.last_name = update_data.last_name
    if update_data.phone_number: current_user.phone_number = update_data.phone_number
    if update_data.email:
        existing = db.query(Doctor).filter(Doctor.email == update_data.email, Doctor.id != current_user.id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already exists")
        current_user.email = update_data.email
    db.commit()
    db.refresh(current_user)
    return {"message": "Profile updated successfully ✅", "doctor": current_user}

def get_current_doctor(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    username = verify_token(token)
    doctor = db.query(Doctor).filter(Doctor.username == username).first()
    if not doctor:
        raise HTTPException(status_code=401, detail="Doctor not found")
    return doctor
