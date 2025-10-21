from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from Controller.patient_controller import get_current_patient
from Controller.images_controller import upload_to_local, get_user_images

router = APIRouter(prefix="/images", tags=["Images"])

# ---------------- رفع ملف واحد ----------------
@router.post("/upload_file/")
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user = Depends(get_current_patient)
):
    return upload_to_local(file, user.id, db)

# ---------------- رفع عدة ملفات ----------------
@router.post("/upload_files/")
async def upload_files(
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
    user = Depends(get_current_patient)
):
    urls = []
    for file in files:
        try:
            urls.append(upload_to_local(file, user.id, db))
        except HTTPException as e:
            urls.append({"filename": file.filename, "error": e.detail})
    return {"files": urls}

# ---------------- استرجاع كل صور المستخدم ----------------
@router.get("/me")
def get_my_images(
    db: Session = Depends(get_db),
    user = Depends(get_current_patient)
):
    return get_user_images(db, user.id)
