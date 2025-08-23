import json
from functools import wraps
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from flask import jsonify

def role_required(*roles):
    """
    Protect routes so only users with allowed roles can access.
    Usage: @role_required('Lawyer', 'Admin')
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()  # ensures JWT is valid
            identity_str = get_jwt_identity()  # this is a JSON string
            user = json.loads(identity_str)    # decode to dict

            if user['role'] not in roles:
                return jsonify({'message': 'Access forbidden: insufficient role'}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator
