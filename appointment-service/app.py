import json
import requests
from sqlalchemy import or_
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone

app = Flask(__name__)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:password@localhost/appointments'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

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
    appointment_slot_id = db.Column(db.Integer, db.ForeignKey('slots.slot_id'), nullable=False)  # Linking to slot_id
    status_id = db.Column(db.Integer, db.ForeignKey('status.status_id'), default=1, nullable=False)  # Linking to status_id
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Define relationships
    slot = db.relationship('Slot', backref=db.backref('appointments', lazy=True))
    status = db.relationship('Status', backref=db.backref('appointments', lazy=True))


# Create the database tables
@app.before_request
def create_tables():
    db.create_all()
    load_initial_data()

# Create the database tables and load initial data
def load_initial_data():
    # Check if there are already statuses in the database
    if Status.query.count() == 0:
        # Load initial status data
        statuses = [
            {'status_id': 1, 'status_name': 'booked'},
            {'status_id': 2, 'status_name': 'rescheduled'},
            {'status_id': 3, 'status_name': 'cancelled'}
        ]
        for status in statuses:
            db.session.add(Status(**status))
        db.session.commit()

    # Check if there are already slots in the database
    if Slot.query.count() == 0:
        # Load initial slot data
        slots = [
            {'slot_id': 1, 'slot_time': '09:00 AM - 10:00 AM'},
            {'slot_id': 2, 'slot_time': '10:00 AM - 11:00 AM'},
            {'slot_id': 3, 'slot_time': '11:00 AM - 12:00 PM'},
            {'slot_id': 4, 'slot_time': '12:00 PM - 01:00 PM'},
            {'slot_id': 5, 'slot_time': '01:00 PM - 02:00 PM'},
            {'slot_id': 6, 'slot_time': '02:00 PM - 03:00 PM'},
            {'slot_id': 7, 'slot_time': '03:00 PM - 04:00 PM'},
            {'slot_id': 8, 'slot_time': '04:00 PM - 05:00 PM'},
            {'slot_id': 9, 'slot_time': '05:00 PM - 06:00 PM'},
        ]
        for slot in slots:
            db.session.add(Slot(**slot))
        db.session.commit()

# Book a new appointment
@app.route('/appointment/book', methods=['POST'])
def book_appointment():
    data = request.json
    user_id=data['user_id']
    professional_id = data['professional_id']
    appointment_date = data['appointment_date']
    appointment_slot_id = data['appointment_slot_id']

    # Check if the same slot is already booked for the professional
    existing_appointment = Appointment.query.filter_by(
        professional_id=professional_id,
        appointment_date=appointment_date,
        appointment_slot_id=appointment_slot_id
    ).filter(or_(Appointment.status_id == 1, Appointment.status_id == 2)).first()

    if existing_appointment:
        return jsonify({'message': 'The selected slot is already booked!'}), 400

    # Proceed to book the appointment if no conflict is found
    new_appointment = Appointment(
        user_id=user_id,
        professional_id=professional_id,
        appointment_date=appointment_date,
        appointment_slot_id=appointment_slot_id,
        notes=data.get('notes', None)
    )
    db.session.add(new_appointment)
    db.session.commit()

    return jsonify({'message': 'Appointment booked successfully!'}), 201


# Check professional availability
@app.route('/professional/<int:professional_id>/availability', methods=['GET'])
def get_availability(professional_id):
    data = request.json
    # user_id=data['user_id']
    professional_id = data['professional_id']
    appointment_date = data['appointment_date']
    # appointment_slot_id = data['appointment_slot_id']

    professional = Appointment.query.get(professional_id)
    if not professional:
        return jsonify({'message': 'Professional not found!'}), 404

    # Query to find available slots
    available_slots = (
        db.session.query(Slot.slot_id, Slot.slot_time)
        .outerjoin(Appointment, (Slot.slot_id == Appointment.appointment_slot_id) & (Appointment.appointment_date == appointment_date))
        .outerjoin(Status, Appointment.status_id == Status.status_id)
        .filter(or_(Appointment.status_id.is_(None), Status.status_id == 3))  
        .all()
    )

    # Convert the result to a list of dictionaries
    available_slots_list = [{'slot_id': slot.slot_id, 'slot_time': slot.slot_time} for slot in available_slots]

    return jsonify({"available_slots": available_slots_list}), 200


# Reschedule an appointment
@app.route('/appointment/<int:appointment_id>/reschedule', methods=['PUT'])
def reschedule_appointment(appointment_id):
    data = request.json
    appointment = Appointment.query.get(appointment_id)

    # Extract necessary fields from the input data
    user_id = data['user_id']
    professional_id = data['professional_id']
    new_appointment_date = data['appointment_date']
    new_appointment_slot_id = data['appointment_slot_id']
    notes = data.get('notes', '')
    
    if not appointment or appointment.status_id == 3:
        return jsonify({'message': 'Appointment not found or already cancelled!'}), 404
    
    # Check if the new slot is available (status 1 = booked, status 2 = rescheduled)
    existing_appointment = (
        Appointment.query.filter_by(
            professional_id=professional_id,
            appointment_date=new_appointment_date,
            appointment_slot_id=new_appointment_slot_id
        )
        .filter(or_(Appointment.status_id == 1, Appointment.status_id == 2))  # Checking for booked or rescheduled slots
        .first()
    )

    if existing_appointment:
        return jsonify({'message': 'Selected slot is already booked!'}), 400

    # Proceed with rescheduling the appointment
    appointment.appointment_date = new_appointment_date
    appointment.appointment_slot_id = new_appointment_slot_id
    appointment.notes = notes  # Update notes if provided
    appointment.status_id = 2  # Mark the appointment as rescheduled

    db.session.commit()

    return jsonify({'message': 'Appointment rescheduled successfully!'}), 200


# Cancel an appointment
@app.route('/appointment/<int:appointment_id>/cancel', methods=['PUT'])
def cancel_appointment(appointment_id):
    # Fetch the appointment details
    appointment = Appointment.query.get(appointment_id)
    
    if not appointment or appointment.status_id == 3:  # Check if appointment is already cancelled
        return jsonify({'message': 'Appointment not found or already cancelled!'}), 404

    # Mark the appointment as canceled by updating the status_id to 3
    appointment.status_id = 3  # Assuming 3 is the status for "cancelled"
    db.session.commit()

    return jsonify({'message': 'Appointment cancelled successfully!'}), 200


# Fetch appointment details
from sqlalchemy.orm import joinedload
@app.route('/appointment/<int:appointment_id>', methods=['GET'])
def get_appointment(appointment_id):
    # Join Appointment with Slot and Status tables
    appointment = (
        db.session.query(Appointment)
        .options(joinedload(Appointment.slot))  # Load slot details
        .options(joinedload(Appointment.status))  # Load status details
        .filter_by(appointment_id=appointment_id)
        .first()
    )
    
    if not appointment:
        return jsonify({'message': 'Appointment not found!'}), 404

    return jsonify({
        'appointment_id': appointment.appointment_id,
        'user_id': appointment.user_id,
        'professional_id': appointment.professional_id,
        'appointment_date': appointment.appointment_date,
        'slot_time': appointment.slot.slot_time,  # Fetch slot time from the Slot table
        'status': appointment.status.status_name,  # Fetch status name from the Status table
        'notes': appointment.notes,
        'created_at': appointment.created_at,
        'updated_at': appointment.updated_at
    }), 200


# Fetch appointment history for a user
from sqlalchemy.orm import joinedload
@app.route('/user/<int:user_id>/appointments', methods=['GET'])
def get_user_appointments(user_id):
    # Query to fetch appointments and join with Slot and Status tables
    appointments = (
        db.session.query(Appointment)
        .options(joinedload(Appointment.slot))  # Eager load slot details
        .options(joinedload(Appointment.status))  # Eager load status details
        .filter_by(user_id=user_id)
        .all()
    )

    if not appointments:
        return jsonify({'message': 'No appointments found for this user!'}), 404

    return jsonify([{
        'appointment_id': appt.appointment_id,
        'professional_id': appt.professional_id,
        'appointment_date': appt.appointment_date,
        'slot_time': appt.slot.slot_time,  # Fetch slot time from Slot table
        'status': appt.status.status_name,  # Fetch status name from Status table
        'notes': appt.notes
    } for appt in appointments]), 200


from sqlalchemy.orm import joinedload
from datetime import datetime

# Fetch upcoming appointments for a professional
@app.route('/professional/<int:professional_id>/upcoming_appointments', methods=['GET'])
def get_professional_upcoming_appointments(professional_id):
    today = datetime.now().date()

    # Query to fetch appointments and join with Slot and Status tables
    appointments = (
        db.session.query(Appointment)
        .options(joinedload(Appointment.slot))  # Eager load slot details
        .options(joinedload(Appointment.status))  # Eager load status details
        .filter_by(professional_id=professional_id)
        .filter(Appointment.appointment_date >= today, Appointment.status_id != 3)  # Exclude cancelled appointments
        .all()
    )

    if not appointments:
        return jsonify({'message': 'No upcoming appointments for this professional!'}), 404

    return jsonify([{
        'appointment_id': appt.appointment_id,
        'user_id': appt.user_id,
        'appointment_date': appt.appointment_date,
        'slot_time': appt.slot.slot_time,  # Fetch slot time from Slot table
        'status': appt.status.status_name,  # Fetch status name from Status table
        'notes': appt.notes
    } for appt in appointments]), 200


if __name__ == '__main__':
    app.run(debug=True, port=5003)
