import requests
from flask import Blueprint, request, jsonify
from sqlalchemy.orm import joinedload
from sqlalchemy import or_, and_
from db.models import Appointment, Slot, Status, db
from datetime import datetime
from config import Config

appointment_routes = Blueprint('appointment_routes', __name__)

# Base URLs for microservices
USER_SERVICE_URL = 'http://localhost:5001'
PROFESSIONAL_SERVICE_URL = "http://localhost:5002"
APPOINTMENT_SERVICE_URL = 'http://localhost:5003'

# Book a new appointment
@appointment_routes.route('/appointment/book', methods=['POST'])
def book_appointment():
    data = request.json
    user_id = data['user_id']
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
@appointment_routes.route('/professional/<int:professional_id>/availability', methods=['GET'])
def get_availability(professional_id):
    appointment_date = request.args.get('appointment_date')  
    print("appointment_date", appointment_date)
    response = requests.get(f"{PROFESSIONAL_SERVICE_URL}/professional/{professional_id}")
    professionals_data = response.json() if response.status_code == 200 else []

    if professionals_data:
        available_slots = (
            db.session.query(Slot.slot_id, Slot.slot_time, Appointment.appointment_id, Status.status_id)
            .outerjoin(Appointment, (Slot.slot_id == Appointment.appointment_slot_id) & 
                                    (Appointment.professional_id == professional_id) & 
                                    (Appointment.appointment_date == appointment_date))
            .outerjoin(Status, Appointment.status_id == Status.status_id)
            .filter(or_(Appointment.appointment_id.is_(None), Status.status_id == 3))
            .all()
        )

        available_slots_list = [{'slot_id': slot.slot_id, 'slot_time': slot.slot_time} for slot in available_slots]
        return jsonify({"available_slots": available_slots_list}), 200
    else:
        return jsonify({'message': 'Professional not found or slots not available!'}), 404

# Reschedule an appointment
@appointment_routes.route('/appointment/<int:appointment_id>/reschedule', methods=['PUT'])
def reschedule_appointment(appointment_id):
    data = request.json
    appointment = Appointment.query.get(appointment_id)

    if not appointment or appointment.status_id == 3:
        return jsonify({'message': 'Appointment not found or already cancelled!'}), 404

    # Check if the new slot is available
    new_appointment_date = data['appointment_date']
    new_appointment_slot_id = data['appointment_slot_id']
    professional_id = data['professional_id']

    existing_appointment = (
        Appointment.query.filter_by(
            professional_id=professional_id,
            appointment_date=new_appointment_date,
            appointment_slot_id=new_appointment_slot_id
        )
        .filter(or_(Appointment.status_id == 1, Appointment.status_id == 2))
        .first()
    )

    if existing_appointment:
        return jsonify({'message': 'Selected slot is already booked!'}), 400

    # Proceed with rescheduling the appointment
    appointment.appointment_date = new_appointment_date
    appointment.appointment_slot_id = new_appointment_slot_id
    appointment.notes = data.get('notes', appointment.notes)
    appointment.status_id = 2  # Mark the appointment as rescheduled

    db.session.commit()

    return jsonify({'message': 'Appointment rescheduled successfully!'}), 200

# Cancel an appointment
@appointment_routes.route('/appointment/<int:appointment_id>/cancel', methods=['DELETE'])
def cancel_appointment(appointment_id):
    appointment = Appointment.query.get(appointment_id)
    
    print(appointment)
    if not appointment or appointment.status_id == 3:
        return jsonify({'message': 'Appointment not found or already cancelled!'}), 404

    appointment.status_id = 3  
    db.session.commit()

    return jsonify({'message': 'Appointment cancelled successfully!'}), 200

# Fetch appointment details
@appointment_routes.route('/appointment/<int:appointment_id>', methods=['GET'])
def get_appointment(appointment_id):
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
        'slot_time': appointment.slot.slot_time,
        'status': appointment.status.status_name,
        'notes': appointment.notes,
        'created_at': appointment.created_at,
        'updated_at': appointment.updated_at
    }), 200

# Fetch appointment history for a user
@appointment_routes.route('/user/<int:user_id>/appointments', methods=['GET'])
def get_user_appointments(user_id):

    response = requests.get(f"{PROFESSIONAL_SERVICE_URL}/professionals")
    professionals_data = response.json() if response.status_code == 200 else []

    # Map professional_id to their details for easy access
    professionals_map = {
        professional['professional_id']: {
            "first_name": professional['first_name'],
            "last_name": professional['last_name'],
            "specialization": professional['specialization']
        }
        for professional in professionals_data
    }

    # Query to fetch appointments and join with Slot and Status tables
    appointments = (
        db.session.query(Appointment)
        .options(joinedload(Appointment.slot))  # Eager load slot details
        .options(joinedload(Appointment.status))  # Eager load status details
        .filter_by(user_id=user_id)
        .all()
    )

    # Add professional details to each appointment
    appointments_with_professional = []
    for appointment in appointments:
        professional_details = professionals_map.get(appointment.professional_id, {})
        appointments_with_professional.append({
            "appointment_id": appointment.appointment_id,
            "professional_name": f"{professional_details.get('first_name', '')} {professional_details.get('last_name', '')}",
            "specialization": professional_details.get('specialization', 'N/A'),
            "appointment_date": appointment.appointment_date,
            "slot_time": appointment.slot.slot_time,
            "status": appointment.status.status_name,
            "notes": appointment.notes
        })

    if not appointments:
        return jsonify({'message': 'No appointments found for this user!'}), 404

    return jsonify(appointments_with_professional), 200

# Fetch upcoming appointments for a professional
@appointment_routes.route('/professional/<int:professional_id>/upcoming_appointments', methods=['GET'])
def get_professional_upcoming_appointments(professional_id):
    today = datetime.now().date()

    appointments = (
        db.session.query(Appointment)
        .options(joinedload(Appointment.slot))     
        .options(joinedload(Appointment.status))   
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
        'slot_time': appt.slot.slot_time,
        'status': appt.status.status_name,
        'notes': appt.notes
    } for appt in appointments]), 200
