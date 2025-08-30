from flask import Blueprint, request, jsonify
from models import User
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

