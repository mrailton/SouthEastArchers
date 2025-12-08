from datetime import date, datetime, timedelta

from flask import flash, redirect, render_template, request, url_for

from app import db
from app.models import Membership, Payment, User
from app.services import MembershipService
from app.utils.email import send_payment_receipt

from . import admin_required, bp


@bp.route("/members")
@admin_required
def members():
    members = User.query.order_by(User.name).all()
    return render_template("admin/members.html", members=members)


@bp.route("/members/<int:user_id>")
@admin_required
def member_detail(user_id):
    member = db.session.get(User, user_id)
    if not member:
        from flask import abort

        abort(404)
    return render_template("admin/member_detail.html", member=member)


@bp.route("/members/<int:user_id>/membership/renew", methods=["POST"])
@admin_required
def renew_membership(user_id):
    member = db.session.get(User, user_id)
    if not member:
        from flask import abort

        abort(404)

    success, message = MembershipService.renew_membership(member)
    flash(message, "success" if success else "error")

    return redirect(url_for("admin.member_detail", user_id=user_id))


@bp.route("/members/<int:user_id>/membership/activate", methods=["POST"])
@admin_required
def activate_membership(user_id):
    member = db.session.get(User, user_id)
    if not member:
        from flask import abort

        abort(404)

    success, message = MembershipService.activate_membership(member)

    if not success:
        flash(message, "error")
        return redirect(url_for("admin.member_detail", user_id=user_id))

    pending_payment = Payment.query.filter_by(
        user_id=user_id,
        payment_type="membership",
        status="paid",
    ).first()

    if pending_payment:
        try:
            send_payment_receipt(member, pending_payment, member.membership)
            flash(f"Membership activated for {member.name}! Receipt email sent.", "success")
        except Exception as e:
            from flask import current_app

            current_app.logger.error(f"Failed to send receipt email: {str(e)}")
            flash(f"Membership activated for {member.name}! (Email failed to send)", "warning")
    else:
        flash(f"Membership activated for {member.name}!", "success")

    return redirect(url_for("admin.member_detail", user_id=user_id))


@bp.route("/members/create", methods=["GET", "POST"])
@admin_required
def create_member():
    if request.method == "POST":
        try:
            dob_str = request.form.get("date_of_birth")
            dob = datetime.strptime(dob_str, "%Y-%m-%d").date()
        except (ValueError, AttributeError):
            flash("Invalid date format.", "error")
            return render_template("admin/create_member.html")

        existing = User.query.filter_by(email=request.form.get("email")).first()
        if existing:
            flash("Email already registered.", "error")
            return render_template("admin/create_member.html")

        user = User(
            name=request.form.get("name"),
            email=request.form.get("email"),
            phone=request.form.get("phone"),
            date_of_birth=dob,
            is_admin=request.form.get("is_admin") == "on",
        )
        user.set_password(request.form.get("password", "changeme123"))

        db.session.add(user)
        db.session.flush()

        if request.form.get("create_membership") == "on":
            membership = Membership(
                user_id=user.id,
                start_date=date.today(),
                expiry_date=date.today() + timedelta(days=365),
                credits=20,
                status="active",
            )
            db.session.add(membership)

        db.session.commit()
        flash(f"Member {user.name} created successfully!", "success")
        return redirect(url_for("admin.members"))

    return render_template("admin/create_member.html")


@bp.route("/members/<int:user_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_member(user_id):
    member = db.session.get(User, user_id)
    if not member:
        from flask import abort

        abort(404)

    if request.method == "POST":
        try:
            dob_str = request.form.get("date_of_birth")
            dob = datetime.strptime(dob_str, "%Y-%m-%d").date()
        except (ValueError, AttributeError):
            flash("Invalid date format.", "error")
            return render_template("admin/edit_member.html", member=member)

        member.name = request.form.get("name")
        member.email = request.form.get("email")
        member.phone = request.form.get("phone")
        member.date_of_birth = dob
        member.is_admin = request.form.get("is_admin") == "on"
        member.is_active = request.form.get("is_active") == "on"

        new_password = request.form.get("password")
        if new_password:
            member.set_password(new_password)

        if member.membership:
            try:
                start_date_str = request.form.get("membership_start_date")
                expiry_date_str = request.form.get("membership_expiry_date")
                credits = request.form.get("membership_credits")

                if start_date_str:
                    member.membership.start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
                if expiry_date_str:
                    member.membership.expiry_date = datetime.strptime(expiry_date_str, "%Y-%m-%d").date()
                if credits:
                    member.membership.credits = int(credits)
            except (ValueError, AttributeError) as e:
                flash(f"Error updating membership: {str(e)}", "error")

        db.session.commit()
        flash(f"Member {member.name} updated successfully!", "success")
        return redirect(url_for("admin.member_detail", user_id=user_id))

    return render_template("admin/edit_member.html", member=member)
