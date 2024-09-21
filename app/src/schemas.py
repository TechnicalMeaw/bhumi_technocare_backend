from pydantic import BaseModel, Field
from typing import Optional, List, Annotated, Tuple
from fastapi import UploadFile, File, Form
from datetime import datetime
from sqlalchemy.orm import Session


# For token verification
class TokenData(BaseModel):
    id : Optional[str] = None

# Token response model
class Token(BaseModel):
    token : str
    existing_user : bool

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