from flask import Blueprint, request, jsonify
from db.models import db, Professional

professional_bp = Blueprint('professional_bp', __name__)

@professional_bp.route('/professional/register', methods=['POST'])
def register():
    data = request.json
    if Professional.query.filter_by(email=data['email']).first():
        return jsonify({'message': 'Email already registered!'}), 400

    new_professional = Professional(
        first_name=data['first_name'],
        last_name=data['last_name'],
        email=data['email'],
        phone=data['phone'],
        specialization=data['specialization']
    )
    try:
        db.session.add(new_professional)
        db.session.commit()
        return jsonify({'message': 'Professional registered successfully!'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Error registering professional', 'error': str(e)}), 500

@professional_bp.route('/professional/<int:professional_id>', methods=['GET'])
def get_professional(professional_id):
    professional = Professional.query.get(professional_id)
    if professional:
        return jsonify({
            'professional_id': professional.professional_id,
            'first_name': professional.first_name,
            'last_name': professional.last_name,
            'email': professional.email,
            'phone': professional.phone,
            'specialization': professional.specialization,
            'created_at': professional.created_at,
            'updated_at': professional.updated_at
        }), 200
    return jsonify({'message': 'Professional not found!'}), 404

@professional_bp.route('/professional/<int:professional_id>', methods=['PUT'])
def update_professional(professional_id):
    data = request.json
    professional = Professional.query.get(professional_id)
    if not professional:
        return jsonify({'message': 'Professional not found!'}), 404

    professional.first_name = data.get('first_name', professional.first_name)
    professional.last_name = data.get('last_name', professional.last_name)
    professional.email = data.get('email', professional.email)
    professional.phone = data.get('phone', professional.phone)
    professional.specialization = data.get('specialization', professional.specialization)

    db.session.commit()
    return jsonify({'message': 'Professional profile updated successfully!'}), 200

@professional_bp.route('/professional/<int:professional_id>', methods=['DELETE'])
def delete_professional(professional_id):
    professional = Professional.query.get(professional_id)
    if not professional:
        return jsonify({'message': 'Professional not found!'}), 404

    db.session.delete(professional)
    db.session.commit()
    return jsonify({'message': 'Professional account deleted successfully!'}), 200

# Fetch all professionals
@professional_bp.route('/professionals', methods=['GET'])
def get_all_professionals():
    professionals = Professional.query.all()
    return jsonify([
        {
            'professional_id': p.professional_id,
            'first_name': p.first_name,
            'last_name': p.last_name,
            'specialization': p.specialization,
            'email': p.email,
            'phone': p.phone,
            'created_at': p.created_at,
            'updated_at': p.updated_at
        } for p in professionals
    ]), 200
