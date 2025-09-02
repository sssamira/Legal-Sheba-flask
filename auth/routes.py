from flask import Blueprint, request, jsonify
from models import User, LawyerProfile, Specialty
from extensions import db, bcrypt
from flask_jwt_extended import create_access_token

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    f_name = data.get('f_name')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'Client')  # default = Client

    
    if User.query.filter((User.email == email)).first():
        return jsonify({'message': 'Email already exists'}), 400

   
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

    
    user = User(
        f_name=f_name,
        email=email,
        password=hashed_password,
        role=role
    )
    db.session.add(user)
    db.session.commit()

    
    import json
    identity = json.dumps({'id': user.id, 'role': user.role})
    token = create_access_token(identity=identity)

    return jsonify({
        'message': 'User created successfully',
        'user_id': user.id,
        'role': role,
        'access_token': token   # <-- added token here
    }), 201




@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    user = User.query.filter_by(email=email).first()
    if not user or not bcrypt.check_password_hash(user.password, password):
        return jsonify({'message': 'Invalid credentials'}), 401

    # Create JWT token: encode identity as JSON string
    import json
    identity = json.dumps({'id': user.id, 'role': user.role})
    token = create_access_token(identity=identity)

    return jsonify({
        'access_token': token,
        'user_id': user.id,
        'role': user.role
    })



@auth_bp.route('/user/<int:user_id>', methods=['GET'])
def view_user(user_id):
    """Return full user info. Includes lawyer profile and specialties when present."""
    user = User.query.get_or_404(user_id)

    profile = LawyerProfile.query.filter_by(user_id=user_id).first()
    profile_data = None
    if profile:
        specs = (
            db.session.query(Specialty.name)
            .filter(Specialty.lawyer_id == profile.id)
            .all()
        )
        specialties = [s.name for s in specs]
        profile_data = {
            'profile_id': profile.id,
            'experience': profile.experience,
            'location': profile.location,
            'court_of_practice': profile.court_of_practice,
            'availability_details': profile.availability_details,
            'v_hour': profile.v_hour,
            'specialties': specialties
        }

    return jsonify({
        'id': user.id,
        'f_name': user.f_name,
        'email': user.email,
        'role': user.role,
        'created_at': user.created_at,
        'profile': profile_data
    })

