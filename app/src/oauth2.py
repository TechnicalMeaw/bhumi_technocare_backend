from jose import JWTError, jwt 
from . import schemas, database, models, easyAes
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from . import config

settings = config.settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='login')

# secret key
# algorithm
# expiration time

SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
aes = easyAes.EasyAES()
# ACCESS_TOKEN_EXPIRE_DAYS = settings.access_token_expire_days

def create_access_token(data : dict):
    to_encode = {"user_id" : aes.encrypt(str(data))}

    # expire = datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    # to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt

def verify_access_token(token: str, credentials_exception):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id : str = aes.decrypt(payload.get("user_id"))

        if user_id is None:
            raise credentials_exception
        
        token_data = schemas.TokenData(id=user_id)
    except JWTError:
        raise credentials_exception
    
    return token_data
    
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)):
    credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                           detail=f"Could not validate credentials",
                                             headers= {"WWW-Authenticate": "Bearer"})
    
    token_data = verify_access_token(token, credentials_exception)

    user = db.query(models.User).filter(models.User.id == token_data.id).first()

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    return user


# def get_current_temp_user(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)):
#     credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
#                                            detail=f"Could not validate credentials",
#                                              headers= {"WWW-Authenticate": "Bearer"})
    
#     token_data = verify_access_token(token, credentials_exception)

#     temp_user = db.query(models.TempUsers).filter(models.TempUsers.id == token_data.id).first()

#     if temp_user is None:
#         raise HTTPException(status_code=404, detail="User not found")

#     return temp_user