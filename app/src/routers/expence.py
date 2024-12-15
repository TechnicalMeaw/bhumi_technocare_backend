from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from .. import schemas, models, oauth2
from ..database import get_db
from sqlalchemy.orm import Session, joinedload
from datetime import datetime, timedelta
from sqlalchemy.sql.expression import cast, or_, and_
from typing import Optional
from app.src.firebase import storage as blob
from sqlalchemy.sql import func
import math
from app.src.firebase import storage as blob


router = APIRouter(prefix= "/expense",
                   tags=["Expence"])


@router.post("/create", status_code=status.HTTP_201_CREATED, response_model=schemas.CommonResponseModel)
async def create(complaint_id : int = Form(...),
                 amount : int = Form(...),
                 expence_type : models.ExpenceType = Form(...),
                 details : str = Form(...),
                 photo : Optional[UploadFile] = File(None),
                 db: Session = Depends(get_db), 
                 current_user : models.User = Depends(oauth2.get_current_user)):
    
    complaint = db.query(models.Complaint).filter(models.Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found")
    
    if not complaint.is_started:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="The service is not started yet")
    
    if complaint.enginner_id != current_user.id and current_user.role != 2:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only assigned engineer or admin can add expences")
    
    new_expence = models.Expence(
                    firm_id = complaint.firm_id,
                    customer_id = complaint.customer_id,
                    details = details,
                    expence_type = expence_type,
                    amount = amount,
                    created_by = current_user.id
                    )
    if photo:
        try:
            res = await blob.upload_file(photo)
            new_expence.photo = res['firebase_url']
        except Exception:
            raise HTTPException(status_code=status.HTTP_424_FAILED_DEPENDENCY, detail="Something went wrong, please try again after some time")

    db.add(new_expence)
    db.commit()

    return {"status": "success", "statusCode": 201, "message" : "Successfully added expence"}


@router.get('/approve', response_model=schemas.CommonResponseModel)
async def approve(expence_id : int, is_approved : bool, db: Session = Depends(get_db), 
                 current_user : models.User = Depends(oauth2.get_current_user)):
    expence = db.query(models.Expence).filter(models.Expence.id == expence_id).first()
    if not expence:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bill not found")
    
    if current_user.role != 2:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admin can approve expences")
    
    expence.is_approved = is_approved
    expence.is_declined = not is_approved
    db.commit()

    return {"status": "success", "statusCode": 200, "message" : "Successfully approved expences"}



@router.get('/get_all', response_model=schemas.AllExpenceResponseModel)
async def get_all(is_approved : Optional[bool] = None, expence_type: Optional[models.ExpenceType] = None, day_count : Optional[int] = 30, page : Optional[int] = 1, limit : Optional[int] = 10, search : Optional[str] = "", db: Session = Depends(get_db), 
                        current_user : models.User = Depends(oauth2.get_current_user)):
    query = (
        db.query(models.Expence)
        .join(models.User, models.Expence.created_by)
        .join(models.Customer, models.Expence.customer_id)
        .filter(or_(models.User.name.ilike(f'%{search}%'),
                    models.Expence.details.ilike(f'%{search}%'),
                    models.Customer.name.ilike(f'%{search}%'),
                    models.Customer.contact_no.ilike(f'%{search}%'),
                    models.Customer.address.ilike(f'%{search}%')
                    ), 
                    models.Expence.created_at > (datetime.now() - timedelta(days=day_count)).date(),
                    )
        .order_by(models.Expence.created_at.desc())
        .options(joinedload(models.Expence.engineer), # Eager load the engineer relationship
                 joinedload(models.Expence.customer)) # Eager load the customer relationship 
    )

    # If not admin, then show only assigned expences
    if current_user.role != 2:
        query = query.filter(models.Attendance.user_id == current_user.id)

    # Filters
    # -------
    # Expence Type
    if expence_type:
        query = query.filter(models.Expence.expence_type == expence_type)

    # Approved
    if is_approved is not None:
        query = query.filter(models.Expence.is_approved == is_approved, models.Expence.is_declined != is_approved)

    total_expences = query.count()

    offset = (page - 1) * limit
    query.limit(offset)

    total_page = math.ceil(total_expences/(limit if limit and limit > 0 else 10))

    return {"status": "success", "statusCode": 200, "message" : "Successfully got expences", 
            "total_count": total_expences,
            "current_page": page,
            "total_page": total_page,
            "prev_page": page-1 if page and page > 1 else None, 
            "next_page": page+1 if page and page < total_page else None,
            "data": query.all()}
