from fastapi import HTTPException, Depends, Request
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
from jose import jwt, JWTError
from fastapi.security import OAuth2PasswordBearer
from typing import Optional
from database import mongo_db  # MongoDB connection

# ================== إعدادات ==================
doctors_collection = mongo_db["doctors"]
bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = "mysecretkey"
ALGORITHM = "HS256"
blacklisted_tokens = set()
MAX_BCRYPT_BYTES = 72
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/doctors/login")

# ================== النماذج ==================
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

# ================== دوال JWT ==================
def create_access_token(username: str, user_id: str, expires_delta: Optional[timedelta] = None):
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

# ================== دوال الطبيب ==================
def register_doctor(request: CreateDoctorRequest):
    if len(request.password.encode('utf-8')) > MAX_BCRYPT_BYTES:
        raise HTTPException(status_code=400, detail="Password too long, max 72 bytes")

    existing = doctors_collection.find_one({
        "$or": [{"username": request.username}, {"email": request.email}]
    })
    if existing:
        if existing["username"] == request.username:
            raise HTTPException(status_code=400, detail="Username already exists")
        else:
            raise HTTPException(status_code=400, detail="Email already exists")

    password_bytes = request.password.encode('utf-8')[:MAX_BCRYPT_BYTES]
    hashed_password = bcrypt_context.hash(password_bytes.decode('utf-8', errors='ignore'))

    new_doctor = {
        "username": request.username,
        "email": request.email,
        "first_name": request.first_name,
        "last_name": request.last_name,
        "role": request.role,
        "hashed_password": hashed_password,
        "phone_number": request.phone_number,
        "appointments": [],  # جدول المواعيد
        "is_active": True,
        "created_at": datetime.utcnow()
    }

    result = doctors_collection.insert_one(new_doctor)
    return {"message": "Doctor registered successfully", "doctor_id": str(result.inserted_id)}


def login_doctor(request_data: LoginDoctorRequest, request: Request):
    # التحقق أن المستخدم أرسل إما الإيميل أو اسم المستخدم
    if not request_data.username and not request_data.email:
        raise HTTPException(status_code=400, detail="يجب إدخال البريد الإلكتروني أو اسم المستخدم")

    # البحث عن الطبيب باستخدام أحدهما
    query = {}
    if request_data.username:
        query = {"username": request_data.username}
    elif request_data.email:
        query = {"email": request_data.email}

    doctor = doctors_collection.find_one(query)

    if not doctor or not bcrypt_context.verify(request_data.password, doctor["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid username/email or password")

    if not doctor.get("is_active", True):
        raise HTTPException(status_code=400, detail="الحساب غير مفعل. يرجى التواصل مع الإدارة.")

    token = create_access_token(doctor["username"], str(doctor["_id"]))
    return {
        "message": f"Welcome Dr. {doctor['first_name']}!",
        "access_token": token,
        "token_type": "bearer",
        "doctor_id": str(doctor["_id"]),
        "doctor_data": {
            "username": doctor["username"],
            "email": doctor["email"],
            "full_name": f"{doctor['first_name']} {doctor['last_name']}",
            "role": doctor["role"],
            "appointments": doctor.get("appointments", [])
        }
    }
def logout_doctor(token: str):
    blacklisted_tokens.add(token)
    return {"message": "Logged out successfully"}

def change_password_doctor(request_data: ChangePasswordRequest, current_user):
    if not bcrypt_context.verify(request_data.old_password, current_user["hashed_password"]):
        raise HTTPException(status_code=400, detail="Old password is incorrect")
    if bcrypt_context.verify(request_data.new_password, current_user["hashed_password"]):
        raise HTTPException(status_code=400, detail="New password must be different from old password")

    password_bytes = request_data.new_password.encode('utf-8')[:MAX_BCRYPT_BYTES]
    hashed_new_password = bcrypt_context.hash(password_bytes.decode('utf-8', errors='ignore'))

    doctors_collection.update_one(
        {"_id": current_user["_id"]},
        {"$set": {"hashed_password": hashed_new_password}}
    )
    return {"message": "Password changed successfully ✅"}

def update_doctor_profile(update_data: UpdateDoctorRequest, current_user):
    updates = {}
    if update_data.first_name:
        updates["first_name"] = update_data.first_name
    if update_data.last_name:
        updates["last_name"] = update_data.last_name
    if update_data.phone_number:
        updates["phone_number"] = update_data.phone_number
    if update_data.email:
        existing = doctors_collection.find_one({
            "email": update_data.email,
            "_id": {"$ne": current_user["_id"]}
        })
        if existing:
            raise HTTPException(status_code=400, detail="Email already exists")
        updates["email"] = update_data.email

    if updates:
        doctors_collection.update_one({"_id": current_user["_id"]}, {"$set": updates})

    updated_user = doctors_collection.find_one({"_id": current_user["_id"]})
    updated_user["_id"] = str(updated_user["_id"])
    return {"message": "Profile updated successfully ✅", "doctor": updated_user}

# ================== المستخدم الحالي ==================
def get_current_doctor(token: str = Depends(oauth2_scheme)):
    username = verify_token(token)
    doctor = doctors_collection.find_one({"username": username})
    if not doctor:
        raise HTTPException(status_code=401, detail="Doctor not found")
    doctor["_id"] = str(doctor["_id"])
    return doctor
