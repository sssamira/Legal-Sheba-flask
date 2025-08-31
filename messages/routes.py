from flask import Blueprint, request, jsonify, send_from_directory, current_app
from extensions import db
from models import Message, Appointment, User
from flask_jwt_extended import get_jwt_identity
from decorators import role_required
import json
import os

messages_bp = Blueprint('messages', __name__, url_prefix='/messages')


@messages_bp.route('/send', methods=['POST'])
def send_message():
    """Send a message related to an appointment.

    Expected JSON: { appointment_id, receiver_id, message_text, file_path (optional), file_type (optional) }
    Sender is derived from JWT.
    """
    ident = json.loads(get_jwt_identity())
    sender_id = ident.get('id')

    data = request.get_json() or {}
    appointment_id = data.get('appointment_id')
    receiver_id = data.get('receiver_id')
    message_text = data.get('message_text')
    file_path = data.get('file_path')
    file_type = data.get('file_type')

    if not appointment_id or not receiver_id:
        return jsonify({'message': 'appointment_id and receiver_id are required'}), 400

    appt = Appointment.query.get(appointment_id)
    if not appt:
        return jsonify({'message': 'Appointment not found'}), 404

    # ensure sender or receiver is part of this appointment
    if sender_id not in (appt.client_id, appt.lawyer_id) or receiver_id not in (appt.client_id, appt.lawyer_id):
        return jsonify({'message': 'Sender or receiver not part of appointment'}), 403

    msg = Message(
        appointment_id=appointment_id,
        sender_id=sender_id,
        receiver_id=receiver_id,
        message_text=message_text,
        file_path=file_path,
        file_type=file_type,
        timestamp=None,
        is_read=False
    )
    db.session.add(msg)
    db.session.commit()
    return jsonify({'message': 'Message sent', 'message_id': msg.id}), 201


@messages_bp.route('/appointment/<int:appointment_id>', methods=['GET'])
def list_messages(appointment_id):
    """List messages for an appointment. Requester must be participant."""
    ident = json.loads(get_jwt_identity())
    user_id = ident.get('id')

    appt = Appointment.query.get_or_404(appointment_id)
    if user_id not in (appt.client_id, appt.lawyer_id):
        return jsonify({'message': 'Not authorized'}), 403

    msgs = Message.query.filter_by(appointment_id=appointment_id).order_by(Message.id.asc()).all()
    result = []
    for m in msgs:
        result.append({
            'id': m.id,
            'appointment_id': m.appointment_id,
            'sender_id': m.sender_id,
            'receiver_id': m.receiver_id,
            'message_text': m.message_text,
            'file_path': m.file_path,
            'file_type': m.file_type,
            'timestamp': m.timestamp,
            'is_read': m.is_read
        })
    return jsonify(result)


@messages_bp.route('/<int:message_id>/read', methods=['POST'])
def mark_read(message_id):
    """Mark a message as read (only the receiver can mark)."""
    ident = json.loads(get_jwt_identity())
    user_id = ident.get('id')

    msg = Message.query.get_or_404(message_id)
    if msg.receiver_id != user_id:
        return jsonify({'message': 'Not authorized'}), 403

    msg.is_read = True
    db.session.commit()
    return jsonify({'message': 'Marked as read'})


@messages_bp.route('/file/<path:filename>', methods=['GET'])
def download_file(filename):
    """Serve uploaded files from configured upload folder. Ensure proper auth checks where needed."""
    upload_folder = current_app.config.get('UPLOAD_FOLDER') or os.path.join(os.getcwd(), 'uploads')
    return send_from_directory(upload_folder, filename, as_attachment=True)
