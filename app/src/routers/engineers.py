from fastapi import APIRouter, Depends, HTTPException, status, Form, UploadFile, File, Request
from .. import schemas, utils, models, oauth2
from ..database import get_db
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Annotated, List, Optional
from ..config import settings
from app.src.firebase import storage as blob
from sqlalchemy.sql.expression import cast, or_, and_
from sqlalchemy import String, select
import math
from app.src.firebase import storage as blob


router = APIRouter(prefix= "/engineers",
                   tags=["Engineer Management"])


@router.get("/", response_model = schemas.AllEngineerResponseModel)
async def get_engineers_list(is_active : Optional[bool] = None, page : Optional[int] = None, limit : Optional[int] = None, search : Optional[str] = "", db: Session = Depends(get_db), 
                    current_user : models.User = Depends(oauth2.get_current_user)):
    
    query = db.query(models.User).filter(models.User.role == 1).filter(or_(cast(models.User.name, String).ilike(f'%{search}%'), 
                                                cast(models.User.phone_no, String).ilike(f'%{search}%'))).order_by(models.User.created_at.desc())
    
    if is_active is not None:
        query = query.filter(models.User.is_active == is_active)

    total_users = query.count()

    # By default the limit is `None`
    # If limit is positive -> set the limit
    if limit and limit > 0:
        query.limit(limit)

    # By default pagination is not implemented
    # So the total page count will be -> `1``
    total_page = 1

    # If page number is provided and is positive
    # Means pagination is requested ---->
    # If limit is not provided, then set it to -> `10`
    # Else take the provided limit ----> Calculate the total page accordingly
    if page and page > 0:
        offset = (page - 1) * (limit if limit and limit > 0 else 10)
        query.limit(offset)

        total_page = math.ceil(total_users/(limit if limit and limit > 0 else 10))

    return {"status": "success", "statusCode": 200, "message" : "Successfully got users", 
            "total_count": total_users,
            "current_page": page,
            "total_page": total_page,
            "prev_page": page-1 if page and page > 1 else None, 
            "next_page": page+1 if page and page < total_page else None,
            "data": query.all()}



# @router.get("/", response_model=schemas.AllEngineerResponseModel)
# async def get_engineers_list(page : int = 1, search : Optional[str] = "", 
#                              db: Session = Depends(get_db), current_user : models.User = Depends(oauth2.get_current_user)):
    
#     search_query = db.query(models.User).filter(models.User.role == 1, models.User.is_active == True).filter(or_(cast(models.User.name, String).ilike(f'%{search}%'), 
#                                                 cast(models.User.phone_no, String).ilike(f'%{search}%'))).order_by(models.User.created_at.desc())
#     search_results = search_query.limit(10).offset((page-1)*10).all()

#     total_users = search_query.count()
#     total_page = math.ceil(total_users/10)
#     return {"status": "success", "statusCode": 200, "message" : "Successfully got users", 
#             "total_count": total_users,
#             "current_page": page,
#             "total_page": total_page,
#             "prev_page": page-1 if page > 1 else None, 
#             "next_page": page+1 if page < total_page else None,
#             "data": search_results}


@router.put("/", response_model= schemas.EngineerResponseModel)
async def update_engineer_details(user_id : Annotated[int, Form()],
                        name : Optional[str] = Form(None),
                        address : Optional[str] = Form(None),
                        phone_no : Optional[str] = Form(None),
                        dob : Optional[str] = Form(None),
                        blood_group : Optional[str] = Form(None),
                        depertment : Optional[str] = Form(None),
                        post : Optional[str] = Form(None),
                        remarks : Optional[str] = Form(None),
                        family_contact_no : Optional[str] = Form(None),
                        photo : Optional[UploadFile] = File(None),
                        resume : Optional[UploadFile] = File(None),

                        db: Session = Depends(get_db), 
                        current_user : models.User = Depends(oauth2.get_current_user)):
    
    if current_user.id != user_id and current_user.role != 2:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You don't have the permission to perform this action")
    
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    if name and name.strip() != "":
        user.name = name
    if address and address.strip() != "":
        user.address = address
    if phone_no and phone_no.strip() != "":
        user.phone_no = phone_no
    if dob and dob.strip() != "":
        user.dob = dob
    if blood_group and blood_group.strip != "":
        user.blood_group = blood_group
    if depertment and depertment.split() != "":
        user.depertment = depertment
    if post and post.strip() != "":
        user.post = post
    
    user.remarks = remarks
    user.family_contact_no = family_contact_no

    if photo:
        if user.photo and user.photo.startswith(f"https://storage.googleapis.com/{settings.firebase_storage_bucket_name}/"):
            try:
                is_success = await blob.delete_file(user.photo)
                if is_success:
                    try:
                        res = await blob.upload_file(photo)
                        user.photo = res['firebase_url']
                    except Exception:
                        pass
            except Exception:
                pass
    
    if resume:
        if user.resume and user.resume.startswith(f"https://storage.googleapis.com/{settings.firebase_storage_bucket_name}/"):
            try:
                is_success = await blob.delete_file(user.resume)
                if is_success:
                    try:
                        res = await blob.upload_file(resume)
                        user.resume = res['firebase_url']
                    except Exception:
                        pass
            except Exception:
                pass
    db.commit()
    db.refresh(user)

    return {"status": "success", "statusCode": 200, "message" : "Successfully got users", "data" : user}

    

@router.delete("/delete", response_model= schemas.CommonResponseModel)
async def delete_engineer(user_id : int, db: Session = Depends(get_db), 
                        current_user : models.User = Depends(oauth2.get_current_user)):
    if current_user.role != 3:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail= "You don't have the authority for doing this action")
    
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    user.is_active = False
    db.commit()

    return {"status": "success", "statusCode": 200, "message" : "Successfully Deleted"}


    