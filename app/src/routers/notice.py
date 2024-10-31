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


router = APIRouter(prefix= "/notice",
                   tags=["Notice Board"])


@router.post("/create", status_code=status.HTTP_201_CREATED, response_model=schemas.CommonResponseModel)
async def create( body : schemas.CreateNoticeRequestModel,
                        db: Session = Depends(get_db), 
                        current_user : models.User = Depends(oauth2.get_current_user)
                        ):
    
    if current_user.role != 2:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admin can create notice")
    
    new_notice = models.NoticeBoard(notice = body.notice, created_by = current_user.id)
    db.add(new_notice)
    db.commit()
    
    return {"status": "success", "statusCode": 201, "message" : "Notice Added"}

@router.delete("/remove", status_code=status.HTTP_201_CREATED, response_model=schemas.CommonResponseModel)
async def create( notice_id : int,
                        db: Session = Depends(get_db), 
                        current_user : models.User = Depends(oauth2.get_current_user)
                        ):
    
    if current_user.role != 2:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admin can remove notice")
    
    notice = db.query(models.NoticeBoard).filter(models.NoticeBoard.id == notice_id, models.NoticeBoard.is_active == True).first()
    if not notice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid notice id")
    notice.is_active = False
    db.commit()
    
    return {"status": "success", "statusCode": 201, "message" : "Notice Added"}



@router.get("/product_types", response_model = schemas.AllNoticeResponseModel)
async def get_product_types(is_active : Optional[bool] = None, page : Optional[int] = None, limit : Optional[int] = None, search : Optional[str] = "", db: Session = Depends(get_db), 
                    current_user : models.User = Depends(oauth2.get_current_user)):
    
    query = db.query(models.NoticeBoard).filter(cast(models.NoticeBoard.notice, String).ilike(f'%{search}%')).order_by(models.NoticeBoard.created_at.desc())
    if is_active is not None:
        query = query.filter(models.NoticeBoard.is_active == is_active)

    total_notices = query.count()

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

        total_page = math.ceil(total_notices/(limit if limit and limit > 0 else 10))

    return {"status": "success", "statusCode": 200, "message" : "Successfully got notices", 
            "total_count": total_notices,
            "current_page": page,
            "total_page": total_page,
            "prev_page": page-1 if page and page > 1 else None, 
            "next_page": page+1 if page and page < total_page else None,
            "data": query.all()}

