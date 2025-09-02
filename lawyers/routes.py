from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity
from extensions import db
from models import LawyerProfile, User, Specialty
from decorators import role_required

lawyers_bp = Blueprint('lawyers', __name__, url_prefix='/lawyers')



@lawyers_bp.route('', methods=['GET'])
def search_lawyers():
    specialty_q = request.args.get('specialty')
    location_q = request.args.get('location')

    # base join to get user fields
    q = db.session.query(LawyerProfile, User).join(
        User, User.id == LawyerProfile.user_id
    )

    if location_q:
        q = q.filter(LawyerProfile.location.ilike(f"%{location_q}%"))

    # if specialty filter is present, join specialties and filter by name
    if specialty_q:
        q = q.join(Specialty, Specialty.lawyer_id == LawyerProfile.id).filter(
            Specialty.name.ilike(f"%{specialty_q}%")
        )

    rows = q.all()

    # gather specialties for all returned profiles in one shot
    profile_ids = list({lp.id for (lp, _) in rows})
    specs_map = {pid: [] for pid in profile_ids}
    if profile_ids:
        specs = (
            db.session.query(Specialty)
            .filter(Specialty.lawyer_id.in_(profile_ids))
            .all()
        )
        for s in specs:
            specs_map[s.lawyer_id].append(s.name)

    result = []
    for lp, usr in rows:
        result.append({
            "id": lp.id,                        
            "user_id": lp.user_id,
            "name": usr.f_name,                 
            "email": usr.email,                 
            "experience": lp.experience,
            "location": lp.location,
            "court_of_practice": lp.court_of_practice,
            "availability_details": lp.availability_details,
            "v_hour": lp.v_hour,
            "specialties": specs_map.get(lp.id, [])
        })

    return jsonify(result)


@lawyers_bp.route('/profile', methods=['POST'])
@role_required('Lawyer')
def create_profile():
    import json
    ident = json.loads(get_jwt_identity())   # decode JSON string
    user_id = ident['id']

    # one profile per lawyer
    if LawyerProfile.query.filter_by(user_id=user_id).first():
        return jsonify({"message": "Profile already exists"}), 400

    data = request.get_json() or {}

    profile = LawyerProfile(
        user_id=user_id,
        experience=data.get('experience'),
        location=data.get('location'),
        court_of_practice=data.get('court_of_practice'),
        availability_details=data.get('availability_details'),
        v_hour=data.get('v_hour')
    )
    db.session.add(profile)
    db.session.flush()  
    names = []
    for n in data.get('specialties', []):
        if isinstance(n, str):
            n = n.strip()
            if n and n not in names:
                names.append(n)

    for name in names:
        db.session.add(Specialty(lawyer_id=profile.id, name=name))

    db.session.commit()
    return jsonify({'message': 'Profile created', 'profile_id': profile.id}), 201



@lawyers_bp.route('/profile/<int:lawyer_id>', methods=['PUT'])
@role_required('Lawyer')
def update_profile(lawyer_id):
    ident = get_jwt_identity()
    user_id = ident['id']

    profile = LawyerProfile.query.get_or_404(lawyer_id)
    if profile.user_id != user_id:
        return jsonify({"message": "Not authorized"}), 403

    data = request.get_json() or {}

    profile.experience = data.get('experience', profile.experience)
    profile.location = data.get('location', profile.location)
    profile.court_of_practice = data.get('court_of_practice', profile.court_of_practice)
    profile.availability_details = data.get('availability_details', profile.availability_details)
    profile.v_hour = data.get('v_hour', profile.v_hour)

    if 'specialties' in data:
        # replace all specialties for this lawyer
        Specialty.query.filter_by(lawyer_id=profile.id).delete()
        names = []
        for n in data.get('specialties') or []:
            if isinstance(n, str):
                n = n.strip()
                if n and n not in names:
                    names.append(n)
        for name in names:
            db.session.add(Specialty(lawyer_id=profile.id, name=name))

    db.session.commit()
    return jsonify({'message': 'Profile updated'})


# -------------------------
# View ONE Lawyer Profile by lawyer_id (public)
#   GET /lawyers/<lawyer_id>
# -------------------------
@lawyers_bp.route('/<int:lawyer_id>', methods=['GET'])
def view_profile(lawyer_id):
    profile = LawyerProfile.query.get_or_404(lawyer_id)
    user = User.query.get(profile.user_id)

    specs = (
        db.session.query(Specialty.name)
        .filter(Specialty.lawyer_id == profile.id)
        .all()
    )
    specialties = [s.name for s in specs]

    return jsonify({
        "id": profile.id,
        "user_id": profile.user_id,
        "name": user.f_name if user else None,
        "email": user.email if user else None,
        "experience": profile.experience,
        "location": profile.location,
        "court_of_practice": profile.court_of_practice,
        "availability_details": profile.availability_details,
        "v_hour": profile.v_hour,
        "specialties": specialties
    })



@lawyers_bp.route('/profile/exists/<int:user_id>', methods=['GET'])
def check_profile_exists(user_id):
    """Public endpoint: return whether the given user_id (lawyer) has created a profile.

    Response JSON:
        { "has_profile": bool, "profile_id": int | None }
    """
    profile = LawyerProfile.query.filter_by(user_id=user_id).first()
    if profile:
        return jsonify({'has_profile': True, 'profile_id': profile.id})
    return jsonify({'has_profile': False, 'profile_id': None})


@lawyers_bp.route('/by_user/<int:user_id>', methods=['GET'])
def view_by_user(user_id):
    """Return combined lawyer info given a user_id (public).

    This joins `users` and `lawyer_profiles` and includes specialties.
    """
    profile = LawyerProfile.query.filter_by(user_id=user_id).first_or_404()
    user = User.query.get(user_id)

    specs = (
        db.session.query(Specialty.name)
        .filter(Specialty.lawyer_id == profile.id)
        .all()
    )
    specialties = [s.name for s in specs]

    return jsonify({
        "id": profile.id,
        "profile_id": profile.id,
        "user_id": profile.user_id,
        "name": user.f_name if user else None,
        "email": user.email if user else None,
        "experience": profile.experience,
        "location": profile.location,
        "court_of_practice": profile.court_of_practice,
        "availability_details": profile.availability_details,
        "v_hour": profile.v_hour,
        "specialties": specialties
    })
