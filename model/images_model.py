from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Images(Base):
    __tablename__ = "images"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    url = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("patients.id"))  

    # العلاقة مع المستخدم
    user = relationship("Users", back_populates="images")
