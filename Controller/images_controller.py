from pathlib import Path
import uuid
from fastapi import UploadFile, HTTPException
from PIL import Image
import aiofiles
from model.images_model import Images

# مجلد رفع الصور
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = (".jpg", ".jpeg", ".png")


# تحقق من امتداد الملف وصلاحيته
def validate_image(file: UploadFile):
    if not file.filename.lower().endswith(ALLOWED_EXTENSIONS):
        raise HTTPException(status_code=400, detail="الملف يجب أن يكون JPG أو PNG فقط")
    try:
        img = Image.open(file.file)
        img.verify()
        file.file.seek(0)
    except:
        raise HTTPException(status_code=400, detail="الملف ليس صورة صالحة")


# رفع الصورة وحفظها محليًا
async def save_image(file: UploadFile) -> str:
    filename = f"{uuid.uuid4().hex}_{file.filename}"
    file_path = UPLOAD_DIR / filename
    async with aiofiles.open(file_path, "wb") as out_file:
        content = await file.read()
        await out_file.write(content)
    return filename


# تسجيل الصورة في قاعدة البيانات
def register_image(db, user_id: int, filename: str) -> Images:
    new_image = Images(filename=filename, url=f"/uploads/{filename}", user_id=user_id)
    db.add(new_image)
    db.commit()
    db.refresh(new_image)
    return new_image
