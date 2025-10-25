# ================== main.py ==================
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from jose import jwt, JWTError
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from datetime import datetime, timedelta
import asyncio
from typing import Optional

from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

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
class Patient(Base):
    __tablename__ = "patients"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    first_name = Column(String(50))
    last_name = Column(String(50))
    role = Column(String(20))
    hashed_password = Column(String(200))
    phone_number = Column(String(20))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

# ---------------- Security & JWT ----------------
bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = "mysecretkey"
ALGORITHM = "HS256"
blacklisted_tokens = set()
MAX_BCRYPT_LENGTH = 72
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/patients/login")

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

# ---------------- Email setup ----------------
conf = ConnectionConfig(
    MAIL_USERNAME="douh@gmail.com",
    MAIL_PASSWORD="douhash",
    MAIL_FROM="douh@gmail.com",
    MAIL_PORT=587,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True
)

async def send_login_notification(email_to: EmailStr, user, ip_address: str = "غير معروف"):
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    body = f"""
مرحبًا {user.first_name} {user.last_name}،
تم تسجيل دخول جديد إلى حسابك في النظام.

📅 التاريخ والوقت: {now}
🌐 عنوان IP: {ip_address}
👤 اسم المستخدم: {user.username}

إذا لم تكن أنت من قام بتسجيل الدخول، يرجى تغيير كلمة المرور فورًا."""
    
    message = MessageSchema(
        subject="تسجيل دخول جديد 👋 - نظام إدارة المستشفى",
        recipients=[email_to],
        body=body,
        subtype="plain"
    )
    try:
        fm = FastMail(conf)
        await fm.send_message(message)
    except Exception as e:
        print(f"❌ فشل إرسال الإشعار إلى {email_to}: {e}")

# ---------------- Schemas ----------------
class CreateUserRequest(BaseModel):
    username: str
    email: EmailStr
    first_name: str
    last_name: str
    password: str
    role: str
    phone_number: str

class LoginUserRequest(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: str

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

class UpdatePatientRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[EmailStr] = None

# ---------------- CRUD Functions ----------------
def register_user(request: CreateUserRequest, db: Session):
    if len(request.password.encode('utf-8')) > MAX_BCRYPT_LENGTH:
        raise HTTPException(status_code=400, detail="Password too long, max 72 bytes")
    
    existing_user = db.query(Patient).filter(
        (Patient.username == request.username) | (Patient.email == request.email)
    ).first()
    if existing_user:
        if existing_user.username == request.username:
            raise HTTPException(status_code=400, detail="Username already exists")
        else:
            raise HTTPException(status_code=400, detail="Email already exists")
    
    hashed_password = bcrypt_context.hash(request.password[:MAX_BCRYPT_LENGTH])
    new_user = Patient(
        username=request.username,
        email=request.email,
        first_name=request.first_name,
        last_name=request.last_name,
        role=request.role,
        phone_number=request.phone_number,
        hashed_password=hashed_password
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User registered successfully", "user_id": new_user.id}

async def login_user(request_data: LoginUserRequest, request: Request, db: Session):
    query = db.query(Patient)
    if request_data.username:
        user = query.filter(Patient.username == request_data.username).first()
    elif request_data.email:
        user = query.filter(Patient.email == request_data.email).first()
    else:
        raise HTTPException(status_code=400, detail="يرجى إدخال اسم المستخدم أو البريد الإلكتروني")

    if not user or not bcrypt_context.verify(request_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="اسم المستخدم أو كلمة المرور غير صحيحة")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="الحساب غير مفعل. يرجى التواصل مع الإدارة.")
    
    token = create_access_token(user.username, user.id)
    client_host = request.client.host if request.client else "غير معروف"
    asyncio.create_task(send_login_notification(user.email, user, client_host))
    
    return {
        "message": f"مرحباً بعودتك {user.first_name}!",
        "access_token": token,
        "token_type": "bearer",
        "user_id": user.id,
        "user_data": {
            "username": user.username,
            "email": user.email,
            "full_name": f"{user.first_name} {user.last_name}",
            "role": user.role
        }
    }

def logout_user(token: str):
    blacklisted_tokens.add(token)
    return {"message": "Logged out successfully"}

def change_password(request_data: ChangePasswordRequest, current_user: Patient, db: Session):
    if not bcrypt_context.verify(request_data.old_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="كلمة المرور القديمة غير صحيحة")
    if bcrypt_context.verify(request_data.new_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="كلمة المرور الجديدة يجب أن تكون مختلفة عن القديمة")
    
    current_user.hashed_password = bcrypt_context.hash(request_data.new_password)
    db.commit()
    return {"message": "تم تغيير كلمة المرور بنجاح ✅"}

def update_patient_profile(update_data: UpdatePatientRequest, current_user: Patient, db: Session):
    if update_data.first_name: current_user.first_name = update_data.first_name
    if update_data.last_name: current_user.last_name = update_data.last_name
    if update_data.phone_number: current_user.phone_number = update_data.phone_number
    if update_data.email:
        existing_user = db.query(Patient).filter(Patient.email == update_data.email, Patient.id != current_user.id).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already exists")
        current_user.email = update_data.email
    db.commit()
    db.refresh(current_user)
    return {"message": "تم تحديث البيانات بنجاح ✅", "user": current_user}

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    username = verify_token(token)
    user = db.query(Patient).filter(Patient.username == username).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

def get_current_patient(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    return get_current_user(token, db)
