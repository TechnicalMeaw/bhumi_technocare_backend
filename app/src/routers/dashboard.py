from fastapi import APIRouter, Depends, HTTPException, status, Form, UploadFile, File, Request
from .. import schemas, utils, models, oauth2
from ..database import get_db
from sqlalchemy.orm import Session, joinedload
from datetime import datetime, timedelta
from typing import Annotated, List, Optional
from ..config import settings
from app.src.firebase import storage as blob
from sqlalchemy.sql.expression import cast, or_, and_
from sqlalchemy import String, func, select
import math
from app.src.firebase import storage as blob


router = APIRouter(prefix= "/dashboard",
                   tags=["Dashboard"])


@router.get("/services")
async def services(day_count : Optional[int] = 30, db: Session = Depends(get_db), 
                        current_user : models.User = Depends(oauth2.get_current_user)):
    
    query = db.query(models.Complaint).filter(models.Complaint.is_deleted == False, models.Complaint.created_at > (datetime.now() - timedelta(days=day_count)).date())

    if current_user.role != 2:
        query = query.filter(models.Complaint.enginner_id == current_user.id)
        
    total = query.count()
    pending = query.filter(models.Complaint.is_resolved == False, models.Complaint.is_started == False).count()
    in_progress = query.filter(models.Complaint.is_resolved == False, models.Complaint.is_started == True).count()
    completed = query.filter(models.Complaint.is_resolved == True).count()
    canceled = query.filter(models.Complaint.is_deleted == True).count()


    return {"status": "success", "statusCode": 200, "message" : "Successfully got service graph data",
            "total" : total,
            "data": [
                {
                    "label": "Pending",
                    "value": pending
                },
                {
                    "label": "In-progress",
                    "value": in_progress
                },
                {
                    "label": "Completed",
                    "value": completed
                },
                 {
                    "label": "Canceled",
                    "value": canceled
                }
            ]}


@router.get("/payments")
async def payments(day_count : Optional[int] = 30, db: Session = Depends(get_db), 
                        current_user : models.User = Depends(oauth2.get_current_user)):
    
    query = db.query(models.Bill).filter(models.Bill.created_at > (datetime.now() - timedelta(days=day_count)).date())

    if current_user.role != 2:
        query = query.filter(models.Bill.created_by == current_user.id)
        
    total = query.with_entities(func.sum(models.Bill.amount)).scalar() or 0
    cash = query.filter(models.Bill.bill_type == models.BillType.cash).with_entities(func.sum(models.Bill.amount)).scalar() or 0
    credit = query.filter(models.Bill.bill_type == models.BillType.credit).with_entities(func.sum(models.Bill.amount)).scalar() or 0
    bill = query.filter(models.Bill.bill_type == models.BillType.bill).with_entities(func.sum(models.Bill.amount)).scalar() or 0
    not_handed = query.filter(models.Bill.is_handed == False).with_entities(func.sum(models.Bill.amount)).scalar() or 0


    return {"status": "success", "statusCode": 200, "message" : "Successfully got bill type graph data",
            "total" : total,
            "data": [
                {
                    "label": "Cash",
                    "value": cash
                },
                {
                    "label": "Credit",
                    "value": credit
                },
                {
                    "label": "Bill",
                    "value": bill
                },
                {
                    "label": "Due",
                    "value": not_handed
                }
            ]}


# @router.get("/payments")
# async def service(day_count : Optional[int] = 30, db: Session = Depends(get_db), 
#                         current_user : models.User = Depends(oauth2.get_current_user)):
    
#     query = db.query(models.Bill).filter(models.Bill.created_at > (datetime.now() - timedelta(days=day_count)).date())

#     if current_user.role != 2:
#         query = query.filter(models.Bill.created_by == current_user.id, models.Bill.bill_type != models.BillType.bill)
        
#     total = query.with_entities(func.sum(models.Bill.amount)).scalar() or 0
#     handed = query.filter(models.Bill.is_handed == True).with_entities(func.sum(models.Bill.amount)).scalar() or 0
#     not_handed = query.filter(models.Bill.is_handed == False).with_entities(func.sum(models.Bill.amount)).scalar() or 0


#     return {"status": "success", "statusCode": 200, "message" : "Successfully got payments graph data",
#             "total" : total,
#             "data": [
#                 {
#                     "label": "Received" if current_user.role == 2 else "Submitted",
#                     "value": handed
#                 },
#                 {
#                     "label": "Due",
#                     "value": not_handed
#                 }
#             ]}


@router.get("/product_type_wise_service_data")
async def product_type_wise_service_data(day_count : Optional[int] = 30, db: Session = Depends(get_db), 
                        current_user : models.User = Depends(oauth2.get_current_user)):
    
    query = (
        db.query(
            func.count(models.Complaint.id).label('complaint_count'),
            models.ProductType.name
        ).filter(models.Complaint.created_at > (datetime.now() - timedelta(days=day_count)).date(), 
                 models.Complaint.is_deleted == False)
        .outerjoin(models.ProductType, models.Complaint.product_type_id == models.ProductType.id)
        .group_by(models.ProductType.name)
    )

    if current_user.role != 2:
        query = query.filter(models.Complaint.enginner_id == current_user.id)

    # Execute and fetch results
    results = query.all()
    data = []
    total = 0
    for count, name in results:
        total += count
        data.append(
            {
                "label": name,
                "value": count
            }
        )


    return {"status": "success", "statusCode": 200, "message" : "Successfully got product type wise service graph data",
            "total" : total,
            "data": data
            }