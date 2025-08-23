from extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    f_name = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False)  # Client, Lawyer
    created_at = db.Column(db.String(50)) 


class Specialty(db.Model):
    __tablename__ = "specialties"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    lawyer_id = db.Column(db.Integer, db.ForeignKey("lawyer_profiles.id")) 
    name = db.Column(db.String(100), nullable=False)

    


class LawyerProfile(db.Model):
    __tablename__ = "lawyer_profiles"

    id = db.Column(db.Integer, primary_key=True,  autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    experience = db.Column(db.Integer)
    location = db.Column(db.String(255))
    court_of_practice = db.Column(db.String(255))
    availability_details = db.Column(db.Text)
    v_hour = db.Column(db.String(255))

    



class InfoHub(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(150), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)
