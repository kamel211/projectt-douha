from pydantic import BaseModel
from datetime import datetime

class AppointmentRequest(BaseModel):
    doctor_id: str
    date_time: datetime
    reason: str
