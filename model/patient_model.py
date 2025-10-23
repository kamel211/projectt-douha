
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime



class Users(Base):
    __tablename__ = "patients"  # اسم الجدول في قاعدة البيانات
    
    # الأعمدة الأساسية
    id = Column(Integer, primary_key=True, index=True)  # مفتاح أساسي
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    
    
    role = Column(String(50), default="patient")
    phone_number = Column(String(20))  
    
    appointments = relationship("Appointment", back_populates="patient")
    images = relationship("Images", back_populates="user")
    
