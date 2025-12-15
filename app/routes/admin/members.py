from datetime import datetime

from flask import abort, current_app, flash, redirect, render_template, request, url_for

from app.models import Payment
from app.services import MembershipService, UserService
from app.utils.email import send_payment_receipt

from . import admin_required, bp


@bp.route("/members")
@admin_required
def members():
    members = UserService.get_all_users()
    return render_template("admin/members.html", members=members)


@bp.route("/members/<int:user_id>")
@admin_required
def member_detail(user_id):
    member = UserService.get_user_by_id(user_id)
    if not member:
        abort(404)
    return render_template("admin/member_detail.html", member=member)


@bp.route("/members/<int:user_id>/membership/renew", methods=["POST"])
@admin_required
def renew_membership(user_id):
    member = UserService.get_user_by_id(user_id)
    if not member:
        abort(404)

    success, message = MembershipService.renew_membership(member)
    flash(message, "success" if success else "error")

    return redirect(url_for("admin.member_detail", user_id=user_id))


@bp.route("/members/<int:user_id>/membership/activate", methods=["POST"])
@admin_required
def activate_membership(user_id):
    member = UserService.get_user_by_id(user_id)
    if not member:
        abort(404)

    success, message = MembershipService.activate_membership(member)

    if not success:
        flash(message, "error")
        return redirect(url_for("admin.member_detail", user_id=user_id))

    payment = Payment.query.filter_by(
        user_id=user_id,
        payment_type="membership",
        status="completed",
    ).first()

    if payment:
        try:
            send_payment_receipt(member, payment, member.membership)
            flash(f"Membership activated for {member.name}! Receipt email sent.", "success")
        except Exception as e:
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

        user, error = UserService.create_member(
            name=request.form.get("name"),
            email=request.form.get("email"),
            date_of_birth=dob,
            phone=request.form.get("phone"),
            password=request.form.get("password", "changeme123"),
            is_admin=request.form.get("is_admin") == "on",
            create_membership=request.form.get("create_membership") == "on",
        )

        if error:
            flash(error, "error")
            return render_template("admin/create_member.html")

        flash(f"Member {user.name} created successfully!", "success")
        return redirect(url_for("admin.members"))

    return render_template("admin/create_member.html")


@bp.route("/members/<int:user_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_member(user_id):
    member = UserService.get_user_by_id(user_id)
    if not member:
        abort(404)

    if request.method == "POST":
        try:
            dob_str = request.form.get("date_of_birth")
            dob = datetime.strptime(dob_str, "%Y-%m-%d").date()
        except (ValueError, AttributeError):
            flash("Invalid date format.", "error")
            return render_template("admin/edit_member.html", member=member)

        # Parse optional membership fields
        membership_start = None
        membership_expiry = None
        membership_credits = None

        if member.membership:
            try:
                start_str = request.form.get("membership_start_date")
                expiry_str = request.form.get("membership_expiry_date")
                credits_str = request.form.get("membership_credits")

                if start_str:
                    membership_start = datetime.strptime(start_str, "%Y-%m-%d").date()
                if expiry_str:
                    membership_expiry = datetime.strptime(expiry_str, "%Y-%m-%d").date()
                if credits_str:
                    membership_credits = int(credits_str)
            except (ValueError, AttributeError) as e:
                flash(f"Error parsing membership data: {str(e)}", "error")
                return render_template("admin/edit_member.html", member=member)

        success, message = UserService.update_member(
            user=member,
            name=request.form.get("name"),
            email=request.form.get("email"),
            date_of_birth=dob,
            phone=request.form.get("phone"),
            is_admin=request.form.get("is_admin") == "on",
            is_active=request.form.get("is_active") == "on",
            password=request.form.get("password") or None,
            membership_start_date=membership_start,
            membership_expiry_date=membership_expiry,
            membership_credits=membership_credits,
        )

        flash(message, "success" if success else "error")
        if success:
            return redirect(url_for("admin.member_detail", user_id=user_id))

    return render_template("admin/edit_member.html", member=member)
