from pydantic import BaseModel, Field
from typing import Optional, List, Annotated, Tuple
from fastapi import UploadFile, File, Form
from datetime import datetime
from sqlalchemy.orm import Session


# Common Response Model
class CommonResponseModel(BaseModel):
    status : str
    statusCode: int
    message: str

# Common Pagination Response Model
class PaginationResponseModel(BaseModel):
    total_count: int
    current_page : int
    total_page : int
    prev_page : int | None
    next_page: int | None

# User Response
class UserQuickDetailResponseModel(BaseModel):
    name : str
    photo : str

# For token verification
class TokenData(BaseModel):
    id : Optional[str] = None

# Token response model
class Token(BaseModel):
    token : str
    existing_user : bool
    user : UserQuickDetailResponseModel

# Create User 
# Request Model
class CreateUserRequestModel(BaseModel):
    name : str
    address : str
    photo : Optional[UploadFile]
    country_code : str
    phone_no : str
    family_contact_no : Optional[str]
    resume : Optional[UploadFile]
    dob : str
    blood_group : str
    depertment : str
    post : str
    remarks : Optional[str]
    password : Optional[str]

class EngineerModel(BaseModel):
    id : int
    name : str
    address : str
    photo : str
    country_code : str
    phone_no : str
    family_contact_no : str
    resume : str
    dob : str
    blood_group : str
    depertment : str
    post : str
    remarks : str
    created_at : datetime

class AllEngineerResponseModel(CommonResponseModel, PaginationResponseModel):
    data : List[EngineerModel]

class EngineerResponseModel(CommonResponseModel):
    data: EngineerModel