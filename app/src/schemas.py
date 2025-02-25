from pydantic import BaseModel, Field
from typing import Optional, List, Annotated, Tuple
from fastapi import UploadFile, File, Form
from datetime import datetime
from sqlalchemy.orm import Session
from uuid import UUID
from ..src import models


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
    role : str

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

# Organization
class OrganizationModel(BaseModel):
    id : int
    name : str
    address : str
    contact_no : str | None
    area_rel : AreaResponseModel | None
    city_rel : AreaResponseModel | None
    contact_person : str | None
    pincode : str | None
    gst_no : str | None
    photo : str | None
    remarks : str | None
    class Config:
        from_attributes = True

# Customer
class CustomerModel(BaseModel):
    id : int
    name : str
    address : str
    contact_no : str
    firm_id : int | None
    area_rel : AreaResponseModel | None
    city_rel : AreaResponseModel | None
    depertment : str | None
    photo : str | None
    remarks : str | None
    class Config:
        from_attributes = True

class BillModel(BaseModel):
    id : int
    amount : int
    bill_number : str
    bill_type : models.BillType
    remarks : str | None
    photo : str | None
    asset_photo : str | None
    gst_bill_number :  str | None
    is_handed : bool
    created_at : datetime
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
    is_started : bool
    organization : OrganizationModel | None
    customer : CustomerModel
    product_type : AreaResponseModel
    engineer : EngineerModel
    service_type : AreaResponseModel

    bill : BillModel | None

    class Config:
        from_attributes = True

class ServiceResponseModel(CommonResponseModel, PaginationResponseModel):
    data : List[ServiceModel]


class UpdateServiceResponseModel(CommonResponseModel):
    data : ServiceModel


class BillResponseModel(BillModel):
    organization : OrganizationModel | None
    customer : CustomerModel
    engineer : EngineerModel
    class Config:
        from_attributes = True

class AllBillResponseModel(CommonResponseModel, PaginationResponseModel):
    data : List[BillResponseModel]


class AttendanceStatusResponseModel(CommonResponseModel):
    is_clocked_in : bool
    attendance_status : int
    last_recorded : datetime | None
    class Config:
        from_attributes = True

class ExpenceResponseModel(BaseModel):
    id : int
    amount : int
    expence_type : models.ExpenceType
    photo : str | None
    details : str
    is_approved : bool
    is_declined : bool
    organization : OrganizationModel | None
    customer : CustomerModel
    engineer : EngineerModel
    created_at : datetime
    remarks : str | None
    class Config:
        from_attributes = True

class AllExpenceResponseModel(CommonResponseModel, PaginationResponseModel):
    data : List[ExpenceResponseModel]

class EngineerAttendanceHoursResponse(BaseModel):
    user : UserQuickDetailResponseModel
    service_time_in_seconds : int

class AllEngineerAttendanceHoursResponseModel(BaseModel):
    data: List[EngineerAttendanceHoursResponse]


# Organization full model
class AllOrganizationDataResponseModel(CommonResponseModel, PaginationResponseModel):
    data : List[OrganizationModel]

# Customer full model
class AllCustomerDataResponseModel(CommonResponseModel, PaginationResponseModel):
    data : List[CustomerModel]