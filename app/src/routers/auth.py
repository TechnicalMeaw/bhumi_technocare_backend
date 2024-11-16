from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, status, Form, UploadFile, File, Request
from .. import schemas, utils, models, oauth2
from ..database import get_db
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm

from datetime import datetime, timedelta
from typing import Annotated, List, Optional
from ..config import settings

router = APIRouter(tags=["Authentication"])


@router.post("/login", response_model= schemas.Token)
async def login(user_credentials: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    print(user_credentials.client_secret, settings.client_secret)
    if user_credentials.client_secret != settings.client_secret:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Request")
    
    user = db.query(models.User).filter(models.User.phone_no == user_credentials.username, models.User.is_active == True).first()
    print(user)
    if not user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Invalid Credentials")
    
    existing_session = db.query(models.UserSessions).filter(models.UserSessions.user_id == user.id).first()

    if not existing_session:
        new_session = models.UserSessions(user_id = user.id, device_id = user_credentials.client_id)
        db.add(new_session)
        db.commit()
    elif existing_session.is_active:
        if existing_session.device_id != user_credentials.client_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Existing user session in another device")
    else:
        existing_session.device_id = user_credentials.client_id
        db.commit()
    
    if not utils.verify(user_credentials.password, user.password):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Invalid Credentials")
    
    if not user.is_verified:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="First verify your phone number")
    
    # create a token
    access_token = oauth2.create_access_token(data=user.id)
    return {"token": access_token, "existing_user" : True, "user" : user}


@router.get("/logout")
async def logout(db: Session = Depends(get_db), current_user : models.User = Depends(oauth2.get_current_user)):
    existing_session = db.query(models.UserSessions).filter(models.UserSessions.user_id == current_user.id).first()
    existing_session.is_active = False
    db.commit()

    return {"status": "success", "statusCode": 200, "message" : "Logged Out"}


@router.post("/reset_password")
async def reset_password(request_data: schemas.ResetPasswordRequestModel, db: Session = Depends(get_db), current_user : models.User = Depends(oauth2.get_current_user)):
    if not utils.verify(request_data.old_password, current_user.password):
        raise HTTPException(status_code= status.HTTP_400_BAD_REQUEST, detail="Incorrect password")
    
    current_user.password = utils.hash(request_data.new_password)
    db.commit()
    
    return {"status": "success", "statusCode": 200, "message" : "Password Changed"}




