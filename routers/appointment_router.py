# -------------------------------
# appointments_router.py
# -------------------------------
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from bson import ObjectId
from bson.errors import InvalidId
from datetime import datetime
from core.auth_utils import get_user_id_from_token,get_doctor_id_from_token # دالة استخراج id من JWT
from database import appointments_collection, doctors_collection, patients_collection


router = APIRouter(prefix="/appointments", tags=["Appointments"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# -------------------------------
# 1️⃣ قائمة الدكاترة
# -------------------------------
@router.get("/doctors")
def list_doctors(token: str = Depends(oauth2_scheme)):
    """جلب قائمة الدكاترة النشطين"""
    doctors = []
    for doc in doctors_collection.find({"is_active": True}):
        doctors.append({
            "id": str(doc["_id"]),
            "full_name": f"{doc['first_name']} {doc['last_name']}",
            "email": doc.get("email", ""),
            "work_hours": doc.get("work_hours", "10:00-16:00"),
            "days": doc.get("work_days", ["Sunday","Monday","Tuesday","Wednesday","Thursday"])
        })
    return doctors

# -------------------------------
# 2️⃣ حجز موعد
# -------------------------------
@router.post("/book")
def create_appointment(
    doctor_id: str,
    date_time: datetime,
    reason: str = "",
    token: str = Depends(oauth2_scheme)
):
    """حجز موعد للمريض"""
    user_id = get_user_id_from_token(token)

    # التأكد من وجود المريض
    patient = patients_collection.find_one({"_id": ObjectId(user_id)})
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # التحقق من صحة doctor_id
    try:
        doc_obj_id = ObjectId(doctor_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid doctor_id")

    doctor = doctors_collection.find_one({"_id": doc_obj_id})
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    # منع حجز في الماضي
    if date_time < datetime.now():
        raise HTTPException(status_code=400, detail="Cannot book in the past")

    # إنشاء الموعد
    appointment = {
        "doctor_id": str(doc_obj_id),
        "patient_id": str(patient["_id"]),
        "patient_name": f"{patient['first_name']} {patient['last_name']}",
        "date_time": date_time,
        "reason": reason,
        "status": "Scheduled"
    }

    result = appointments_collection.insert_one(appointment)
    return {"message": "Appointment booked successfully", "appointment_id": str(result.inserted_id)}

# -------------------------------
# 3️⃣ عرض مواعيد المريض
# -------------------------------
@router.get("/my-appointments")
def get_user_appointments(token: str = Depends(oauth2_scheme)):
    """جلب جميع مواعيد المريض الحالي"""
    user_id = get_user_id_from_token(token)
    appointments = list(appointments_collection.find({"patient_id": user_id}))

    result = []
    for appt in appointments:
        doctor_id = appt.get("doctor_id")
        doctor_name = "غير معروف"
        if doctor_id:
            doctor = doctors_collection.find_one({"_id": ObjectId(doctor_id)})
            if doctor:
                doctor_name = f"{doctor['first_name']} {doctor['last_name']}"

        result.append({
            "appointment_id": str(appt["_id"]),
            "doctor_name": doctor_name,
            "date_time": appt["date_time"].isoformat() if hasattr(appt["date_time"], "isoformat") else str(appt["date_time"]),
            "status": appt.get("status", "Unknown"),
            "reason": appt.get("reason", "-")
        })
    return result

# -------------------------------
# 4️⃣ عرض مواعيد الدكتور الحالي
# -------------------------------
@router.get("/doctor-appointments")
def get_doctor_appointments(token: str = Depends(oauth2_scheme)):
    """جلب جميع المواعيد للطبيب المسجل دخول"""
    doctor_id = get_user_id_from_token(token)  # id الدكتور من التوكن
    appointments = list(appointments_collection.find({"doctor_id": doctor_id}))

    result = []
    for appt in appointments:
        patient_id = appt.get("patient_id")
        patient_name = "غير معروف"
        if patient_id:
            patient = patients_collection.find_one({"_id": ObjectId(patient_id)})
            if patient:
                patient_name = f"{patient['first_name']} {patient['last_name']}"

        result.append({
            "appointment_id": str(appt["_id"]),
            "patient_name": patient_name,
            "date_time": appt["date_time"].isoformat() if hasattr(appt["date_time"], "isoformat") else str(appt["date_time"]),
            "status": appt.get("status", "Unknown"),
            "reason": appt.get("reason", "-")
        })
    return result

# -------------------------------
# 5️⃣ إلغاء موعد
# -------------------------------
@router.delete("/cancel/{appointment_id}")
def cancel_appointment(appointment_id: str, token: str = Depends(oauth2_scheme)):
    """إلغاء موعد من قبل المريض"""
    user_id = get_user_id_from_token(token)
    try:
        appt_obj_id = ObjectId(appointment_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid appointment_id")

    appointment = appointments_collection.find_one({"_id": appt_obj_id, "patient_id": user_id})
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    appointments_collection.update_one({"_id": appt_obj_id}, {"$set": {"status": "Cancelled"}})
    return {"message": "Appointment cancelled successfully"}


@router.post("/approve-cancel/{appointment_id}")
def approve_cancel_appointment(appointment_id: str, token: str = Depends(oauth2_scheme)):
    """الدكتور يوافق على إلغاء موعد"""
    doctor_id = get_doctor_id_from_token(token)
    try:
        appt_obj_id = ObjectId(appointment_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid appointment_id")

    # ------------------ هنا مؤقت للتأكد من البيانات ------------------
    appointment = appointments_collection.find_one({"_id": appt_obj_id})
    print(appointment)  # ستشوف كل بيانات الموعد في console
    # ---------------------------------------------------------------

    if not appointment or appointment.get("status") != "PendingCancellation":
        raise HTTPException(status_code=404, detail="Appointment not found or not pending cancellation")

    appointments_collection.delete_one({"_id": appt_obj_id})
    return {"message": "تم إلغاء الموعد بنجاح"}

@router.post("/request-cancel/{appointment_id}")
def request_cancel_appointment(appointment_id: str, token: str = Depends(oauth2_scheme)):
    """المريض يطلب إلغاء الموعد → يحتاج موافقة الدكتور"""
    user_id = get_user_id_from_token(token)
    try:
        appt_obj_id = ObjectId(appointment_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid appointment_id")

    appointment = appointments_collection.find_one({"_id": appt_obj_id, "patient_id": user_id})
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    # نغير الحالة إلى PendingCancellation
    appointments_collection.update_one({"_id": appt_obj_id}, {"$set": {"status": "PendingCancellation"}})
    return {"message": "تم طلب إلغاء الموعد، بانتظار موافقة الدكتور"}
