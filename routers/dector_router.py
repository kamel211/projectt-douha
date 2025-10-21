from fastapi import APIRouter, Depends, Request
from Controller import doctor_controller

router = APIRouter(prefix="/doctors", tags=["Doctors Auth"])

# تسجيل دكتور
@router.post("/register")
def register(request: doctor_controller.CreateDoctorRequest):
    return doctor_controller.register_doctor(request)

# تسجيل دخول دكتور
@router.post("/login")
def login(request: doctor_controller.LoginDoctorRequest, req: Request):
    return doctor_controller.login_doctor(request, req)

# تسجيل خروج
@router.post("/logout")
def logout(token: str = Depends(doctor_controller.oauth2_scheme)):
    return doctor_controller.logout_doctor(token)

# الحصول على بيانات الدكتور الحالي
@router.get("/me")
def get_me(doctor=Depends(doctor_controller.get_current_doctor)):
    return doctor

# تحديث الملف الشخصي
@router.put("/update")
def update_profile(update_data: doctor_controller.UpdateDoctorRequest,
                   doctor=Depends(doctor_controller.get_current_doctor)):
    return doctor_controller.update_doctor_profile(update_data, doctor)
