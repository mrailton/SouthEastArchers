from collections.abc import Sequence
from typing import cast

from flask import abort, current_app, flash, redirect, render_template, request, url_for

from app import db
from app.forms import CreateMemberForm, EditMemberForm
from app.models import Credit, Payment, Role
from app.services import MembershipService, UserService
from app.utils.decorators import permission_required

from . import bp


@bp.get("/members")
@permission_required("members.read")
def members():
    members = UserService.get_all_users()
    return render_template("admin/members.html", members=members)


@bp.get("/members/<int:user_id>")
@permission_required("members.read")
def member_detail(user_id):
    member = UserService.get_user_by_id(user_id)
    if not member:
        abort(404)
    return render_template("admin/member_detail.html", member=member)


@bp.post("/members/<int:user_id>/membership/renew")
@permission_required("members.manage_membership")
def renew_membership(user_id):
    member = UserService.get_user_by_id(user_id)
    if not member:
        abort(404)

    success, message = MembershipService.renew_membership(member)
    flash(message, "success" if success else "error")

    return redirect(url_for("admin.member_detail", user_id=user_id))


@bp.post("/members/<int:user_id>/membership/activate")
@permission_required("members.manage_membership")
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
        from app.services.mail_service import send_payment_receipt

        send_payment_receipt(member.id, payment.id)
        flash(f"Membership activated for {member.name}! Receipt email sent.", "success")
    else:
        flash(f"Membership activated for {member.name}!", "success")

    return redirect(url_for("admin.member_detail", user_id=user_id))


@bp.post("/members/<int:user_id>/activate")
@permission_required("members.activate_account")
def activate_user(user_id):
    """Activate a user account and send welcome email"""
    member = UserService.get_user_by_id(user_id)
    if not member:
        abort(404)

    if member.is_active:
        flash(f"{member.name}'s account is already active.", "warning")
        return redirect(url_for("admin.member_detail", user_id=user_id))

    member.is_active = True
    from app import db

    db.session.commit()

    # Send welcome email
    from app.services.mail_service import send_welcome_email

    try:
        send_welcome_email(user_id)
        flash(f"Account activated for {member.name}! Welcome email sent.", "success")
    except Exception as e:
        current_app.logger.error(f"Failed to send welcome email: {str(e)}")
        flash(f"Account activated for {member.name}! (Email failed to send)", "warning")

    return redirect(url_for("admin.member_detail", user_id=user_id))


@bp.get("/members/create")
@permission_required("members.create")
def create_member():
    """Display member creation form"""
    form = CreateMemberForm()
    form.roles.choices = [(r.id, r.name) for r in Role.query.order_by(Role.name)]
    return render_template("admin/create_member.html", form=form)


@bp.post("/members/create")
@permission_required("members.create")
def create_member_post():
    """Handle member creation form submission"""
    form = CreateMemberForm()
    form.roles.choices = [(r.id, r.name) for r in Role.query.order_by(Role.name)]

    if form.validate_on_submit():
        user, error = UserService.create_member(
            name=form.name.data,
            email=form.email.data,
            phone=form.phone.data,
            password=form.password.data or "changeme123",
            role_ids=form.roles.data,
            create_membership=form.create_membership.data,
            qualification=form.qualification.data if hasattr(form, "qualification") else "none",
        )

        if error:
            flash(error, "error")
            return render_template("admin/create_member.html", form=form)

    for field, errors in form.errors.items():
        for error in errors:
            flash(error, "error")

    return render_template("admin/create_member.html", form=form)


@bp.get("/members/<int:user_id>/edit")
@permission_required("members.update")
def edit_member(user_id):
    """Display member edit form"""
    member = UserService.get_user_by_id(user_id)
    if not member:
        abort(404)

    form = EditMemberForm(obj=member)

    if member.membership:
        form.membership_start_date.data = member.membership.start_date
        form.membership_expiry_date.data = member.membership.expiry_date
        form.membership_initial_credits.data = member.membership.initial_credits
        form.membership_purchased_credits.data = member.membership.purchased_credits

    form.roles.choices = [(r.id, r.name) for r in Role.query.order_by(Role.name)]
    form.roles.data = [r.id for r in cast(Sequence, member.roles)]
    return render_template("admin/edit_member.html", member=member, form=form)


@bp.post("/members/<int:user_id>/edit")
@permission_required("members.update")
def edit_member_post(user_id):
    member = UserService.get_user_by_id(user_id)
    if not member:
        abort(404)

    form = EditMemberForm(obj=member)
    form.roles.choices = [(r.id, r.name) for r in Role.query.order_by(Role.name)]

    if form.validate_on_submit():
        success, message = UserService.update_member(
            user=member,
            name=form.name.data,
            email=form.email.data,
            phone=form.phone.data,
            qualification=form.qualification.data,
            qualification_detail=form.qualification_detail.data or None,
            role_ids=form.roles.data,
            is_active=form.is_active.data,
            password=form.password.data or None,
            membership_start_date=form.membership_start_date.data,
            membership_expiry_date=form.membership_expiry_date.data,
            membership_initial_credits=form.membership_initial_credits.data,
            membership_purchased_credits=form.membership_purchased_credits.data,
        )

        flash(message, "success" if success else "error")
        if success:
            return redirect(url_for("admin.member_detail", user_id=user_id))

    for field, errors in form.errors.items():
        for error in errors:
            flash(error, "error")

    return render_template("admin/edit_member.html", member=member, form=form)


@bp.post("/members/<int:user_id>/credits/add")
@permission_required("members.manage_membership")
def add_credits(user_id):
    """Add shooting credits to a member's account"""
    member = UserService.get_user_by_id(user_id)
    if not member:
        abort(404)

    if not member.membership:
        flash("Member does not have an active membership.", "error")
        return redirect(url_for("admin.member_detail", user_id=user_id))

    try:
        quantity = int(request.form.get("quantity", 0))
        if quantity < 1:
            flash("Please enter a valid number of credits.", "error")
            return redirect(url_for("admin.member_detail", user_id=user_id))
    except ValueError:
        flash("Please enter a valid number of credits.", "error")
        return redirect(url_for("admin.member_detail", user_id=user_id))

    reason = request.form.get("reason", "").strip() or "Admin adjustment"

    # Add credits to membership
    member.membership.add_credits(quantity)

    # Create credit record (no payment associated)
    credit = Credit(
        user_id=member.id,
        amount=quantity,
        payment_id=None,
    )
    db.session.add(credit)
    db.session.commit()

    current_app.logger.info(f"Admin added {quantity} credits to user {member.id} ({member.email}). Reason: {reason}")

    flash(f"Added {quantity} credit(s) to {member.name}'s account.", "success")
    return redirect(url_for("admin.member_detail", user_id=user_id))
