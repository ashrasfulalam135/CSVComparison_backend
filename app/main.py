from fastapi import FastAPI, File, Form, UploadFile, HTTPException, Response, status, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import Field
import models.models as models
from db.database import engine, SessionLocal
# from schemas.schemas import UserCsv
from sqlalchemy.orm import Session
import os
import uuid
import pandas as pd

app = FastAPI()

models.Base.metadata.create_all(bind=engine)

# Configure CORS
origins = [
    os.getenv("ALLOWED_URL"),  # Add your frontend URL here
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],  # You can restrict this to specific HTTP methods if needed
    allow_headers=["*"],  # You can restrict this to specific headers if needed
)

def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()
        
def error_handle(sourceFileName, comparedFileName):
    # check file submitted or not
    if not sourceFileName and not comparedFileName:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, 
                            detail={"source_file_error" : "Source file required",
                                    "compared_file_error" : "Compared file required"})
    if not sourceFileName:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, 
                            detail={"source_file_error" : "Source file required"})
    if not comparedFileName:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, 
                            detail={"compared_file_error" : "Compared file required"})
        
    # check file extension
    _, source_file_extension = os.path.splitext(sourceFileName)
    _, compared_file_extension = os.path.splitext(sourceFileName)
    if source_file_extension[1:] != 'csv' and compared_file_extension[1:] != 'csv':
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                            detail={"source_file_error" : "Source file should be csv formate",
                                    "compared_file_error" : "Compared file should be csv formate"})
    if source_file_extension[1:] != 'csv':
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                            detail={"source_file_error" : "Source file should be csv formate"})
    if compared_file_extension[1:] != 'csv':
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                            detail={"compared_file_error" : "Compared file should be csv formate"})
        
def sorting_data(uploadfolderpath, sourceFileName, comparedFileName):
    source_df = pd.read_csv(os.path.join(uploadfolderpath, sourceFileName))
    sorted_source_df = source_df.apply(lambda x: x.sort_values().reset_index(drop=True))
    sorted_source_file_path = os.path.join(uploadfolderpath, f"shorted_{sourceFileName}")
    sorted_source_df.to_csv(sorted_source_file_path, index=False)
    
    compared_df = pd.read_csv(os.path.join(uploadfolderpath, comparedFileName))
    sorted_compared_df = compared_df.apply(lambda x: x.sort_values().reset_index(drop=True))
    sorted_compared_file_path = os.path.join(uploadfolderpath, f"shorted_{comparedFileName}")
    sorted_compared_df.to_csv(sorted_compared_file_path, index=False)
    
    return sorted_source_file_path, sorted_compared_file_path

def difference_data(uploadfolderpath, sourceFileName, comparedFileName):
    sorted_source_df = pd.read_csv(sourceFileName)
    sorted_compared_df = pd.read_csv(comparedFileName)
    
    difference_df = pd.merge(sorted_source_df,sorted_compared_df, how='outer', indicator=True).loc[lambda x:x['_merge'] == 'left_only'].drop(columns=['_merge'])
    difference_file_path = os.path.join(uploadfolderpath, "difference.csv")
    difference_df.to_csv(difference_file_path, index=False)
    
    return difference_file_path
    

@app.post("/upload")
async def create_user_csv(
    sort: bool = Form(default=False),
    compare: bool = Form(default=False),
    sourceFile: UploadFile = File(...),
    comparedFile: UploadFile = File(...),
    # use_csv: UserCsv,
    db: Session = Depends(get_db)
):
    #check required file and extension
    error_handle(sourceFile.filename, comparedFile.filename)
    
    # Generate a unique user_id using uuid
    user_id = str(uuid.uuid4())
    
    # Create user folder if not exists
    folder_path = f"./uploads/{user_id}"
    os.makedirs(folder_path, exist_ok=True)
    
    source_file_name = sourceFile.filename
    source_file_path = os.path.join(folder_path, source_file_name)
    compared_file_name = comparedFile.filename
    compared_file_path = os.path.join(folder_path, compared_file_name)

    # Save file
    with open(source_file_path, "wb") as f:
        f.write(sourceFile.file.read())
    with open(compared_file_path, "wb") as f:
        f.write(comparedFile.file.read())
    
    user_csv_model = models.UserCsvs()
    user_csv_model.user_id = user_id
    user_csv_model.folder_path = folder_path
    user_csv_model.source_file_name = source_file_name
    user_csv_model.compared_file_name = compared_file_name

    db.add(user_csv_model)
    db.commit()
    
    #sorting data
    sorted_source_file_path = None
    sorted_compared_file_path = None
    if sort:
        sorted_source_file_path, sorted_compared_file_path = sorting_data(folder_path, source_file_name, compared_file_name)
    
    #compare data
    difference_of_source_and_compared_csv_path = None
    if compare:
        difference_of_source_and_compared_csv_path = difference_data(folder_path, source_file_path, compared_file_path)
        
    
    data = {
        "user_id": user_id,
        "folder_path": folder_path,
        "source_file_name": source_file_name,
        "compared_file_name": compared_file_name,
        "sorted_source_file_path": sorted_source_file_path,
        "sorted_compared_file_path": sorted_compared_file_path,
        "difference_of_source_and_compared_csv_path": difference_of_source_and_compared_csv_path,
    }
    
    return JSONResponse(content=data)