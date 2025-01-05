from fastapi import APIRouter, Depends, HTTPException, status, Form, UploadFile, File, Request
from .. import schemas, utils, models, oauth2
from ..database import get_db
from sqlalchemy.orm import Session, joinedload
from datetime import datetime, timedelta
from typing import Annotated, List, Optional
from ..config import settings
from app.src.firebase import storage as blob
from sqlalchemy.sql.expression import cast, or_, and_
from sqlalchemy import String, select
import math
from app.src.firebase import storage as blob


router = APIRouter(prefix= "/service",
                   tags=["Service/Leads"])


@router.post("/create_complaint", status_code=status.HTTP_201_CREATED, response_model=schemas.CommonResponseModel)
async def create_complaint(
                        customer_id : Annotated[int, Form()],
                        product_type_id : Annotated[int, Form()],
                        enginner_id : Annotated[int, Form()],
                        due_date : Annotated[datetime, Form()],     # 'due_date': '2024-10-20T23:59:59'  # Format for datetime
                        service_type_id : Annotated[int, Form()],
                        firm_id : Optional[int] = Form(None),
                        asset_id : Optional[int] = Form(None),
                        remarks : Optional[str] = Form(None),
                        photo : Optional[UploadFile] = File(None),

                        db: Session = Depends(get_db), 
                        current_user : models.User = Depends(oauth2.get_current_user)
                        ):

    if current_user.role != 2:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admin can create complaints")
    
    customer = db.query(models.Customer).filter(models.Customer.id == customer_id, models.Customer.is_active == True).first()
    if not customer:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid customer id")
    
    product_type = db.query(models.ProductType).filter(models.ProductType.id == product_type_id, models.ProductType.is_active == True).first()
    if not product_type:
        raise HTTPException(status_code= status.HTTP_400_BAD_REQUEST, detail= "Invalid product type")
    
    engineer = db.query(models.User).filter(models.User.role != 2, models.User.id == enginner_id, models.User.is_active == True).first()
    if not engineer:
        raise HTTPException(status_code= status.HTTP_400_BAD_REQUEST, detail= "Invalid engineer id")
    
    service_type = db.query(models.ServiceType).filter(models.ServiceType.id == service_type_id, models.ServiceType.is_active == True).first()
    if not service_type:
        raise HTTPException(status_code= status.HTTP_400_BAD_REQUEST, detail= "Invalid service type")

    
    new_complaint = models.Complaint(customer_id = customer_id,
                                      product_type_id = product_type_id, 
                                      enginner_id = enginner_id, 
                                      due_date = due_date,
                                      service_type_id = service_type.id, 
                                      remarks = remarks)
    
    # Optional
    if firm_id:
        firm = db.query(models.Firm).filter(models.Firm.id == firm_id).first()
        if not firm:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid organization id")
        new_complaint.firm_id = firm_id
        
    # Optional
    if asset_id:
        asset = db.query(models.Asset).filter(models.Asset.id == asset_id).first()
        if not asset:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid asset id")
        new_complaint.asset_id = asset_id

    # Optional
    if photo:
        try:
            res = await blob.upload_file(photo)
            new_complaint.photo = res['firebase_url']
        except Exception:
            pass

    db.add(new_complaint)
    db.commit()

    return {"status": "success", "statusCode": 201, "message" : "Complaint Created"}


@router.put("/update_complaint", response_model=schemas.UpdateServiceResponseModel)
async def update_complaint(
                        complaint_id : Annotated[int, Form()],
                        customer_id : Optional[int] = Form(None),
                        product_type_id : Optional[int] = Form(None),
                        enginner_id : Optional[int] = Form(None),
                        due_date : Optional[datetime] = Form(None),     # 'due_date': '2024-10-20T23:59:59'  # Format for datetime
                        service_type_id : Optional[int] = Form(None),
                        firm_id : Optional[int] = Form(None),
                        asset_id : Optional[int] = Form(None),
                        remarks : Optional[str] = Form(None),
                        photo : Optional[UploadFile] = File(None),

                        db: Session = Depends(get_db), 
                        current_user : models.User = Depends(oauth2.get_current_user)
                        ):
    
    if current_user.role != 2:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admin can update complaints")
    
    complaint = db.query(models.Complaint).filter(models.Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found")
    
    # Customer
    if customer_id:
        customer = db.query(models.Customer).filter(models.Customer.id == customer_id, models.Customer.is_active == True).first()
        if not customer:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid customer id")
        complaint.customer_id = customer.id

    # Product Type
    if product_type_id:
        product_type = db.query(models.ProductType).filter(models.ProductType.id == product_type_id, models.ProductType.is_active == True).first()
        if not product_type:
            raise HTTPException(status_code= status.HTTP_400_BAD_REQUEST, detail= "Invalid product type")
        complaint.product_type_id = product_type.id

    # Engineer
    if enginner_id:
        engineer = db.query(models.User).filter(models.User.role != 2, models.User.id == enginner_id, models.User.is_active == True).first()
        if not engineer:
            raise HTTPException(status_code= status.HTTP_400_BAD_REQUEST, detail= "Invalid engineer id")
        complaint.enginner_id = engineer.id
    
    # Due Date
    if due_date and complaint.due_date != due_date:
        complaint.due_date = due_date

    # Service Type
    if service_type_id:
        service_type = db.query(models.ServiceType).filter(models.ServiceType.id == service_type_id, models.ServiceType.is_active == True).first()
        if not service_type:
            raise HTTPException(status_code= status.HTTP_400_BAD_REQUEST, detail= "Invalid service type")
        complaint.service_type_id = service_type.id

    # Organization
    if firm_id:
        firm = db.query(models.Firm).filter(models.Firm.id == firm_id).first()
        if not firm:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid organization id")
        complaint.firm_id = firm_id
        
    # Asset
    if asset_id:
        asset = db.query(models.Asset).filter(models.Asset.id == asset_id).first()
        if not asset:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid asset id")
        complaint.asset_id = asset_id

    # Photo
    if photo:
        try:
            # If photo exists then delete it
            if complaint.photo:
                await blob.delete_file(complaint.photo)
            # Upload the new photo
            res = await blob.upload_file(photo)
            # Assign it to the complaint
            complaint.photo = res['firebase_url']
        except Exception:
            pass

    # Remarks
    if remarks and complaint.remarks != remarks:
        complaint.remarks = remarks

    db.commit()
    db.refresh(complaint)

    return {"status": "success", "statusCode": 200, "message" : "Successfully Updated", "data": complaint}

    
        
@router.post("/add_firm", status_code=status.HTTP_201_CREATED, response_model=schemas.CommonResponseModel)
async def add_firm(     name : Annotated[str, Form()],
                        address : Annotated[str, Form()],
                        area_id : Optional[int] = Form(None),
                        city_id : Optional[int] = Form(None),
                        mobile_no : Optional[str] = Form(None),
                        contact_person_name : Optional[str] = Form(None),
                        pincode : Optional[str] = Form(None),
                        gst_no : Optional[str] = File(None),
                        remarks : Optional[str] = Form(None),
                        photo : Optional[UploadFile] = File(None),

                        db: Session = Depends(get_db), 
                        current_user : models.User = Depends(oauth2.get_current_user)
                        ):
    
    if current_user.role != 2:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admin can create complaints")
    
    new_firm = models.Firm(name = name, 
                           address = address, 
                           contact_no = mobile_no,
                           contact_person = contact_person_name,
                           pincode = pincode,
                           gst_no = gst_no,
                           remarks = remarks)

    # Optional
    if area_id:
        area = db.query(models.Area).filter(models.Area.id == area_id, models.Area.is_active == True).first()
        if not area:
            raise HTTPException(status_code= status.HTTP_400_BAD_REQUEST, detail="Invalid area id")
        new_firm.area = area.id

    # Optional
    if city_id:
        city = db.query(models.City).filter(models.City.id == city_id, models.City.is_active == True).first()
        if not city:
            raise HTTPException(status_code= status.HTTP_400_BAD_REQUEST, detail="Invalid city id")
        new_firm.area = city.id

    # Optional
    if photo:
        try:
            res = await blob.upload_file(photo)
            new_firm.photo = res['firebase_url']
        except Exception:
            pass

    db.add(new_firm)
    db.commit()

    return {"status": "success", "statusCode": 201, "message" : "Organization Created"}


@router.put("/edit_firm", response_model=schemas.CommonResponseModel)
async def edit_firm( firm_id : int = Form(...),
                        name : Optional[str] = Form(None),
                        address : Optional[str] = Form(None),
                        area_id : Optional[int] = Form(None),
                        city_id : Optional[int] = Form(None),
                        mobile_no : Optional[str] = Form(None),
                        contact_person_name : Optional[str] = Form(None),
                        pincode : Optional[str] = Form(None),
                        gst_no : Optional[str] = File(None),
                        remarks : Optional[str] = Form(None),
                        photo : Optional[UploadFile] = File(None),

                        db: Session = Depends(get_db), 
                        current_user : models.User = Depends(oauth2.get_current_user)
                        ):
    
    if current_user.role != 2:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admin can create complaints")
    
    firm = db.query(models.Firm).filter(models.Firm.id == firm_id).first()

    if not firm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid Firm id")
    
    if name:
        firm.name = name
    if address:
        firm.address = address
    if mobile_no:
        firm.contact_no = mobile_no
    if contact_person_name:
        firm.contact_person = contact_person_name
    if pincode:
        firm.pincode = pincode
    if gst_no:
        firm.gst_no = gst_no
    if remarks:
        firm.remarks = remarks

    # Optional
    if area_id:
        area = db.query(models.Area).filter(models.Area.id == area_id, models.Area.is_active == True).first()
        if not area:
            raise HTTPException(status_code= status.HTTP_400_BAD_REQUEST, detail="Invalid area id")
        firm.area = area.id

    # Optional
    if city_id:
        city = db.query(models.City).filter(models.City.id == city_id, models.City.is_active == True).first()
        if not city:
            raise HTTPException(status_code= status.HTTP_400_BAD_REQUEST, detail="Invalid city id")
        firm.area = city.id

    # Optional
    if photo:
        try:
            if firm.photo:
                await blob.delete_file(firm.photo)
            res = await blob.upload_file(photo)
            firm.photo = res['firebase_url']
        except Exception:
            pass

    db.commit()

    return {"status": "success", "statusCode": 200, "message" : "Organization Updated"}


@router.delete("/delete_firm", response_model=schemas.CommonResponseModel)
async def delete_firm( firm_id : int,
                        db: Session = Depends(get_db), 
                        current_user : models.User = Depends(oauth2.get_current_user)
                        ):
    
    if current_user.role != 2:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admin can delete organization")
    
    firm = db.query(models.Firm).filter(models.Firm.id == firm_id).first()
    if not firm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid firm id")
    
    is_used = db.query(models.Complaint).filter(models.Complaint.firm_id == firm.id)
    if is_used:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Organization is already in use")
    db.delete(firm)
    db.commit()
    
    return {"status": "success", "statusCode": 200, "message" : "Organization Deleted"}

@router.post("/add_customer", status_code=status.HTTP_201_CREATED, response_model=schemas.CommonResponseModel)
async def add_customer(     name : Annotated[str, Form()],
                        address : Annotated[str, Form()],
                        mobile_no : Annotated[str, Form()],
                        area_id : Optional[int] = Form(None),
                        city_id : Optional[int] = Form(None),
                        depertment : Optional[str] = Form(None),
                        organization_id : Optional[int] = Form(None),
                        remarks : Optional[str] = Form(None),
                        photo : Optional[UploadFile] = File(None),

                        db: Session = Depends(get_db), 
                        current_user : models.User = Depends(oauth2.get_current_user)
                        ):
    
    if current_user.role != 2:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admin can create customers")
    
    new_customer = models.Customer(name = name, 
                                   contact_no = mobile_no, 
                                   address = address,
                                   depertment = depertment,
                                   remarks = remarks)
    
    # Optional
    if area_id:
        area = db.query(models.Area).filter(models.Area.id == area_id, models.Area.is_active == True).first()
        if not area:
            raise HTTPException(status_code= status.HTTP_400_BAD_REQUEST, detail="Invalid area id")
        new_customer.area = area.id

    # Optional
    if city_id:
        city = db.query(models.City).filter(models.City.id == city_id, models.City.is_active == True).first()
        if not city:
            raise HTTPException(status_code= status.HTTP_400_BAD_REQUEST, detail="Invalid city id")
        new_customer.area = city.id
    
    # Optional
    if organization_id:
        firm = db.query(models.Firm).filter(models.Firm.id == organization_id, models.Firm.is_active == True).first()
        if not firm:
            raise HTTPException(status_code= status.HTTP_400_BAD_REQUEST, detail="Invalid organization id")
        new_customer.firm_id = firm.id

    # Optional
    if photo:
        try:
            res = await blob.upload_file(photo)
            new_customer.photo = res['firebase_url']
        except Exception:
            pass

    db.add(new_customer)
    db.commit()
    return {"status": "success", "statusCode": 201, "message" : "Customer Created"}


@router.put("/edit_customer", status_code=status.HTTP_201_CREATED, response_model=schemas.CommonResponseModel)
async def edit_customer( customer_id : Annotated[str, Form()],
                        name : Optional[str] = Form(None),
                        address : Optional[str] = Form(None),
                        mobile_no : Optional[str] = Form(None),
                        area_id : Optional[int] = Form(None),
                        city_id : Optional[int] = Form(None),
                        depertment : Optional[str] = Form(None),
                        organization_id : Optional[int] = Form(None),
                        remarks : Optional[str] = Form(None),
                        photo : Optional[UploadFile] = File(None),

                        db: Session = Depends(get_db), 
                        current_user : models.User = Depends(oauth2.get_current_user)
                        ):
    
    if current_user.role != 2:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admin can edit customers")
    
    customer = db.query(models.Customer).filter(models.Customer.id == customer_id).first()

    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid Customer id")
    
    if name:
        customer.name = name
    if address:
        customer.address = address
    if mobile_no:
        customer.contact_no = mobile_no
    if depertment:
        customer.depertment = depertment
    if remarks:
        customer.remarks = remarks
    
    # Optional
    if area_id:
        area = db.query(models.Area).filter(models.Area.id == area_id, models.Area.is_active == True).first()
        if not area:
            raise HTTPException(status_code= status.HTTP_400_BAD_REQUEST, detail="Invalid area id")
        customer.area = area.id

    # Optional
    if city_id:
        city = db.query(models.City).filter(models.City.id == city_id, models.City.is_active == True).first()
        if not city:
            raise HTTPException(status_code= status.HTTP_400_BAD_REQUEST, detail="Invalid city id")
        customer.area = city.id
    
    # Optional
    if organization_id:
        firm = db.query(models.Firm).filter(models.Firm.id == organization_id, models.Firm.is_active == True).first()
        if not firm:
            raise HTTPException(status_code= status.HTTP_400_BAD_REQUEST, detail="Invalid organization id")
        customer.firm_id = firm.id

    # Optional
    if photo:
        try:
            if customer.photo:
                await blob.delete_file(customer.photo)
            res = await blob.upload_file(photo)
            customer.photo = res['firebase_url']
        except Exception:
            pass

    db.commit()
    return {"status": "success", "statusCode": 201, "message" : "Customer Updated"}


@router.delete("/delete_customer", response_model=schemas.CommonResponseModel)
async def delete_customer( customer_id : int,
                        db: Session = Depends(get_db), 
                        current_user : models.User = Depends(oauth2.get_current_user)
                        ):
    
    if current_user.role != 2:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admin can delete customer")
    
    customer = db.query(models.Customer).filter(models.Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid customer id")
    
    is_used = db.query(models.Complaint).filter(models.Complaint.customer_id == customer.id)
    if is_used:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Customer is already in use")
    db.delete(customer)
    db.commit()
    
    return {"status": "success", "statusCode": 200, "message" : "Customer Deleted"}

@router.post("/add_area", status_code=status.HTTP_201_CREATED, response_model=schemas.CommonResponseModel)
async def add_area( body : schemas.CreateAreaRequestModel,
                        db: Session = Depends(get_db), 
                        current_user : models.User = Depends(oauth2.get_current_user)
                        ):
    
    if current_user.role != 2:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admin can create complaints")
    
    new_area = models.Area(name = body.name)
    db.add(new_area)
    db.commit()
    
    return {"status": "success", "statusCode": 201, "message" : "Area Added"}


@router.post("/add_city", status_code=status.HTTP_201_CREATED, response_model=schemas.CommonResponseModel)
async def add_city( body : schemas.CreateCityRequestModel,
                        db: Session = Depends(get_db), 
                        current_user : models.User = Depends(oauth2.get_current_user)
                        ):
    
    if current_user.role != 2:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admin can create city")
    
    area = db.query(models.Area).filter(models.Area.id == body.area_id, models.Area.is_active == True).first()
    if not area:
        raise HTTPException(status_code= status.HTTP_400_BAD_REQUEST, detail="Invalid area id")
    
    new_city = models.City(name = body.name, area = area.id)
    db.add(new_city)
    db.commit()

    return {"status": "success", "statusCode": 201, "message" : "Organization Created"}


@router.post("/add_product_type", status_code=status.HTTP_201_CREATED, response_model=schemas.CommonResponseModel)
async def add_product_type( body : schemas.CreateAreaRequestModel,
                        db: Session = Depends(get_db), 
                        current_user : models.User = Depends(oauth2.get_current_user)
                        ):
    
    if current_user.role != 2:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admin can create product type")
    
    new_product_type = models.ProductType(name = body.name)
    db.add(new_product_type)
    db.commit()
    
    return {"status": "success", "statusCode": 201, "message" : "Product Type Added"}


@router.put("/edit_product_type", response_model=schemas.CommonResponseModel)
async def edit_product_type(product_type_id : int, updated_name : str,
                        db: Session = Depends(get_db), 
                        current_user : models.User = Depends(oauth2.get_current_user)):
    if current_user.role != 2:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admin can delete product type")
    
    product_type = db.query(models.ProductType).filter(models.ProductType.id == product_type_id).first()
    if not product_type:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid product type id")
    
    product_type.name = updated_name
    db.commit()
    return {"status": "success", "statusCode": 200, "message" : "Product Type Updated"}


@router.delete("/delete_product_type", response_model=schemas.CommonResponseModel)
async def delete_product_type( product_type_id : int,
                        db: Session = Depends(get_db), 
                        current_user : models.User = Depends(oauth2.get_current_user)
                        ):
    
    if current_user.role != 2:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admin can delete product type")
    
    product_type = db.query(models.ProductType).filter(models.ProductType.id == product_type_id).first()
    if not product_type:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid product type id")
    
    is_used = db.query(models.Complaint).filter(models.Complaint.product_type_id == product_type.id)
    if is_used:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Product type is already in use")
    db.delete(product_type)
    db.commit()
    
    return {"status": "success", "statusCode": 200, "message" : "Product Type Deleted"}


@router.post("/add_service_type", status_code=status.HTTP_201_CREATED, response_model=schemas.CommonResponseModel)
async def add_service_type( body : schemas.CreateAreaRequestModel,
                        db: Session = Depends(get_db), 
                        current_user : models.User = Depends(oauth2.get_current_user)
                        ):
    
    if current_user.role != 2:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admin can create service type")
    
    new_product_type = models.ServiceType(name = body.name)
    db.add(new_product_type)
    db.commit()
    
    return {"status": "success", "statusCode": 201, "message" : "Product Type Added"}


@router.put("/edit_service_type", response_model=schemas.CommonResponseModel)
async def edit_service_type(service_type_id : int, updated_name : str,
                        db: Session = Depends(get_db), 
                        current_user : models.User = Depends(oauth2.get_current_user)):
    if current_user.role != 2:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admin can delete service type")
    
    service_type = db.query(models.ServiceType).filter(models.ServiceType.id == service_type_id).first()
    if not service_type:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid service type id")
    
    service_type.name = updated_name
    db.commit()
    return {"status": "success", "statusCode": 200, "message" : "Service Type Updated"}


@router.delete("/delete_service_type", response_model=schemas.CommonResponseModel)
async def delete_service_type( service_type_id : int,
                        db: Session = Depends(get_db), 
                        current_user : models.User = Depends(oauth2.get_current_user)
                        ):
    
    if current_user.role != 2:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admin can delete service type")
    
    service_type = db.query(models.ServiceType).filter(models.ServiceType.id == service_type_id).first()
    if not service_type:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid service type id")
    
    is_used = db.query(models.Complaint).filter(models.Complaint.service_type_id == service_type.id)
    if is_used:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Service type is already in use")
    
    db.delete(service_type)
    db.commit()
    
    return {"status": "success", "statusCode": 200, "message" : "Service Type Deleted"}



@router.get("/service_types", response_model = schemas.AllAreaResponseModel)
async def get_service_type(is_active : Optional[bool] = None, page : Optional[int] = None, limit : Optional[int] = None, search : Optional[str] = "", db: Session = Depends(get_db), 
                    current_user : models.User = Depends(oauth2.get_current_user)):
    
    query = db.query(models.ServiceType).filter(cast(models.ServiceType.name, String).ilike(f'%{search}%')).order_by(models.ServiceType.created_at.desc())
    if is_active is not None:
        query = query.filter(models.ServiceType.is_active == is_active)

    total_service_type = query.count()

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

        total_page = math.ceil(total_service_type/(limit if limit and limit > 0 else 10))

    return {"status": "success", "statusCode": 200, "message" : "Successfully got service types", 
            "total_count": total_service_type,
            "current_page": page,
            "total_page": total_page,
            "prev_page": page-1 if page and page > 1 else None, 
            "next_page": page+1 if page and page < total_page else None,
            "data": query.all()}


@router.get("/product_types", response_model = schemas.AllAreaResponseModel)
async def get_product_types(is_active : Optional[bool] = None, page : Optional[int] = None, limit : Optional[int] = None, search : Optional[str] = "", db: Session = Depends(get_db), 
                    current_user : models.User = Depends(oauth2.get_current_user)):
    
    query = db.query(models.ProductType).filter(cast(models.ProductType.name, String).ilike(f'%{search}%')).order_by(models.ProductType.created_at.desc())
    if is_active is not None:
        query = query.filter(models.ProductType.is_active == is_active)

    total_product_type = query.count()

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

        total_page = math.ceil(total_product_type/(limit if limit and limit > 0 else 10))

    return {"status": "success", "statusCode": 200, "message" : "Successfully got product types", 
            "total_count": total_product_type,
            "current_page": page,
            "total_page": total_page,
            "prev_page": page-1 if page and page > 1 else None, 
            "next_page": page+1 if page and page < total_page else None,
            "data": query.all()}


@router.get("/areas", response_model = schemas.AllAreaResponseModel)
async def get_areas(is_active : Optional[bool] = None, page : Optional[int] = None, limit : Optional[int] = None, search : Optional[str] = "", db: Session = Depends(get_db), 
                    current_user : models.User = Depends(oauth2.get_current_user)):
    
    query = db.query(models.Area).filter(cast(models.Area.name, String).ilike(f'%{search}%')).order_by(models.Area.created_at.desc())
    if is_active is not None:
        query = query.filter(models.Area.is_active == is_active)

    total_area = query.count()

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

        total_page = math.ceil(total_area/(limit if limit and limit > 0 else 10))

    return {"status": "success", "statusCode": 200, "message" : "Successfully got areas", 
            "total_count": total_area,
            "current_page": page,
            "total_page": total_page,
            "prev_page": page-1 if page and page > 1 else None, 
            "next_page": page+1 if page and page < total_page else None,
            "data": query.all()}


@router.get("/cities", response_model = schemas.AllAreaResponseModel)
async def get_cities(area_id : Optional[int] = None, is_active : Optional[bool] = None, page : Optional[int] = None, limit : Optional[int] = None, search : Optional[str] = "", db: Session = Depends(get_db), 
                    current_user : models.User = Depends(oauth2.get_current_user)):
    query = db.query(models.City).filter(cast(models.City.name, String).ilike(f'%{search}%')).order_by(models.City.created_at.desc())

    if area_id:
        query = query.filter(models.City.area == area_id)

    if is_active is not None:
        query = query.filter(models.City.is_active == is_active)

    total_city = query.count()

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

        total_page = math.ceil(total_city/(limit if limit and limit > 0 else 10))

    return {"status": "success", "statusCode": 200, "message" : "Successfully got cities", 
            "total_count": total_city,
            "current_page": page,
            "total_page": total_page,
            "prev_page": page-1 if page and page > 1 else None, 
            "next_page": page+1 if page and page < total_page else None,
            "data": query.all()}


@router.get("/organizations", response_model = schemas.AllAreaResponseModel)
async def get_organizations(is_active : Optional[bool] = None, page : Optional[int] = None, limit : Optional[int] = None, search : Optional[str] = "", db: Session = Depends(get_db), 
                    current_user : models.User = Depends(oauth2.get_current_user)):
    
    query = db.query(models.Firm).filter(or_(cast(models.Firm.name, String).ilike(f'%{search}%'),
                                             cast(models.Firm.contact_no, String).ilike(f'%{search}%'))).order_by(models.Firm.created_at.desc())
    if is_active is not None:
        query = query.filter(models.Firm.is_active == is_active)

    total_firms = query.count()

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

        total_page = math.ceil(total_firms/(limit if limit and limit > 0 else 10))

    return {"status": "success", "statusCode": 200, "message" : "Successfully got cities", 
            "total_count": total_firms,
            "current_page": page,
            "total_page": total_page,
            "prev_page": page-1 if page and page > 1 else None, 
            "next_page": page+1 if page and page < total_page else None,
            "data": query.all()}


@router.get("/customers", response_model = schemas.AllAreaResponseModel)
async def get_customers(organization_id : Optional[int] = None, is_active : Optional[bool] = None, page : Optional[int] = None, limit : Optional[int] = None, search : Optional[str] = "", db: Session = Depends(get_db), 
                    current_user : models.User = Depends(oauth2.get_current_user)):
    query = db.query(models.Customer).filter(or_(
        cast(models.Customer.name, String).ilike(f'%{search}%'),
        cast(models.Customer.contact_no, String).ilike(f'%{search}%'))
        ).order_by(models.Customer.created_at.desc())

    if organization_id:
        query = query.filter(models.Customer.firm_id == organization_id)

    if is_active is not None:
        query = query.filter(models.Customer.is_active == is_active)

    total_customer = query.count()

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

        total_page = math.ceil(total_customer/(limit if limit and limit > 0 else 10))

    return {"status": "success", "statusCode": 200, "message" : "Successfully got customers", 
            "total_count": total_customer,
            "current_page": page,
            "total_page": total_page,
            "prev_page": page-1 if page and page > 1 else None, 
            "next_page": page+1 if page and page < total_page else None,
            "data": query.all()}



@router.get("/complaints", response_model=schemas.ServiceResponseModel)
async def get_complaints(organization_id : Optional[int] = None, 
                         customer_id : Optional [int] = None,
                         engineer_id : Optional[int] = None,

                         service_type_id : Optional[int] = None,
                         product_type_id : Optional[int] = None,

                         is_resolved : Optional[bool] = None,
                         is_overdue : Optional[bool] = None,

                         is_started : Optional[bool] = None,

                         day_count : Optional[int] = 30,

                         page : Optional[int] = 1, 
                         limit : Optional[int] = 10, 
                         search : Optional[str] = "", 
                         db: Session = Depends(get_db), current_user : models.User = Depends(oauth2.get_current_user)):
    
    query = (
        db.query(models.Complaint)
        .join(models.Firm, models.Complaint.organization)  # Join with Firm
        .join(models.City, models.Firm.city == models.City.id, isouter=True)  # Join with City
        .join(models.Area, models.Firm.area == models.Area.id, isouter=True)  # Join with Area
        .join(models.Customer, models.Complaint.customer)  # Join with Customer
        .join(models.User, models.Complaint.engineer)  # Join with Engineer/User
        .join(models.ServiceType, models.Complaint.service_type)  # Join with ServiceType
        .join(models.ProductType, models.Complaint.product_type)  # Join with ProductType
        .filter(
            or_(
                cast(models.Complaint.id, String).ilike(f"%{search}%"),         # Complaint ID
                cast(models.Firm.name, String).ilike(f"%{search}%"),           # Firm Name
                cast(models.City.name, String).ilike(f"%{search}%"),           # Firm City Name
                cast(models.Area.name, String).ilike(f"%{search}%"),           # Firm Area Name
                cast(models.Firm.address, String).ilike(f"%{search}%"),        # Firm Address
                cast(models.Customer.name, String).ilike(f"%{search}%"),       # Customer Name
                cast(models.Customer.address, String).ilike(f"%{search}%"),    # Customer Address
                cast(models.Customer.contact_no, String).ilike(f"%{search}%"), # Customer Contact
                cast(models.User.name, String).ilike(f"%{search}%"),           # Engineer Name
                cast(models.User.phone_no, String).ilike(f"%{search}%"),       # Engineer Phone No
                cast(models.ServiceType.name, String).ilike(f"%{search}%"),    # Service Type Name
                cast(models.ProductType.name, String).ilike(f"%{search}%")     # Product Type Name
            ),
            models.Complaint.created_at > (datetime.now() - timedelta(days=day_count)).date(),
            models.Complaint.is_deleted == False
        )
        .order_by(models.Complaint.created_at.desc())
    )

    # Apply Filter
    # ------------
    # Firm
    if organization_id:
        query = query.filter(models.Complaint.firm_id == organization_id)
    # Customer
    if customer_id:
        query = query.filter(models.Complaint.customer_id == customer_id)
    # Engineer [Default]
    if current_user.role == 1:
        query = query.filter(models.Complaint.enginner_id == current_user.id)
    # Engineer
    elif engineer_id:
        query = query.filter(models.Complaint.enginner_id == engineer_id)

    # Resolved
    if is_resolved is not None:
        query = query.filter(models.Complaint.is_resolved == is_resolved)
    # Overdue
    if is_overdue is not None:
        query = query.filter(models.Complaint.due_date > datetime.now())
    # Service Type
    if service_type_id:
        query = query.filter(models.Complaint.service_type_id == service_type_id)
    # Product Type
    if product_type_id:
        query = query.filter(models.Complaint.product_type_id == product_type_id)
    # Started or not
    if is_started is not None:
        query = query.filter(models.Complaint.is_started == is_started)



    total_complaints = query.count()
    query.offset((page - 1) * limit).limit(limit)

    total_page = math.ceil(total_complaints/limit)

    return {"status": "success", "statusCode": 200, "message" : "Successfully got complaints", 
            "total_count": total_complaints,
            "current_page": page,
            "total_page": total_page,
            "prev_page": page-1 if page and page > 1 else None, 
            "next_page": page+1 if page and page < total_page else None,
            "data": query.all()}


@router.delete('/delete_complaint')
async def delete_complaint(complaint_id : int, db: Session = Depends(get_db), current_user : models.User = Depends(oauth2.get_current_user)):
    if current_user.role != 2:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only Admins can delete complaint")
    
    complaint = db.query(models.Complaint).filter(models.Complaint.id == complaint_id).first()

    if not complaint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found")
    
    complaint.is_deleted = True
    db.commit()

    return {"status": "success", "statusCode": 200, "message" : "Complaint deleted"}


@router.get('/start_service')
async def start_service(complaint_id : int, db: Session = Depends(get_db), current_user : models.User = Depends(oauth2.get_current_user)):
    complaint = db.query(models.Complaint).filter(models.Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found")
    
    if complaint.enginner_id != current_user.id and current_user.role != 2:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only assigned engineer or admin can start the service")
    
    complaint.is_started = True
    db.commit()
    return {"status": "success", "statusCode": 200, "message" : "Service started"}

