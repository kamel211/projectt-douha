from fastapi import APIRouter, UploadFile, File, Depends
from sqlalchemy.orm import Session
from database import get_db
from Controller import images_controller, appointment_controller

router = APIRouter(prefix="/images", tags=["Images"])


@router.post("/upload_to_appointment/{appointment_id}")
async def upload_image_to_appointment(
    appointment_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # 1. تحقق من الصورة
    images_controller.validate_image(file)

    # 2. حفظ الصورة
    filename = await images_controller.save_image(file)
    image_url = f"/uploads/{filename}"

    # 3. جلب الحجز
    appointment = appointment_controller.get_appointment(db, appointment_id)

    # 4. تسجيل الصورة في جدول الصور
    images_controller.register_image(db, appointment.user_id, filename)

    # 5. ربط الصورة بالحجز
    appointment_controller.attach_image_to_appointment(appointment, image_url)
    db.commit()
    db.refresh(appointment)

    return {
        "appointment_id": appointment.id,
        "image_url": image_url,
        "reason": appointment.reason
    }
