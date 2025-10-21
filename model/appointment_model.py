from sqlalchemy import Column, Integer, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship
from database import Base
from model.patient_model import Users
from model.doctor_model import Doctors

class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("patient.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    date_time = Column(DateTime, nullable=False)

    status = Column(String, default="Scheduled", nullable=False)

    patient = relationship("Users", back_populates="appointments")

    doctor = relationship("Doctors", back_populates="appointments")
