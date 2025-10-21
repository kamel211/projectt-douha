# from fastapi import FastAPI
# from database import engine, Base
# from routers import patient_router, dector_router, appointment_router, images

# # إنشاء جميع الجداول
# Base.metadata.create_all(bind=engine)

# app = FastAPI(title="Hospital Management System",
#     description="API for Hospital Management System",
#     version="1.0.0")

# # تضمين الرواتر
# app.include_router(patient_router.router)
# app.include_router(dector_router.router)
# app.include_router(appointment_router.router)
# app.include_router(images.router)

# @app.get("/")
# def root():
#     return {"message": "API is running"}
