
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
from model.patient_model import Users

class Images(Base):
    __tablename__ = "images"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    url = Column(String)
    user_id = Column(Integer, ForeignKey("patient.id"))  # تم تصحيح اسم الجدول هنا
    user = relationship("Users", back_populates="images")