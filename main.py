from fastapi import FastAPI
from database import *
from routers import patient_router 
from routers import dector_router 
from routers import appointment_router 
from routers import images
Base.metadata.create_all(bind=engine)
app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "🚀 Server is running with auto-reload!"}


# patient
app.include_router(patient_router.router)




# dector

app.include_router(dector_router.router)

# appointments
app.include_router(appointment_router.router)
app.include_router(images.router)


# uvicorn main:app --reload