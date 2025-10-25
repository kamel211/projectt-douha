         
from pathlib import Path
import uuid
from fastapi import UploadFile, HTTPException
from PIL import Image
import aiofiles
from model.images_model import Images

# ---------------- إعداد مجلد رفع الصور ----------------
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = (".jpg", ".jpeg", ".png")


# ---------------- دالة التحقق من صلاحية الصورة ----------------
def validate_image(file: UploadFile):
    """يتأكد أن الملف صورة صالحة (jpg أو png)."""
    if not file.filename.lower().endswith(ALLOWED_EXTENSIONS):
        raise HTTPException(status_code=400, detail="الملف يجب أن يكون JPG أو PNG فقط")
    try:
        img = Image.open(file.file)
        img.verify()
        file.file.seek(0)
    except Exception:
        raise HTTPException(status_code=400, detail="الملف ليس صورة صالحة")


# ---------------- دالة حفظ الصورة محليًا ----------------
async def save_image(file: UploadFile) -> str:
    """يحفظ الصورة داخل مجلد uploads ويعيد اسم الملف."""
    filename = f"{uuid.uuid4().hex}_{file.filename}"
    file_path = UPLOAD_DIR / filename
    async with aiofiles.open(file_path, "wb") as out_file:
        content = await file.read()
        await out_file.write(content)
    return filename


# ---------------- دالة تسجيل الصورة في قاعدة البيانات ----------------
def register_image(db, user_id: int, filename: str) -> Images:
    """يسجل الصورة في قاعدة البيانات ويرجع كائن الصورة."""
    new_image = Images(
        filename=filename,
        url=f"/uploads/{filename}",
        user_id=user_id
    )
    db.add(new_image)
    db.commit()
    db.refresh(new_image)
    return new_image


# ---------------- دالة جلب آخر صورة للمستخدم ----------------
def get_last_user_image(db, user_id: int):
    """ترجع آخر صورة رفعها المستخدم (إن وجدت)."""
    last_image = (
        db.query(Images)
        .filter(Images.user_id == user_id)
        .order_by(Images.id.desc())
        .first()
    )
    if not last_image:
        return None
    return last_image
