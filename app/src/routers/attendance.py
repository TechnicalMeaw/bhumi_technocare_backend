from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from .. import schemas, models, oauth2
from ..database import get_db
from sqlalchemy.orm import Session, joinedload
from datetime import datetime
from typing import Optional
from app.src.firebase import storage as blob
from sqlalchemy.sql import func
import math
from app.src.firebase import storage as blob


router = APIRouter(prefix= "/attendance",
                   tags=["Attendance"])


@router.post("/clock_in", status_code=status.HTTP_201_CREATED, response_model=schemas.CommonResponseModel)
async def clock_in(photo : UploadFile = File(),
                        db: Session = Depends(get_db), 
                        current_user : models.User = Depends(oauth2.get_current_user)
                        ):
    now = datetime.now()
    existing_attendance = db.query(models.Attendance).filter(models.Attendance.user_id == current_user.id, models.Attendance.created_at > datetime(year=now.year, month=now.month, day=now.day, hour=0, minute=0, second=0)).order_by(models.Attendance.created_at.desc()).first()

    if existing_attendance and existing_attendance.is_clock_in == True:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User is already clocked in")
    
    new_attendance = models.Attendance(user_id = current_user.id, is_clock_in = True)
    
    try:
        res = await blob.upload_file(photo)
        new_attendance.photo = res['firebase_url']
    except Exception:
        raise HTTPException(status_code=status.HTTP_424_FAILED_DEPENDENCY, detail="Something went wrong, please try again after some time")

    db.add(new_attendance)
    db.commit()
    
    return {"status": "success", "statusCode": 201, "message" : "Successfully clocked in"}


@router.post("/clock_out", status_code=status.HTTP_201_CREATED, response_model=schemas.CommonResponseModel)
async def clock_out(photo : UploadFile = File(),
                        db: Session = Depends(get_db), 
                        current_user : models.User = Depends(oauth2.get_current_user)
                        ):
    now = datetime.now()
    existing_attendance = db.query(models.Attendance).filter(models.Attendance.user_id == current_user.id, models.Attendance.created_at > datetime(year=now.year, month=now.month, day=now.day, hour=0, minute=0, second=0)).order_by(models.Attendance.created_at.desc()).first()

    if not existing_attendance or (existing_attendance and existing_attendance.is_clock_in == False):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User is already clocked out")
    
    new_attendance = models.Attendance(user_id = current_user.id, is_clock_in = False)
    
    try:
        res = await blob.upload_file(photo)
        new_attendance.photo = res['firebase_url']
    except Exception:
        raise HTTPException(status_code=status.HTTP_424_FAILED_DEPENDENCY, detail="Something went wrong, please try again after some time")

    db.add(new_attendance)
    db.commit()
    
    return {"status": "success", "statusCode": 201, "message" : "Successfully clocked out"}



@router.get("/approve", response_model=schemas.CommonResponseModel)
async def approve(attendance_id : int,
                        db: Session = Depends(get_db), 
                        current_user : models.User = Depends(oauth2.get_current_user)
                        ):

    attendance = db.query(models.Attendance).filter(models.Attendance.id == attendance_id).first()

    if not attendance:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid attendance id")
    
    attendance.is_approved = True
    db.commit()
    
    return {"status": "success", "statusCode": 200, "message" : "Successfully approved"}


@router.get("/get_all", response_model= schemas.AllAttendanceResponseModel)
async def get_all(is_approved: Optional[bool] = None, date : Optional[datetime] = None, page : Optional[int] = 1, limit : Optional[int] = 10, search : Optional[str] = "", db: Session = Depends(get_db), 
                        current_user : models.User = Depends(oauth2.get_current_user)):
    query = (
        db.query(models.Attendance)
        .join(models.User, models.Attendance.user)
        .filter(models.User.name.ilike(f'%{search}%'))
        .order_by(models.Attendance.created_at.desc())
        .options(joinedload(models.Attendance.user))  # Eager load the user relationship
    )
    if current_user.role != 2:
        query = query.filter(models.Attendance.user_id == current_user.id)

    if is_approved is True:
        query = query.filter(models.Attendance.is_approved == True)
    elif is_approved is False:
        query = query.filter(models.Attendance.is_approved == False)

    if date:
        query = query.filter(func.date(models.Attendance.created_at) == date.date())

    total_attendance = query.count()

    offset = (page - 1) * limit
    query.limit(offset)

    total_page = math.ceil(total_attendance/(limit if limit and limit > 0 else 10))

    return {"status": "success", "statusCode": 200, "message" : "Successfully got attendance details", 
            "total_count": total_attendance,
            "current_page": page,
            "total_page": total_page,
            "prev_page": page-1 if page and page > 1 else None, 
            "next_page": page+1 if page and page < total_page else None,
            "data": query.all()}


    

    