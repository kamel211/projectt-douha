from fastapi import HTTPException, APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime, time
from jose import jwt
from database import get_db
from model.appointment_model import Appointment
from model.doctor_model import Doctors
from model.patient_model import Users
from Controller.images_controller import get_last_user_image  # ✅ استيراد
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
# 1️⃣ حجز موعد جديد مع ربط آخر صورة
# ------------------------
def book_appointment(db: Session, user: Users, doctor_id: int, date_time: datetime, reason: str = None):
    doctor = db.query(Doctors).filter(Doctors.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    now = datetime.now()
    if date_time <= now:
        raise HTTPException(status_code=400, detail="Cannot book an appointment in the past")

    if date_time.time() < time(10, 0) or date_time.time() > time(16, 0):
        raise HTTPException(status_code=400, detail="Appointment must be within working hours (10:00 - 16:00)")

    if date_time.weekday() > 4:
        raise HTTPException(status_code=400, detail="Appointments are only allowed from Sunday to Thursday")

    if date_time.minute not in (0, 30):
        raise HTTPException(status_code=400, detail="Appointments must start at 00 or 30 minutes")

    conflict = db.query(Appointment).filter(
        Appointment.doctor_id == doctor_id,
        Appointment.date_time == date_time,
        Appointment.status != "Cancelled"
    ).first()
    if conflict:
        raise HTTPException(status_code=400, detail="Doctor already has an appointment at this time")

    # ✅ جلب آخر صورة رفعها المريض وربطها بالحجز
    last_image = get_last_user_image(db, user.id)
    image_id = last_image.id if last_image else None

    new_app = Appointment(
        user_id=user.id,
        doctor_id=doctor_id,
        date_time=date_time,
        reason=reason,
        status="Scheduled",
        image_id=image_id  # ✅ ربط الصورة
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

    if appointment.user_id != user.id:
        raise HTTPException(status_code=403, detail="You are not allowed to cancel this appointment")

    if appointment.status == "Cancelled":
        raise HTTPException(status_code=400, detail="Appointment already cancelled")

    if appointment.date_time < datetime.now():
        raise HTTPException(status_code=400, detail="Cannot cancel a past appointment")

    appointment.status = "Cancelled"
    db.commit()
    db.refresh(appointment)

    return {"message": "Appointment cancelled successfully", "appointment_id": appointment.id}


# ------------------------
# 3️⃣ عرض كل مواعيد المريض مع رابط الصورة
# ------------------------
def get_user_appointments(db: Session, user: Users):
    appointments = db.query(Appointment).filter(Appointment.user_id == user.id).all()
    if not appointments:
        return {"appointments": []}

    result = []
    for app in appointments:
        doctor = db.query(Doctors).filter(Doctors.id == app.doctor_id).first()
        doctor_name = doctor.name if doctor and doctor.name else "Unknown"

        image_url = app.image.url if app.image else None  # ✅ رابط الصورة

        result.append({
            "appointment_id": app.id,
            "doctor_name": doctor_name,
            "date_time": app.date_time.strftime("%Y-%m-%d %H:%M") if app.date_time else "-",
            "status": app.status if app.status else "-",
            "reason": app.reason if app.reason else "-",
            "image_url": image_url
        })

    return {"appointments": result}


# ------------------------
# 4️⃣ استخراج id الدكتور من التوكن
# ------------------------
def get_doctor_id_from_token(token: str):
    payload = jwt.decode(token, "SECRET_KEY", algorithms=["HS256"])
    return payload.get("sub")


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
        image_url = app.image.url if app.image else None  # ✅ رابط الصورة للطبيب
        result.append({
            "appointment_id": app.id,
            "patient_name": patient.name if patient else "Unknown",
            "date_time": app.date_time.isoformat(),
            "status": app.status,
            "reason": app.reason,
            "image_url": image_url
        })
    return {"appointments": result}
