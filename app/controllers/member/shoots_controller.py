from flask import render_template
from flask_login import current_user, login_required

from app.models import Shoot, User


class ShootsController:
    @login_required
    def __call__(self):
        user = current_user
        user_shoots = Shoot.query.join(Shoot.users).filter(User.id == user.id).order_by(Shoot.date.desc()).all()
        return render_template("member/shoots.html", shoots=user_shoots, user=user)
