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


router = APIRouter(prefix= "/billing",
                   tags=["Billing"])


@router.post("/create", status_code=status.HTTP_201_CREATED, response_model=schemas.CommonResponseModel)
async def create(complaint_id : int = Form(...),
                 amount : int = Form(...),
                 bill_type : models.BillType = Form(...),
                 bill_number : str = Form(...),
                 bill_photo : Optional[UploadFile] = File(None),
                 asset_photo : Optional[UploadFile] = File(None),
                 remarks : Optional[str] = Form(None),
                 db: Session = Depends(get_db), 
                 current_user : models.User = Depends(oauth2.get_current_user)):
    
    complaint = db.query(models.Complaint).filter(models.Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found")
    
    if not complaint.is_started:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="The service is not started yet")
    
    if complaint.enginner_id != current_user.id and current_user.role != 2:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only assigned engineer or admin can create bill")
    
    new_bill = models.Bill(firm_id = complaint.firm_id,
                customer_id = complaint.customer_id,
                amount = amount,
                bill_type = bill_type,
                bill_number = bill_number,
                remarks = remarks,
                created_by = current_user.id)
    if bill_photo:
        try:
            res = await blob.upload_file(bill_photo)
            new_bill.photo = res['firebase_url']
        except Exception:
            raise HTTPException(status_code=status.HTTP_424_FAILED_DEPENDENCY, detail="Something went wrong, please try again after some time")

    if asset_photo:
        try:
            res = await blob.upload_file(asset_photo)
            new_bill.asset_photo = res['firebase_url']
        except Exception:
            raise HTTPException(status_code=status.HTTP_424_FAILED_DEPENDENCY, detail="Something went wrong, please try again after some time")

    db.add(new_bill)
    db.commit()
    db.refresh(new_bill)
    complaint.bill_id = new_bill.id
    complaint.is_resolved = True
    db.commit()

    return {"status": "success", "statusCode": 201, "message" : "Successfully added bill"}



@router.get('/receive_credit_payment', response_model=schemas.CommonResponseModel)
async def receive_credit_payment(bill_id : int, db: Session = Depends(get_db), 
                 current_user : models.User = Depends(oauth2.get_current_user)):
    
    bill = db.query(models.Bill).filter(models.Bill.id == bill_id).first()

    if not bill:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bill not found")
    
    if bill.created_by != current_user.id and current_user.role != 2:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admin or who created the bill can collect this payment")
    
    bill.bill_type = models.BillType.cash
    db.commit()

    return {"status": "success", "statusCode": 200, "message" : "Successfully received payment"}


@router.get('/approve', response_model=schemas.CommonResponseModel)
async def approve(bill_id : int, db: Session = Depends(get_db), 
                 current_user : models.User = Depends(oauth2.get_current_user)):
    bill = db.query(models.Bill).filter(models.Bill.id == bill_id).first()
    if not bill:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bill not found")
    
    if current_user.role != 2:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admin can approve bills")
    
    bill.is_handed = True

    db.commit()

    return {"status": "success", "statusCode": 200, "message" : "Successfully approved bill payment"}


@router.get('/get_all', response_model=schemas.AllBillResponseModel)
async def get_all(is_approved : Optional[bool] = None, bill_type: Optional[models.BillType] = None, day_count : Optional[int] = 30, page : Optional[int] = 1, limit : Optional[int] = 10, search : Optional[str] = "", db: Session = Depends(get_db), 
                        current_user : models.User = Depends(oauth2.get_current_user)):
    query = (
        db.query(models.Bill)
        .join(models.User, models.Bill.created_by)
        .join(models.Customer, models.Bill.customer_id)
        .filter(or_(models.User.name.ilike(f'%{search}%'),
                    # models.Bill.id.ilike(f'%{search}%'),
                    models.Bill.bill_number.ilike(f'%{search}%'),
                    models.Customer.name.ilike(f'%{search}%'),
                    models.Customer.contact_no.ilike(f'%{search}%'),
                    models.Customer.address.ilike(f'%{search}%')
                    ), 
                    models.Bill.created_at > (datetime.now() - timedelta(days=day_count)).date(),
                    )
        .order_by(models.Bill.created_at.desc())
        .options(joinedload(models.Bill.engineer), # Eager load the engineer relationship
                 joinedload(models.Bill.customer)) # Eager load the customer relationship 
    )

    # If not admin, then show only assigned bills
    if current_user.role != 2:
        query = query.filter(models.Bill.created_by == current_user.id)

    # Filters
    # -------
    # Bill Type
    if bill_type:
        query = query.filter(models.Bill.bill_type == bill_type)

    # Approved
    if is_approved is not None:
        query = query.filter(models.Bill.is_handed == is_approved)

    total_bills = query.count()

    offset = (page - 1) * limit
    query.limit(offset)

    total_page = math.ceil(total_bills/(limit if limit and limit > 0 else 10))

    return {"status": "success", "statusCode": 200, "message" : "Successfully got bills", 
            "total_count": total_bills,
            "current_page": page,
            "total_page": total_page,
            "prev_page": page-1 if page and page > 1 else None, 
            "next_page": page+1 if page and page < total_page else None,
            "data": query.all()}
