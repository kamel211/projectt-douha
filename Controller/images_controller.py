from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session
from model.images_model import Images
from pathlib import Path
import shutil
import uuid

# مجلد حفظ الصور
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# الامتدادات المسموحة
ALLOWED_EXTENSIONS = (".jpg", ".jpeg", ".png")

# ---------------- رفع صورة واحدة ----------------
def upload_to_local(file: UploadFile, user_id: int, db: Session):
    if not file.filename.lower().endswith(ALLOWED_EXTENSIONS):
        raise HTTPException(status_code=400, detail="الملف يجب أن يكون JPG أو PNG فقط")

    try:
        # إنشاء اسم فريد للصورة
        filename = f"{uuid.uuid4().hex}_{file.filename.lower()}"
        file_path = UPLOAD_DIR / filename

        # حفظ الصورة على السيرفر
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # حفظ معلومات الصورة في قاعدة البيانات
        new_image = Images(
            filename=filename,
            url=f"/uploads/{filename}",
            user_id=user_id
        )
        db.add(new_image)
        db.commit()
        db.refresh(new_image)

        return {
            "id": new_image.id,
            "filename": new_image.filename,
            "url": new_image.url,
            "user_id": new_image.user_id 
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"فشل الرفع: {str(e)}")


# ---------------- استرجاع صور المستخدم ----------------
def get_user_images(db: Session, user_id: int):
    images = db.query(Images).filter(Images.user_id == user_id).all()
    return [
        {"id": img.id, "filename": img.filename, "url": img.url, "user_id": img.user_id}
        for img in images
    ]
