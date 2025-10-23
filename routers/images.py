
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from Controller.patient_controller import get_current_patient
from Controller.images_controller import upload_to_local, get_user_images

router = APIRouter(prefix="/images", tags=["Images"])

# ---------------- رفع صورة واحدة ----------------
@router.post("/upload/")
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user = Depends(get_current_patient),
    appointment_id: int | None = None  # 👈 إضافة هذا السطر الجديد
):
    """
    يرفع صورة جديدة للمستخدم الحالي، ويمكن ربطها مباشرة بموعد إن تم تمرير appointment_id
    """
    return upload_to_local(file, user.id, db, appointment_id)  # 👈 تمرير appointment_id إلى الدالة


# ---------------- استرجاع كل صور المستخدم ----------------
@router.get("/me")
def get_my_images(
    db: Session = Depends(get_db),
    user = Depends(get_current_patient)
):
    """
    يعيد جميع الصور التي رفعها المستخدم الحالي
    """
    return get_user_images(db, user.id)
