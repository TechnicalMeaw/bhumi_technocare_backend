from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy import func, case, and_
from .. import schemas, models, oauth2
from ..database import get_db
from sqlalchemy.orm import Session, joinedload, aliased
from datetime import datetime, timedelta
from typing import Optional
from app.src.firebase import storage as blob
from sqlalchemy.sql import func
import math


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
    existing_attendance = db.query(models.Attendance).filter(models.Attendance.user_id == current_user.id, models.Attendance.created_at >= now.date()).order_by(models.Attendance.created_at.desc()).first()

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
    
    if current_user.role != 2:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admin can approve attendance")

    attendance = db.query(models.Attendance).filter(models.Attendance.id == attendance_id).first()

    if not attendance:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid attendance id")
    
    attendance.is_approved = True
    db.commit()
    
    return {"status": "success", "statusCode": 200, "message" : "Successfully approved"}


@router.get("/get_all", response_model= schemas.AllAttendanceResponseModel)
async def get_all(is_approved: Optional[bool] = None, day_count : Optional[int] = 7, page : Optional[int] = 1, limit : Optional[int] = 10, search : Optional[str] = "", db: Session = Depends(get_db), 
                        current_user : models.User = Depends(oauth2.get_current_user)):
    query = (
        db.query(models.Attendance)
        .join(models.User, models.Attendance.user)
        .filter(models.Attendance.created_at > (datetime.now() - timedelta(days=day_count)).date(), models.User.name.ilike(f'%{search}%'))
        .order_by(models.Attendance.created_at.desc())
        .options(joinedload(models.Attendance.user))  # Eager load the user relationship
    )
    if current_user.role != 2:
        query = query.filter(models.Attendance.user_id == current_user.id)

    if is_approved is True:
        query = query.filter(models.Attendance.is_approved == True)
    elif is_approved is False:
        query = query.filter(models.Attendance.is_approved == False)

    total_attendance = query.count()

    offset = (page - 1) * limit
    query.offset(offset).limit(limit)

    total_page = math.ceil(total_attendance/(limit if limit and limit > 0 else 10))

    return {"status": "success", "statusCode": 200, "message" : "Successfully got attendance details", 
            "total_count": total_attendance,
            "current_page": page,
            "total_page": total_page,
            "prev_page": page-1 if page and page > 1 else None, 
            "next_page": page+1 if page and page < total_page else None,
            "data": query.all()}


    
@router.get('/status', response_model=schemas.AttendanceStatusResponseModel)
async def get_status(db: Session = Depends(get_db), 
                        current_user : models.User = Depends(oauth2.get_current_user)):
    
    existing_attendance = db.query(models.Attendance).filter(models.Attendance.user_id == current_user.id, models.Attendance.created_at >= datetime.now().date()).order_by(models.Attendance.created_at.desc()).first()

    if not existing_attendance:
        return {"status": "success", "statusCode": 200, "message" : "Successfully got attendance status", 
                "is_clocked_in" : False, "attendance_status" : -1, "last_recorded" : None}
    
    return {"status": "success", "statusCode": 200, "message" : "Successfully got attendance status", 
                "is_clocked_in" : existing_attendance.is_clock_in, 
                "attendance_status" : 1 if existing_attendance.is_clock_in else 0, "last_recorded" : existing_attendance.created_at}


@router.get("/leaderboard")
async def get_leaderboard(
    day_count: int = 7,
    search: str = "",
    page: int = 1,
    limit: int = 10,
    db: Session = Depends(get_db),
):
    # Calculate the date range for filtering attendance records
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=day_count)

    # Alias for Attendance table to calculate service time
    prev_entry = aliased(models.Attendance)

    # Query to calculate the service time between clock-in and clock-out
    service_time_query = (
        db.query(
            models.Attendance.user_id,
            func.sum(
                case(
                    (and_(
                        models.Attendance.is_clock_in == True,
                        prev_entry.is_clock_in == False,
                        prev_entry.created_at < models.Attendance.created_at,
                        models.Attendance.created_at <= end_date,
                        prev_entry.created_at >= start_date,
                    ),
                    func.least(
                        func.extract("epoch", models.Attendance.created_at - prev_entry.created_at),
                        8 * 3600,  # Maximum service time of 8 hours per session
                    )),
                    else_=0,
                )
            ).label("service_time"),
        )
        .join(
            prev_entry,
            and_(
                models.Attendance.user_id == prev_entry.user_id,
                models.Attendance.created_at > prev_entry.created_at,
            ),
        )
        .filter(models.Attendance.created_at.between(start_date, end_date))
        .group_by(models.Attendance.user_id)
        .subquery()
    )



    # Join the service time query with the User table
    query = (
        db.query(
            models.User,
            service_time_query.c.service_time.label("total_service_time"),
        )
        .join(service_time_query, models.User.id == service_time_query.c.user_id)
        .filter(models.User.is_active == True)
    )

    

    # Apply search filter for name
    if search:
        query = query.filter(models.User.name.ilike(f"%{search}%"))

    # Count total entries for pagination
    total_entries = query.count()

    # Apply pagination
    offset = (page - 1) * limit
    users_with_service_time = query.offset(offset).limit(limit).all()

    # Calculate total pages
    total_pages = math.ceil(total_entries / limit)

    # Construct the response
    response = {
        "status": "success",
        "statusCode": 200,
        "message": "Successfully fetched leaderboard",
        "total_count": total_entries,
        "current_page": page,
        "total_page": total_pages,
        "prev_page": page - 1 if page > 1 else None,
        "next_page": page + 1 if page < total_pages else None,
        "data": [
            {
                "user": {
                    "id": user.id,
                    "name": user.name,
                    "address": user.address,
                    "photo": user.photo,
                    "depertment": user.depertment,
                    "post": user.post,
                },
                "total_service_time": service_time,
            }
            for user, service_time in users_with_service_time
        ],
    }

    return response
