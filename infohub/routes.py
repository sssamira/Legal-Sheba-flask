from flask import Blueprint, request, jsonify, abort
from extensions import db
from models import InfoHub
from datetime import datetime

infohub_bp = Blueprint('infohub', __name__, url_prefix='/infohub')


@infohub_bp.route('/titles', methods=['GET'])
def get_titles():
    """Return a list of all infohub titles with id and category."""
    items = InfoHub.query.order_by(InfoHub.date.desc()).all()
    result = [{'id': i.id, 'title': i.title, 'category': i.category, 'date': i.date} for i in items]
    return jsonify(result), 200


@infohub_bp.route('/', methods=['GET'])
def get_all():
    """Return full info entries (id, title, content, category, date)."""
    items = InfoHub.query.order_by(InfoHub.date.desc()).all()
    result = [{'id': i.id, 'title': i.title, 'content': i.content, 'category': i.category, 'date': i.date} for i in items]
    return jsonify(result), 200


@infohub_bp.route('/', methods=['POST'])
def create_info():
    """Create a new InfoHub entry. Expects JSON with title, content, category, optional date."""
    data = request.get_json() or {}
    title = data.get('title')
    content = data.get('content')
    category = data.get('category')
    date_str = data.get('date')

    if not title or not content or not category:
        return jsonify({'error': 'title, content and category are required'}), 400

    if date_str:
        # try to parse ISO-like input and store as 'YYYY-MM-DD HH:MM'
        try:
            dt = datetime.fromisoformat(date_str)
            date = dt.strftime("%Y-%m-%d %H:%M")
        except ValueError:
            # if parsing fails, accept the raw string (caller is responsible for format)
            date = date_str
    else:
        date = datetime.utcnow().strftime("%Y-%m-%d %H:%M")

    entry = InfoHub(title=title, content=content, category=category, date=date)
    db.session.add(entry)
    db.session.commit()

    return jsonify({'id': entry.id, 'title': entry.title, 'category': entry.category, 'date': entry.date}), 201


@infohub_bp.route('/titles/<string:category>', methods=['GET'])
def get_titles_by_category(category):
    """Return titles filtered by category."""
    items = InfoHub.query.filter_by(category=category).order_by(InfoHub.date.desc()).all()
    result = [{'id': i.id, 'title': i.title, 'date': i.date} for i in items]
    return jsonify(result), 200


@infohub_bp.route('/contents/<int:item_id>', methods=['GET'])
def get_content_by_id(item_id):
    """Return the content (and metadata) for an InfoHub entry by id."""
    item = InfoHub.query.get(item_id)
    if not item:
        return jsonify({'error': 'not found'}), 404
    result = {'id': item.id, 'title': item.title, 'content': item.content, 'category': item.category, 'date': item.date}
    return jsonify(result), 200
