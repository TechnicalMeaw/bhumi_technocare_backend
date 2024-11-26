from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from .. import schemas, models, oauth2
from ..database import get_db
from sqlalchemy.orm import Session, joinedload
from datetime import datetime
from typing import Optional
from app.src.firebase import storage as blob
from sqlalchemy.sql import func
import math
from app.src.firebase import storage as blob


router = APIRouter(prefix= "/billing",
                   tags=["Billing"])


@router.post("/create", status_code=status.HTTP_201_CREATED, response_model=schemas.CommonResponseModel)
async def create(complaint_id : int,
                 amount : int,
                 bill_type : models.BillType,
                 bill_number : str,
                 photo : Optional[UploadFile] = File(None),
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
    if photo:
        try:
            res = await blob.upload_file(photo)
            new_bill.photo = res['firebase_url']
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


# @router.get('/get_all')
# async def get_all(bill_type: Optional[models.BillType] = None, day_count : Optional[int] = 30, page : Optional[int] = 1, limit : Optional[int] = 10, search : Optional[str] = "", db: Session = Depends(get_db), 
#                         current_user : models.User = Depends(oauth2.get_current_user)):
    
