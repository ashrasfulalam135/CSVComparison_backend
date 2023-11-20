from sqlalchemy import JSON, Column, Integer, String, Text
from sqlalchemy.sql.sqltypes import Integer
from db.database import Base

class UserCsvs(Base):
    __tablename__ = "usercsvs"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String(length=255))
    folder_path = Column(String(length=255))
    source_file_name = Column(Text)
    compared_file_name = Column(Text)