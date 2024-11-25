from pydantic import BaseModel, Field
from typing import Optional, List, Annotated, Tuple
from fastapi import UploadFile, File, Form
from datetime import datetime
from sqlalchemy.orm import Session
from uuid import UUID


# Common Response Model
class CommonResponseModel(BaseModel):
    status : str
    statusCode: int
    message: str

# Common Pagination Response Model
class PaginationResponseModel(BaseModel):
    total_count: int
    current_page : int | None
    total_page : int
    prev_page : int | None
    next_page: int | None

# User Response
class UserQuickDetailResponseModel(BaseModel):
    name : str
    photo : str | None

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

# Reset Password
# Request Model
class ResetPasswordRequestModel(BaseModel):
    old_password: str
    new_password: str

class EngineerModel(BaseModel):
    id : int
    name : str
    address : str
    photo : str | None
    country_code : str
    phone_no : str
    family_contact_no : str
    resume : str | None
    dob : str
    blood_group : str
    depertment : str
    post : str
    remarks : str | None
    created_at : datetime

class AllEngineerResponseModel(CommonResponseModel, PaginationResponseModel):
    data : List[EngineerModel]

class EngineerResponseModel(CommonResponseModel):
    data: EngineerModel


# Area
# Request Model
class CreateAreaRequestModel(BaseModel):
    name : str

# Response Model
class AreaResponseModel(BaseModel):
    id : int
    name : str

class AllAreaResponseModel(CommonResponseModel, PaginationResponseModel):
    data : List[AreaResponseModel]

# City
# Request Model
class CreateCityRequestModel(BaseModel):
    name: str
    area_id : int

# Notice
# Create
class CreateNoticeRequestModel(BaseModel):
    notice : str
    
# Response Model
class NoticeResModel(BaseModel):
    id : UUID
    notice : str
    created_at : datetime
    is_active : bool

class AllNoticeResponseModel(CommonResponseModel, PaginationResponseModel):
    data : List[NoticeResModel]

# Attendance
class AttendanceModel(BaseModel):
    id : int
    photo : str
    is_clock_in : bool
    is_approved : bool
    created_at : datetime
    user : UserQuickDetailResponseModel


class AllAttendanceResponseModel(CommonResponseModel, PaginationResponseModel):
    data : List[AttendanceModel]



# Service
# Response Model

class BillModel(BaseModel):
    id : int
    amount : int
    bill_number : str
    remarks : str | None
    photo : str | None
    is_handed : bool
    class Config:
        from_attributes = True

class ServiceModel(BaseModel):
    id : int
    due_date : datetime
    # asset_id
    remarks : str | None
    photo : str | None
    created_at : datetime
    is_resolved : bool

    organization : AreaResponseModel | None
    customer : AreaResponseModel
    product_type : AreaResponseModel
    engineer : AreaResponseModel
    service_type : AreaResponseModel

    bill : BillModel

    class Config:
        from_attributes = True

class ServiceResponseModel(CommonResponseModel, PaginationResponseModel):
    data : List[ServiceModel]