import enum
from sqlalchemy import Column, Enum, Integer, String, Boolean, TIMESTAMP, TextClause, ForeignKey, text
from .database import Base
from sqlalchemy.orm import relationship
import uuid
from sqlalchemy.dialects.postgresql import UUID




class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    name = Column(String, nullable = False)
    address = Column(String, nullable = False)
    photo = Column(String, nullable = True)
    country_code = Column(String, nullable=False)
    phone_no = Column(String, nullable=False)
    family_contact_no = Column(String, nullable = True)
    resume = Column(String, nullable = True)
    dob = Column(String, nullable = False)
    blood_group = Column(String, nullable = False)
    depertment = Column(String, nullable = False)
    post = Column(String, nullable = False)
    remarks = Column(String, nullable = True)

    password = Column(String, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=TextClause("Now()"))
    is_verified = Column(Boolean, nullable = False, server_default = TextClause("True"))
    role = Column(Integer, server_default = TextClause("1"))
    last_login = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("Now()"))
    is_active = Column(Boolean, nullable = False, server_default = text("True"))

class Area(Base):
    __tablename__ = "area"
    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    name = Column(String, nullable = False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=TextClause("Now()"))
    is_active = Column(Boolean, nullable = False, server_default = text("True"))

class City(Base):
    __tablename__ = "city"
    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    name = Column(String, nullable = False)
    area = Column(Integer, ForeignKey(Area.id, ondelete="CASCADE"), nullable = False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=TextClause("Now()"))
    is_active = Column(Boolean, nullable = False, server_default = text("True"))

class Firm(Base):
    __tablename__ = "firms"
    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    name = Column(String, nullable = False)
    area = Column(Integer, ForeignKey(Area.id, ondelete="CASCADE"), nullable = True)
    city = Column(Integer, ForeignKey(City.id, ondelete="CASCADE"), nullable = True)
    contact_person = Column(String, nullable = True)
    address = Column(String, nullable = False)
    contact_no = Column(String, nullable = True)
    pincode = Column(String, nullable = True)
    gst_no = Column(String, nullable = True)
    remarks = Column(String, nullable = True)
    photo = Column(String, nullable = True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=TextClause("Now()"))
    is_active = Column(Boolean, nullable = False, server_default = text("True"))



class Customer(Base):
    __tablename__ = "customers"
    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    firm_id = Column(Integer, ForeignKey(Firm.id, ondelete="CASCADE"), nullable = True)
    name = Column(String, nullable = False)
    contact_no = Column(String, nullable = False)
    depertment = Column(String, nullable = True)
    address = Column(String, nullable = False)
    remarks = Column(String, nullable = True)
    photo = Column(String, nullable = True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=TextClause("Now()"))
    is_active = Column(Boolean, nullable = False, server_default = text("True"))


class Asset(Base):
    __tablename__ = "assets"
    id = Column(String, primary_key=True, nullable=False)
    category = Column(String, nullable = True)
    name = Column(String, nullable = False)
    remarks = Column(String, nullable = True)
    manufacturing_year = Column(Integer, nullable=False)
    estimate_cost = Column(Integer, nullable=False)
    photo = Column(String, nullable = True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=TextClause("Now()"))
    is_active = Column(Boolean, nullable = False, server_default = text("True"))

class ProductType(Base):
    __tablename__ = "product_type"
    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    name = Column(String, nullable = False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=TextClause("Now()"))
    is_active = Column(Boolean, nullable = False, server_default = text("True"))


class Complaint(Base):
    __tablename__ = "complaints"
    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    firm_id = Column(Integer, ForeignKey(Firm.id, ondelete="CASCADE"), nullable = True)
    customer_id = Column(Integer, ForeignKey(Customer.id, ondelete="CASCADE"), nullable = False)
    product_type_id = Column(Integer, ForeignKey(ProductType.id, ondelete="CASCADE"), nullable = False)
    enginner_id = Column(Integer, ForeignKey(User.id, ondelete="CASCADE"), nullable = False)
    due_date = Column(TIMESTAMP(timezone=True), nullable=False, server_default=TextClause("Now()"))
    service_type = Column(String, nullable = False)

    # contact_no = Column(String, nullable = False)
    asset_id = Column(String, ForeignKey(Asset.id, ondelete="CASCADE"), nullable = True)
    remarks = Column(String, nullable = True)
    photo = Column(String, nullable = True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=TextClause("Now()"))
    is_resolved = Column(Boolean, nullable = False, server_default = text("False"))


class UserSessions(Base):
    __tablename__ = "user_sessions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey(User.id, ondelete="CASCADE"), index= True, nullable = False)
    device_id = Column(String, nullable = False, unique= True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=TextClause("Now()"))
    is_active = Column(Boolean, nullable = False, server_default = text("True"))


