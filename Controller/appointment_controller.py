from fastapi import HTTPException, APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime, time
from jose import jwt

from model.appointment_model import Appointment
from model.doctor_model import Doctors
from model.patient_model import Users
from model.appointment_schema import AppointmentRequest
from database import get_db
from fastapi.security import OAuth2PasswordBearer

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# ------------------------
# 0️⃣ جلب كل الدكاترة
# ------------------------
def get_all_doctors(db: Session):
    doctors = db.query(Doctors).all()
    result = []
    for doctor in doctors:
        result.append({
            "id": doctor.id,
            "name": doctor.name,
            "specialty": doctor.specialty
        })
    return {"doctors": result}

# ------------------------
# 1️⃣ حجز موعد جديد
# ------------------------
def book_appointment(db: Session, user: Users, doctor_id: int, date_time: datetime, reason: str = None):
    # التحقق من وجود الدكتور
    doctor = db.query(Doctors).filter(Doctors.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    # لا يمكن حجز موعد في الماضي
    now = datetime.now()
    if date_time <= now:
        raise HTTPException(status_code=400, detail="Cannot book an appointment in the past")

    # التحقق من ساعات العمل 10:00 - 16:00
    if date_time.time() < time(10, 0) or date_time.time() > time(16, 0):
        raise HTTPException(status_code=400, detail="Appointment must be within working hours (10:00 - 16:00)")

    # التحقق من أيام العمل Sunday-Thursday
    if date_time.weekday() > 4:  # 0=Monday ... 6=Sunday
        raise HTTPException(status_code=400, detail="Appointments are only allowed from Sunday to Thursday")

    # التحقق من دقائق الموعد (00 أو 30 فقط)
    if date_time.minute not in (0, 30):
        raise HTTPException(status_code=400, detail="Appointments must start at 00 or 30 minutes")

    # التحقق من التعارض مع مواعيد أخرى
    conflict = db.query(Appointment).filter(
        Appointment.doctor_id == doctor_id,
        Appointment.date_time == date_time,
        Appointment.status != "Cancelled"
    ).first()
    if conflict:
        raise HTTPException(status_code=400, detail="Doctor already has an appointment at this time")

    # إنشاء الموعد
    new_app = Appointment(
        user_id=user.id,
        doctor_id=doctor_id,
        date_time=date_time,
        reason=reason,
        status="Scheduled"
    )
    db.add(new_app)
    db.commit()
    db.refresh(new_app)

    return new_app

# ------------------------
# 2️⃣ إلغاء موعد
# ------------------------
def cancel_appointment(db: Session, user: Users, appointment_id: int):
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    # التحقق من ملكية الموعد
    if appointment.user_id != user.id:
        raise HTTPException(status_code=403, detail="You are not allowed to cancel this appointment")

    # التحقق من حالة الموعد
    if appointment.status == "Cancelled":
        raise HTTPException(status_code=400, detail="Appointment already cancelled")

    # لا يمكن إلغاء موعد قديم
    if appointment.date_time < datetime.now():
        raise HTTPException(status_code=400, detail="Cannot cancel a past appointment")

    appointment.status = "Cancelled"
    db.commit()
    db.refresh(appointment)

    return {"message": "Appointment cancelled successfully", "appointment_id": appointment.id}

# ------------------------
# 3️⃣ عرض كل مواعيد المريض
# ------------------------
def get_user_appointments(db: Session, user: Users):
    appointments = db.query(Appointment).filter(Appointment.user_id == user.id).all()
    if not appointments:
        return {"appointments": []}

    result = []
    for app in appointments:
        doctor = db.query(Doctors).filter(Doctors.id == app.doctor_id).first()
        doctor_name = doctor.name if doctor and doctor.name else "Unknown"

        result.append({
            "appointment_id": app.id,
            "doctor_name": doctor_name,
            "date_time": app.date_time.strftime("%Y-%m-%d %H:%M") if app.date_time else "-",
            "status": app.status if app.status else "-",
            "reason": app.reason if app.reason else "-"
        })

    return {"appointments": result}

# ------------------------
# 4️⃣ دالة لاستخراج id الدكتور من التوكن
# ------------------------
def get_doctor_id_from_token(token: str):
    payload = jwt.decode(token, "SECRET_KEY", algorithms=["HS256"])
    return payload.get("sub")  # id الدكتور

# ------------------------
# 5️⃣ عرض مواعيد الدكتور الخاصة به
# ------------------------
@router.get("/appointments/doctor")
def get_doctor_appointments(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    doctor_id = get_doctor_id_from_token(token)
    appointments = db.query(Appointment).filter(Appointment.doctor_id == doctor_id).all()

    result = []
    for app in appointments:
        patient = db.query(Users).filter(Users.id == app.user_id).first()
        result.append({
            "appointment_id": app.id,
            "patient_name": patient.name if patient else "Unknown",
            "date_time": app.date_time.isoformat(),
            "status": app.status,
            "reason": app.reason
        })
    return {"appointments": result}
