from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Status model to manage appointment statuses
class Status(db.Model):
    __tablename__ = 'status'
    status_id = db.Column(db.Integer, primary_key=True)
    status_name = db.Column(db.String(50), nullable=False)

# Slot model to manage standard time slots
class Slot(db.Model):
    __tablename__ = 'slots'
    slot_id = db.Column(db.Integer, primary_key=True)
    slot_time = db.Column(db.String(20), nullable=False)

# Appointment model
class Appointment(db.Model):
    __tablename__ = 'appointments'
    appointment_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    professional_id = db.Column(db.Integer, nullable=False)
    appointment_date = db.Column(db.Date, nullable=False)
    appointment_slot_id = db.Column(db.Integer, db.ForeignKey('slots.slot_id'), nullable=False)
    status_id = db.Column(db.Integer, db.ForeignKey('status.status_id'), default=1, nullable=False)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Define relationships
    slot = db.relationship('Slot', backref=db.backref('appointments', lazy=True))
    status = db.relationship('Status', backref=db.backref('appointments', lazy=True))
