# -------------------------------
# appointments_router.py
# -------------------------------
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime, time
from bson.objectid import ObjectId

from database import appointments_collection, doctors_collection, patients_collection, images_collection
from Controller.patient_controller import get_current_patient

router = APIRouter(prefix="/appointments", tags=["Appointments"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# -------------------------------
# 0️⃣ جلب كل الدكاترة
# -------------------------------
@router.get("/doctors")
def get_all_doctors():
    doctors = list(doctors_collection.find())
    result = [{"id": str(doc["_id"]), "name": doc["name"], "specialty": doc.get("specialty", "")} for doc in doctors]
    return {"doctors": result}


# -------------------------------
# 1️⃣ رفع صورة
# -------------------------------
@router.post("/upload_file/")
async def upload_file(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_patient)
):
    # حفظ الصورة في MongoDB
    new_image = {
        "user_id": str(user["_id"]),
        "filename": file.filename,
        "path": f"uploads/{file.filename}",
        "created_at": datetime.utcnow()
    }
    result = images_collection.insert_one(new_image)
    return {"message": "File uploaded successfully", "image_id": str(result.inserted_id)}


# -------------------------------
# 2️⃣ حجز موعد جديد
# -------------------------------
@router.post("/book")
def create_appointment(doctor_id: str, date_time: datetime, reason: str = None, image_id: str = None, user: dict = Depends(get_current_patient)):
    # التحقق من وجود الدكتور
    doctor = doctors_collection.find_one({"_id": ObjectId(doctor_id)})
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    # منع الحجز في الماضي
    if date_time <= datetime.now():
        raise HTTPException(status_code=400, detail="Cannot book an appointment in the past")

    # التحقق من ساعات العمل 10:00 - 16:00
    if date_time.time() < time(10, 0) or date_time.time() > time(16, 0):
        raise HTTPException(status_code=400, detail="Appointment must be within working hours (10:00-16:00)")

    # أيام العمل Sunday-Thursday
    if date_time.weekday() > 4:
        raise HTTPException(status_code=400, detail="Appointments are only allowed from Sunday to Thursday")

    # دقائق الموعد
    if date_time.minute not in (0, 30):
        raise HTTPException(status_code=400, detail="Appointments must start at 00 or 30 minutes")

    # التحقق من التعارض مع مواعيد أخرى
    conflict = appointments_collection.find_one({
        "doctor_id": doctor_id,
        "date_time": date_time,
        "status": {"$ne": "Cancelled"}
    })
    if conflict:
        raise HTTPException(status_code=400, detail="Doctor already has an appointment at this time")

    # إنشاء الموعد
    new_app = {
        "user_id": str(user["_id"]),
        "doctor_id": doctor_id,
        "date_time": date_time,
        "reason": reason,
        "status": "Scheduled",
        "image_id": image_id
    }
    result = appointments_collection.insert_one(new_app)
    return {"message": "Appointment booked successfully", "appointment_id": str(result.inserted_id)}


# -------------------------------
# 3️⃣ عرض مواعيد المريض
# -------------------------------
@router.get("/my-appointments")
def get_user_appointments(user: dict = Depends(get_current_patient)):
    appointments = list(appointments_collection.find({"user_id": str(user["_id"])}))
    result = []
    for app in appointments:
        doctor = doctors_collection.find_one({"_id": ObjectId(app["doctor_id"])})
        image = images_collection.find_one({"_id": ObjectId(app["image_id"])}) if app.get("image_id") else None
        result.append({
            "appointment_id": str(app["_id"]),
            "doctor_name": doctor["name"] if doctor else "Unknown",
            "date_time": app["date_time"].strftime("%Y-%m-%d %H:%M"),
            "status": app["status"],
            "reason": app.get("reason", "-"),
            "image_url": image["path"] if image else None
        })
    return {"appointments": result}


# -------------------------------
# 4️⃣ إلغاء موعد
# -------------------------------
@router.delete("/cancel/{appointment_id}")
def cancel_appointment(appointment_id: str, user: dict = Depends(get_current_patient)):
    appointment = appointments_collection.find_one({"_id": ObjectId(appointment_id), "user_id": str(user["_id"])})
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    if appointment["status"] == "Cancelled":
        raise HTTPException(status_code=400, detail="Appointment already cancelled")

    if appointment["date_time"] < datetime.now():
        raise HTTPException(status_code=400, detail="Cannot cancel a past appointment")

    appointments_collection.update_one(
        {"_id": ObjectId(appointment_id)},
        {"$set": {"status": "Cancelled"}}
    )

    return {"message": "Appointment cancelled successfully", "appointment_id": appointment_id}




# # -------------------------------
# # appointments_router.py
# # -------------------------------
# from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
# from fastapi.security import OAuth2PasswordBearer
# from sqlalchemy.orm import Session
# from datetime import datetime
# from database import get_db
# from model.appointment_model import Appointment
# from model.patient_model import Users
# from model.images_model import Images
# from model.appointment_schema import AppointmentRequest
# from Controller.patient_controller import get_current_patient

# router = APIRouter(prefix="/appointments", tags=["Appointments"])
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# # -------------------------------
# # 0️⃣ رفع صورة
# # -------------------------------
# @router.post("/upload_file/")
# async def upload_file(
#     file: UploadFile = File(...),
#     db: Session = Depends(get_db),
#     user: Users = Depends(get_current_patient)
# ):
#     # حفظ الصورة في قاعدة البيانات
#     new_image = Images(
#         user_id=user.id,
#         filename=file.filename,
#         path=f"uploads/{file.filename}"
#     )
#     db.add(new_image)
#     db.commit()
#     db.refresh(new_image)

#     return {"message": "File uploaded successfully", "image_id": new_image.id}


# # -------------------------------
# # 1️⃣ حجز موعد مع صورة
# # -------------------------------
# @router.post("/book")
# def create_appointment_endpoint(
#     appointment: AppointmentRequest,
#     db: Session = Depends(get_db),
#     user: Users = Depends(get_current_patient)
# ):
#     # التحقق من وجود الدكتور
#     doctor = db.query(Users).filter(Users.id == appointment.doctor_id).first()
#     if not doctor:
#         raise HTTPException(status_code=404, detail="Doctor not found")

#     # منع الحجز في الماضي
#     if appointment.date_time <= datetime.now():
#         raise HTTPException(status_code=400, detail="Cannot book an appointment in the past")

#     # التحقق من ساعات العمل 10:00 - 16:00
#     if appointment.date_time.time() < datetime.strptime("10:00", "%H:%M").time() or \
#        appointment.date_time.time() > datetime.strptime("16:00", "%H:%M").time():
#         raise HTTPException(status_code=400, detail="Appointment must be within working hours (10:00-16:00)")

#     # التحقق من أيام العمل Sunday-Thursday
#     if appointment.date_time.weekday() > 4:
#         raise HTTPException(status_code=400, detail="Appointments are only allowed from Sunday to Thursday")

#     # التحقق من دقائق الموعد
#     if appointment.date_time.minute not in (0, 30):
#         raise HTTPException(status_code=400, detail="Appointments must start at 00 or 30 minutes")

#     # التحقق من التعارض مع مواعيد أخرى
#     conflict = db.query(Appointment).filter(
#         Appointment.doctor_id == appointment.doctor_id,
#         Appointment.date_time == appointment.date_time,
#         Appointment.status != "Cancelled"
#     ).first()
#     if conflict:
#         raise HTTPException(status_code=400, detail="Doctor already has an appointment at this time")

#     # إنشاء الموعد
#     new_app = Appointment(
#         user_id=user.id,
#         doctor_id=appointment.doctor_id,
#         date_time=appointment.date_time,
#         reason=appointment.reason,
#         status="Scheduled",
#         image_id=appointment.image_id  # ← ربط الصورة بالموعد
#     )
#     db.add(new_app)
#     db.commit()
#     db.refresh(new_app)

#     return {"message": "Appointment booked successfully", "appointment_id": new_app.id}


# # -------------------------------
# # 2️⃣ عرض مواعيد المريض مع الصورة
# # -------------------------------
# @router.get("/my-appointments")
# def get_user_appointments(db: Session = Depends(get_db), user: Users = Depends(get_current_patient)):
#     appointments = db.query(Appointment).filter(Appointment.user_id == user.id).all()

#     result = []
#     for app in appointments:
#         doctor_name = app.doctor.name if app.doctor else "Unknown"
#         result.append({
#             "appointment_id": app.id,
#             "doctor_name": doctor_name,
#             "date_time": app.date_time.strftime("%Y-%m-%d %H:%M"),
#             "status": app.status,
#             "reason": app.reason,
#             "image_url": app.image.path if app.image else None  # ← رابط الصورة
#         })
#     return {"appointments": result}


# # -------------------------------
# # 3️⃣ إلغاء موعد
# # -------------------------------
# @router.delete("/cancel/{appointment_id}")
# def cancel_appointment(appointment_id: int, db: Session = Depends(get_db), user: Users = Depends(get_current_patient)):
#     appointment = db.query(Appointment).filter(Appointment.id == appointment_id, Appointment.user_id == user.id).first()
#     if not appointment:
#         raise HTTPException(status_code=404, detail="Appointment not found")

#     if appointment.status == "Cancelled":
#         raise HTTPException(status_code=400, detail="Appointment already cancelled")

#     if appointment.date_time < datetime.now():
#         raise HTTPException(status_code=400, detail="Cannot cancel a past appointment")

#     appointment.status = "Cancelled"
#     db.commit()
#     db.refresh(appointment)

#     return {"message": "Appointment cancelled successfully", "appointment_id": appointment.id}