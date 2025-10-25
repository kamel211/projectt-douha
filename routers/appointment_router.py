from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from sqlalchemy.orm import Session
from datetime import datetime, time

from database import get_db
from model.appointment_model import Appointment
from model.doctor_model import Doctors
from model.patient_model import Users
from model.images_model import Images
from Controller.patient_controller import get_current_patient

router = APIRouter(prefix="/appointments", tags=["Appointments"])

# -------------------------------
# 0️⃣ جلب كل الدكاترة
# -------------------------------
@router.get("/doctors")
def get_all_doctors(db: Session = Depends(get_db)):
    doctors = db.query(Doctors).all()
    return {
        "doctors": [
            {"id": doctor.id, "name": doctor.name, "specialty": doctor.specialty}
            for doctor in doctors
        ]
    }

# -------------------------------
# 1️⃣ رفع صورة
# -------------------------------
@router.post("/upload_file/")
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: Users = Depends(get_current_patient)
):
    # حفظ الصورة محليًا
    import uuid, aiofiles, os
    UPLOAD_DIR = "uploads"
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    filename = f"{uuid.uuid4().hex}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    async with aiofiles.open(file_path, "wb") as out_file:
        content = await file.read()
        await out_file.write(content)

    # تسجيل الصورة في قاعدة البيانات
    new_image = Images(
        user_id=user.id,
        filename=filename,
        url=file_path
    )
    db.add(new_image)
    db.commit()
    db.refresh(new_image)
    return {"message": "File uploaded successfully", "image_id": new_image.id}

# -------------------------------
# 2️⃣ حجز موعد جديد مع آخر صورة
# -------------------------------
@router.post("/book")
def create_appointment(
    doctor_id: int,
    date_time: datetime,
    reason: str = None,
    db: Session = Depends(get_db),
    user: Users = Depends(get_current_patient)
):
    doctor = db.query(Doctors).filter(Doctors.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    now = datetime.now()
    if date_time <= now:
        raise HTTPException(status_code=400, detail="Cannot book an appointment in the past")

    if date_time.time() < time(10, 0) or date_time.time() > time(16, 0):
        raise HTTPException(status_code=400, detail="Appointment must be within working hours (10:00-16:00)")

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

    # جلب آخر صورة رفعها المستخدم
    last_image = db.query(Images).filter(Images.user_id == user.id).order_by(Images.id.desc()).first()
    image_id = last_image.id if last_image else None

    new_app = Appointment(
        user_id=user.id,
        doctor_id=doctor.id,
        date_time=date_time,
        reason=reason,
        status="Scheduled",
        image_id=image_id
    )
    db.add(new_app)
    db.commit()
    db.refresh(new_app)
    return {"message": "Appointment booked successfully", "appointment_id": new_app.id}

# -------------------------------
# 3️⃣ عرض مواعيد المريض
# -------------------------------
@router.get("/my-appointments")
def get_user_appointments(
    db: Session = Depends(get_db),
    user: Users = Depends(get_current_patient)
):
    appointments = db.query(Appointment).filter(Appointment.user_id == user.id).all()
    result = []
    for app in appointments:
        doctor_name = app.doctor.name if app.doctor else "Unknown"
        image_url = app.image.url if app.image else None
        result.append({
            "appointment_id": app.id,
            "doctor_name": doctor_name,
            "date_time": app.date_time.strftime("%Y-%m-%d %H:%M"),
            "status": app.status,
            "reason": app.reason or "-",
            "image_url": image_url
        })
    return {"appointments": result}

# -------------------------------
# 4️⃣ إلغاء موعد
# -------------------------------
@router.delete("/cancel/{appointment_id}")
def cancel_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    user: Users = Depends(get_current_patient)
):
    appointment = db.query(Appointment).filter(
        Appointment.id == appointment_id,
        Appointment.user_id == user.id
    ).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    if appointment.status == "Cancelled":
        raise HTTPException(status_code=400, detail="Appointment already cancelled")

    if appointment.date_time < datetime.now():
        raise HTTPException(status_code=400, detail="Cannot cancel a past appointment")

    appointment.status = "Cancelled"
    db.commit()
    db.refresh(appointment)
    return {"message": "Appointment cancelled successfully", "appointment_id": appointment.id}
