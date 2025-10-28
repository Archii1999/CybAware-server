from sqlalchemy import Column, Integer, String, DateTime, func, Boolean
from app.database import Base

class User(Base):
    __tablename__ = "users"

    #uniek ID
    id = Column(Integer, primary_key=True, index=True)

    #domeinvelden
    name =Column(String(100), nullable=False) #verplicht
    email = Column(String(100), unique=True ,nullable=False, index=True) #uniek email + geindexeerd
    password = Column(String(255), nullable=False) #MOET NOG GEHASHT WORDEN
    is_active = Column(Boolean, nullable=False, server_default="1") #IEMAND ACHTIEF JA OF DER NEE

    #tijden
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self) -> str:
        return f"<User id ={self.id} email={self.email}>"