from flask import Blueprint, jsonify, render_template
from sqlalchemy import func
from app.models import Project, User

api = Blueprint("api", __name__)

@api.route("/api/users", methods=["GET"])
def get_users():
    users = User.query.all()
    return jsonify([
        {
            "id": u.id,
            "full_name": u.full_name,
            "email": u.email,
            "title": u.title,
            "location": u.location
        }
        for u in users
    ])

@api.route("/api/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify({
        "id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "title": user.title,
        "location": user.location
    })