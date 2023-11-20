
from fastapi import File, Form, UploadFile
from pydantic import BaseModel
   
class UserCsv(BaseModel):
    sort: bool = Form(default=False),
    compare: bool = Form(default=False),
    sourceFile: UploadFile = File(...),
    comparedFile: UploadFile = File(...),