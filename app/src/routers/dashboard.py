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


    return {"status": "success", "statusCode": 200, "message" : "Successfully got service graph data",
            "data": [
                {
                    "label": "Total",
                    "value": total
                },
                {
                    "label": "Pending",
                    "value": pending
                },
                {
                    "label": "In-progress",
                    "value": in_progress
                }
            ]}


@router.get("/bills")
async def bills(day_count : Optional[int] = 30, db: Session = Depends(get_db), 
                        current_user : models.User = Depends(oauth2.get_current_user)):
    
    query = db.query(models.Bill).filter(models.Bill.created_at > (datetime.now() - timedelta(days=day_count)).date())

    if current_user.role != 2:
        query = query.filter(models.Bill.created_by == current_user.id)
        
    total = query.with_entities(func.sum(models.Bill.amount)).scalar() or 0
    cash = query.filter(models.Bill.bill_type == models.BillType.cash).with_entities(func.sum(models.Bill.amount)).scalar() or 0
    credit = query.filter(models.Bill.bill_type == models.BillType.credit).with_entities(func.sum(models.Bill.amount)).scalar() or 0
    bill = query.filter(models.Bill.bill_type == models.BillType.bill).with_entities(func.sum(models.Bill.amount)).scalar() or 0



    return {"status": "success", "statusCode": 200, "message" : "Successfully got bill type graph data",
            "data": [
                {
                    "label": "Total",
                    "value": total
                },
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
                }
            ]}


@router.get("/payments")
async def service(day_count : Optional[int] = 30, db: Session = Depends(get_db), 
                        current_user : models.User = Depends(oauth2.get_current_user)):
    
    query = db.query(models.Bill).filter(models.Bill.is_deleted == False, models.Bill.created_at > (datetime.now() - timedelta(days=day_count)).date())

    if current_user.role != 2:
        query = query.filter(models.Bill.created_by == current_user.id, models.Bill.bill_type != models.BillType.bill)
        
    total = query.with_entities(func.sum(models.Bill.amount)).scalar() or 0
    handed = query.filter(models.Bill.is_handed == True).with_entities(func.sum(models.Bill.amount)).scalar() or 0
    not_handed = query.filter(models.Bill.is_handed == False).with_entities(func.sum(models.Bill.amount)).scalar() or 0


    return {"status": "success", "statusCode": 200, "message" : "Successfully got payments graph data",
            "data": [
                {
                    "label": "Total",
                    "value": total
                },
                {
                    "label": "Received" if current_user.role == 2 else "Submitted",
                    "value": handed
                },
                {
                    "label": "Due",
                    "value": not_handed
                }
            ]}
