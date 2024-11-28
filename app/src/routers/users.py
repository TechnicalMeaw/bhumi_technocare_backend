from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, status, Form, UploadFile, File, Request
from .. import schemas, utils, models, oauth2
from ..database import get_db
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Annotated, List, Optional
from ..config import settings
from app.src.firebase import storage as blob

router = APIRouter(prefix= "/users",
                   tags=["User Management"])


@router.post("/create_user", status_code=status.HTTP_201_CREATED, response_model=schemas.CommonResponseModel)
async def create_user(name : Annotated[str, Form()],
                        address : Annotated[str, Form()],
                        phone_no : Annotated[str, Form()],
                        dob : Annotated[str, Form()],
                        blood_group : Annotated[str, Form()],
                        depertment : Annotated[str, Form()],
                        post : Annotated[str, Form()],
                        remarks : Optional[str] = Form(None),
                        password : Optional[str] = Form(None),
                        family_contact_no : Optional[str] = Form(None),
                        photo : Optional[UploadFile] = File(None),
                        resume : Optional[UploadFile] = File(None),

                        db: Session = Depends(get_db), 
                        current_user : models.User = Depends(oauth2.get_current_user)
                        ):
    
    if current_user.role != 2:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admin can create account")

    if not utils.is_phone_number(phone_no):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail= "Invalid phone number")
    
    country_code, phone_no = utils.split_phone_number(phone_no)

    existing_user = db.query(models.User).filter(models.User.country_code == country_code, models.User.phone_no == phone_no).first()
    
    if existing_user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail= "User already exists")

    if not password or password == "":
        password = "Bhumi@123"
    
    new_user = models.User(name = name, 
                            address = address,
                            country_code = country_code,
                            phone_no = phone_no,
                            dob = dob,
                            blood_group = blood_group,
                            depertment = depertment,
                            post = post,
                            remarks = remarks,
                            password = utils.hash(password),
                            family_contact_no = family_contact_no)
    
    if photo:
        res = await blob.upload_file(photo)
        new_user.photo = res['firebase_url']
    
    if resume:
        res = await blob.upload_file(resume)
        new_user.resume = res['firebase_url']
        

    db.add(new_user)
    db.commit()

    return {"status": "success", "statusCode": 201, "message" : "Account Created"}
    


