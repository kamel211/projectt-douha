# auth_utils.py
from fastapi import HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError

# ---------------- إعدادات JWT ----------------
SECRET_KEY = "mysecretkey"
ALGORITHM = "HS256"

# ---------------- OAuth2 ----------------
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/doctors/login")  # رابط endpoint تسجيل الدخول

def get_user_id_from_token(token: str) -> str:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def get_doctor_id_from_token(token: str):
    """
    دالة لاستخراج id الدكتور من JWT
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        doctor_id = payload.get("id")  # تأكد أن الـ key هنا هو "id" وليس "sub"
        if not doctor_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        return doctor_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")



# def get_doctor_id_from_token(token: str):
#     """
#     دالة لاستخراج id الدكتور من JWT
#     """
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         doctor_id = payload.get("sub")
#         if not doctor_id:
#             raise HTTPException(status_code=401, detail="Invalid token")
#         return doctor_id
#     except JWTError:
#         raise HTTPException(status_code=401, detail="Invalid token")
