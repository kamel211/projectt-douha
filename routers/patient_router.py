from fastapi import APIRouter, Depends, Header, Request
from Controller.patient_controller import (
    CreateUserRequest,
    LoginUserRequest,
    ChangePasswordRequest,
    UpdatePatientRequest,
    register_user,
    login_user,
    logout_user,
    change_password,
    update_patient_profile,
    get_current_patient
)

router = APIRouter(prefix="/patients", tags=["Patients Auth"])

# تسجيل مريض جديد
@router.post("/register")
def register(request: CreateUserRequest):
    return register_user(request)


@router.post("/login")
async def login(request: LoginUserRequest, req: Request):
    return await login_user(request, req)

# تسجيل الخروج للمريض
@router.post("/logout")
def logout(Authorization: str = Header(...)):
    token = Authorization.split(" ")[1]
    return logout_user(token)

# تغيير كلمة المرور
@router.put("/change-password")
def change_patient_password(
    request_data: ChangePasswordRequest,
    current_user: dict = Depends(get_current_patient)
):
    return change_password(request_data, current_user)

# بيانات المستخدم الحالي
@router.get("/me")
def get_current_patient_info(current_user: dict = Depends(get_current_patient)):
    return {
        "id": str(current_user["_id"]),
        "username": current_user["username"],
        "email": current_user["email"],
        "first_name": current_user["first_name"],
        "last_name": current_user["last_name"],
        "phone_number": current_user.get("phone_number", ""),
        "role": current_user["role"],
        "full_name": f"{current_user['first_name']} {current_user['last_name']}"
    }

# تحديث بيانات المريض]
#######################kamel
@router.put("/profile")
def update_patient_profile_endpoint(
    update_data: UpdatePatientRequest,
    current_user: dict = Depends(get_current_patient)
):
    return update_patient_profile(update_data, current_user)

