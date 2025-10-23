# model/images_model.py
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Images(Base):
    __tablename__ = "images"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    url = Column(String, nullable=False)

    # ربط بالمستخدم
    user_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    user = relationship("Users", back_populates="images")

    # ربط بالموعد (اختياري)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=True)
    appointment = relationship("Appointment", back_populates="images")
