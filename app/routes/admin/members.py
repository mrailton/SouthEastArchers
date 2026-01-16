from datetime import datetime

from flask import abort, current_app, flash, redirect, render_template, request, url_for

from app.forms import CreateMemberForm, EditMemberForm
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
    form = CreateMemberForm()

    if form.validate_on_submit():
        user, error = UserService.create_member(
            name=form.name.data,
            email=form.email.data,
            phone=form.phone.data,
            password=form.password.data or "changeme123",
            is_admin=form.is_admin.data,
            create_membership=form.create_membership.data,
        )

        if error:
            flash(error, "error")
            return render_template("admin/create_member.html", form=form)

        if user:
            flash(f"Member {user.name} created successfully!", "success")
            return redirect(url_for("admin.members"))

    for field, errors in form.errors.items():
        for error in errors:
            flash(error, "error")

    return render_template("admin/create_member.html", form=form)


@bp.route("/members/<int:user_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_member(user_id):
    member = UserService.get_user_by_id(user_id)
    if not member:
        abort(404)

    form = EditMemberForm(obj=member)

    if request.method == "GET" and member.membership:
        form.membership_start_date.data = member.membership.start_date
        form.membership_expiry_date.data = member.membership.expiry_date
        form.membership_credits.data = member.membership.credits

    if form.validate_on_submit():
        success, message = UserService.update_member(
            user=member,
            name=form.name.data,
            email=form.email.data,
            phone=form.phone.data,
            is_admin=form.is_admin.data,
            is_active=form.is_active.data,
            password=form.password.data or None,
            membership_start_date=form.membership_start_date.data,
            membership_expiry_date=form.membership_expiry_date.data,
            membership_credits=form.membership_credits.data,
        )

        flash(message, "success" if success else "error")
        if success:
            return redirect(url_for("admin.member_detail", user_id=user_id))

    for field, errors in form.errors.items():
        for error in errors:
            flash(error, "error")

    return render_template("admin/edit_member.html", member=member, form=form)
