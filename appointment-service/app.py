from flask import Flask
from db.models import db
from config import Config
from db.models import Status, Slot, Appointment
from routes.appointment_routes import appointment_routes

app = Flask(__name__)
app.config.from_object(Config)

# Create the database tables
@app.before_request
def create_tables():
    db.create_all()
    load_initial_data()

# Load initial data into the database
def load_initial_data():
    # Check and load statuses
    if Status.query.count() == 0:
        statuses = [
            {'status_id': 1, 'status_name': 'booked'},
            {'status_id': 2, 'status_name': 'rescheduled'},
            {'status_id': 3, 'status_name': 'cancelled'}
        ]
        for status in statuses:
            db.session.add(Status(**status))
        db.session.commit()

    # Check and load slots
    if Slot.query.count() == 0:
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

# Initialize database
db.init_app(app)

# Register blueprints
app.register_blueprint(appointment_routes)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5003)
    
