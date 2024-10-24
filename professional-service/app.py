from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone

app = Flask(__name__)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:password@localhost/professionals'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# Professional model
class Professional(db.Model):
    __tablename__ = 'professionals'
    
    professional_id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    specialization = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


# Create the database tables
@app.before_request
def create_tables():
    db.create_all()


# Register a new professional
@app.route('/professional/register', methods=['POST'])
def register_professional():
    data = request.json
    new_professional = Professional(
        first_name=data['first_name'],
        last_name=data['last_name'],
        specialization=data['specialization'],
        email=data['email'],
        phone=data['phone']
    )
    db.session.add(new_professional)
    db.session.commit()
    return jsonify({'message': 'Professional registered successfully!'}), 201


# Delete a professional profile
@app.route('/professional/<int:professional_id>', methods=['DELETE'])
def delete_professional(professional_id):
    professional = Professional.query.get(professional_id)
    if not professional:
        return jsonify({'message': 'Professional not found!'}), 404

    db.session.delete(professional)
    db.session.commit()
    return jsonify({'message': 'Professional profile deleted successfully!'}), 200


# Fetch professional profile
@app.route('/professional/<int:professional_id>', methods=['GET'])
def get_professional(professional_id):
    professional = Professional.query.get(professional_id)
    if not professional:
        return jsonify({'message': 'Professional not found!'}), 404

    return jsonify({
        'professional_id': professional.professional_id,
        'first_name': professional.first_name,
        'last_name': professional.last_name,
        'specialization': professional.specialization,
        'email': professional.email,
        'phone': professional.phone,
        'created_at': professional.created_at,
        'updated_at': professional.updated_at
    }), 200


# Fetch professional availability
@app.route('/professional/<int:professional_id>/availability', methods=['GET'])
def get_availability(professional_id):
    professional = Professional.query.get(professional_id)
    if not professional:
        return jsonify({'message': 'Professional not found!'}), 404

    return jsonify({
        'professional_id': professional.professional_id,
        'available_slots': professional.available_slots
    }), 200


if __name__ == '__main__':
    app.run(debug=True, port=5002)
