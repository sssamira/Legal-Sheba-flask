from flask import Blueprint, request, jsonify
from extensions import db
from models import Appointment, User, LawyerProfile
from flask_jwt_extended import get_jwt_identity
from decorators import role_required
import json

appointments_bp = Blueprint('appointments', __name__, url_prefix='/appointments')


@appointments_bp.route('/new', methods=['POST'])
@role_required('Client')
def create_appointment():
    """Client creates an appointment with a lawyer.
    Expected JSON: { lawyer_id: int, appointment_date: str (ISO), problem_description: str }
    """
    ident = json.loads(get_jwt_identity())
    client_id = ident.get('id')

    data = request.get_json() or {}
    lawyer_id = data.get('lawyer_id')
    appointment_date = data.get('appointment_date')
    problem_description = data.get('problem_description')

    if not lawyer_id or not appointment_date:
        return jsonify({'message': 'lawyer_id and appointment_date are required'}), 400

    # check lawyer exists
    if not LawyerProfile.query.get(lawyer_id):
        return jsonify({'message': 'Lawyer not found'}), 404

    appt = Appointment(
        client_id=client_id,
        lawyer_id=lawyer_id,
        appointment_date=appointment_date,
        problem_description=problem_description,
        status='pending'
    )
    db.session.add(appt)
    db.session.commit()
    return jsonify({'message': 'Appointment created', 'appointment_id': appt.id}), 201


@appointments_bp.route('', methods=['GET'])
@role_required('Client')
def list_client_appointments():
    """List appointments for authenticated client."""
    ident = json.loads(get_jwt_identity())
    client_id = ident.get('id')

    rows = Appointment.query.filter_by(client_id=client_id).all()
    result = []
    for r in rows:
        result.append({
            'id': r.id,
            'client_id': r.client_id,
            'lawyer_id': r.lawyer_id,
            'appointment_date': r.appointment_date,
            'status': r.status,
            'problem_description': r.problem_description,
            'notes': r.notes
        })
    return jsonify(result)


@appointments_bp.route('/lawyer', methods=['GET'])
@role_required('Lawyer')
def list_lawyer_appointments():
    """List appointments for authenticated lawyer."""
    ident = json.loads(get_jwt_identity())
    user_id = ident.get('id')
    # find lawyer_profile id for this user
    lp = LawyerProfile.query.filter_by(user_id=user_id).first()
    if not lp:
        return jsonify({'message': 'Profile not found'}), 404

    rows = Appointment.query.filter_by(lawyer_id=lp.id).all()
    result = []
    for r in rows:
        result.append({
            'id': r.id,
            'client_id': r.client_id,
            'lawyer_id': r.lawyer_id,
            'appointment_date': r.appointment_date,
            'status': r.status,
            'problem_description': r.problem_description,
            'notes': r.notes
        })
    return jsonify(result)


@appointments_bp.route('/<int:appointment_id>', methods=['GET'])
@role_required('Client')
def get_appointment(appointment_id):
    """Get appointment details (client must own the appointment)."""
    ident = json.loads(get_jwt_identity())
    client_id = ident.get('id')

    appt = Appointment.query.get_or_404(appointment_id)
    if appt.client_id != client_id:
        return jsonify({'message': 'Not authorized'}), 403

    return jsonify({
        'id': appt.id,
        'client_id': appt.client_id,
        'lawyer_id': appt.lawyer_id,
        'appointment_date': appt.appointment_date,
        'status': appt.status,
        'problem_description': appt.problem_description,
        'notes': appt.notes
    })


@appointments_bp.route('/<int:appointment_id>', methods=['PUT'])
@role_required('Lawyer')
def update_appointment(appointment_id):
    """Lawyer updates status and notes for an appointment assigned to them."""
    ident = json.loads(get_jwt_identity())
    user_id = ident.get('id')
    lp = LawyerProfile.query.filter_by(user_id=user_id).first()
    if not lp:
        return jsonify({'message': 'Profile not found'}), 404

    appt = Appointment.query.get_or_404(appointment_id)
    if appt.lawyer_id != lp.id:
        return jsonify({'message': 'Not authorized'}), 403

    data = request.get_json() or {}
    if 'status' in data:
        appt.status = data.get('status')
    if 'notes' in data:
        appt.notes = data.get('notes')

    db.session.commit()
    return jsonify({'message': 'Appointment updated'})


@appointments_bp.route('/<int:appointment_id>/cancel', methods=['POST'])
@role_required('Client')
def cancel_appointment(appointment_id):
    """Client cancels their appointment."""
    ident = json.loads(get_jwt_identity())
    client_id = ident.get('id')

    appt = Appointment.query.get_or_404(appointment_id)
    if appt.client_id != client_id:
        return jsonify({'message': 'Not authorized'}), 403

    appt.status = 'cancelled'
    db.session.commit()
    return jsonify({'message': 'Appointment cancelled'})
