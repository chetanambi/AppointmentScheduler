from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import requests
from config import APPOINTMENT_SERVICE_URL, PROFESSIONAL_SERVICE_URL
from utils.security import is_logged_in

appointment_routes = Blueprint('appointment_routes', __name__)

@appointment_routes.route('/professional/<int:professional_id>/availability', methods=['GET', 'POST'])
def show_availability(professional_id):
    if not is_logged_in():
        flash('Please log in to access this page.', 'error')
        return redirect(url_for('user_routes.login'))

    if request.method == 'POST':
        appointment_date = request.form['appointment_date']
        response = requests.get(
            f"{APPOINTMENT_SERVICE_URL}/professional/{professional_id}/availability",
            params={'appointment_date': appointment_date}
        )
        available_slots = response.json().get('available_slots', []) if response.status_code == 200 else []
        response = requests.get(f"{PROFESSIONAL_SERVICE_URL}/professional/{professional_id}")
        professional_fname = response.json()['first_name']
        professional_lname = response.json()['last_name']

        return render_template('available_slots.html',
                               professional_id=professional_id,
                               available_slots=available_slots,
                               appointment_date=appointment_date,
                               professional_fname=professional_fname,
                               professional_lname=professional_lname)

    return render_template('availability_form.html', professional_id=professional_id)

@appointment_routes.route('/appointment/book', methods=['POST'])
def book_appointment():
    if not is_logged_in():
        flash('Please log in to access this page.', 'error')
        return redirect(url_for('user_routes.login'))

    user_id = session['user_id']
    professional_id = request.form['professional_id']
    appointment_date = request.form['appointment_date']
    appointment_slot_id = request.form['slot_id']
    notes = request.form.get('notes', '')

    data = {
        'user_id': user_id,
        'professional_id': professional_id,
        'appointment_date': appointment_date,
        'appointment_slot_id': appointment_slot_id,
        'notes': notes
    }

    response = requests.post(f"{APPOINTMENT_SERVICE_URL}/appointment/book", json=data)
    if response.status_code == 201:
        flash('Appointment booked successfully!', 'success')
    else:
        flash(response.json().get('message', 'Error booking appointment!'), 'error')

    return redirect(url_for('professional_routes.list_professionals'))

@appointment_routes.route('/appointment/<int:appointment_id>/cancel', methods=['POST'])
def cancel_appointment(appointment_id):
    if not is_logged_in():
        flash('Please log in to access this page.', 'error')
        return redirect(url_for('user_routes.login'))

    response = requests.delete(f"{APPOINTMENT_SERVICE_URL}/appointment/{appointment_id}/cancel")
    print("response", response)
    if response.status_code == 200:
        flash('Appointment cancelled successfully!', 'success')
    else:
        flash(response.json().get('message', 'Error canceling appointment!'), 'error')

    return redirect(url_for('user_routes.profile', user_id=session['user_id']))

# Route to fetch appointment history for a user
@appointment_routes.route('/user/<int:user_id>/appointments', methods=['GET'])
def get_user_appointments(user_id):
    if not is_logged_in():
        flash('Please log in to access this page.', 'error')
        return redirect(url_for('user_routes.login'))

    response = requests.get(f"{APPOINTMENT_SERVICE_URL}/user/{user_id}/appointments")
    appointments = response.json() if response.status_code == 200 else []

    return render_template('appointment_history.html', appointments=appointments)