from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.src import models
from app.src.database import engine
from app.src.routers import users, auth, engineers, service, notice, attendance


# models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(engineers.router)
app.include_router(service.router)
app.include_router(notice.router)
app.include_router(attendance.router)
