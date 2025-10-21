from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
from appointment_model import Appointment

class Doctors(Base):
    __tablename__ = "doctors"  
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    specialty = Column(String)
    email = Column(String, unique=True, nullable=False)
    phone = Column(String)
    hashed_password = Column(String, nullable=False)  # لتسجيل الدخول

    # العلاقة مع المواعيد
    appointments = relationship("Appointment", back_populates="doctor")
