import base64
import hashlib
import uuid
from passlib.context import CryptContext
from datetime import datetime
from sqlalchemy.orm import Session
from app.src import models
# from datetime import time
import re


pwd_context = CryptContext(schemes=["bcrypt"], deprecated = "auto")

def hash(password : str):
    return pwd_context.hash(password)

def verify(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)



def split_phone_number(phone_number):
    pattern = r'^(\+\d{1,3})(\d{10})$'
    match = re.match(pattern, phone_number)
    if match:
        country_code = match.group(1)
        number = match.group(2)
        return country_code, number
    else:
        return None, None
    
def is_email(email):
    pattern = r'^\S+@\S+\.\S+$'
    return re.match(pattern, email) is not None

def is_phone_number(phone_number):
    pattern = r'^\+?[0-9]+(?:\s*-?\s*[0-9]+)*$'
    return re.match(pattern, phone_number) is not None
