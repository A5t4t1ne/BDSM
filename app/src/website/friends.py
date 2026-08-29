"""Friend list: add someone by username, they confirm."""

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from loguru import logger
from werkzeug import Response

from . import db
from .models import Friendship, FriendshipStatus, User

friends = Blueprint("friends", __name__)


@friends.route("/friends")
@login_required
def index() -> str:
    """The friend list, plus requests waiting in either direction."""
    incoming = Friendship.query.filter_by(
        addressee_id=current_user.id, status=FriendshipStatus.PENDING
    ).all()
    outgoing = Friendship.query.filter_by(
        requester_id=current_user.id, status=FriendshipStatus.PENDING
    ).all()

    accepted = Friendship.query.filter(
        Friendship.status == FriendshipStatus.ACCEPTED,
        db.or_(
            Friendship.requester_id == current_user.id,
            Friendship.addressee_id == current_user.id,
        ),
    ).all()
    # the remove button needs the row id, keyed by the other user
    friendship_ids = {
        (f.addressee_id if f.requester_id == current_user.id else f.requester_id): f.id
        for f in accepted
    }

    return render_template(
        "friends.html",
        user=current_user,
        friends=current_user.friends(),
        friendship_ids=friendship_ids,
        incoming=incoming,
        outgoing=outgoing,
    )


@friends.route("/friends/add", methods=["POST"])
@login_required
def add() -> Response:
    """Send a friend request to the user with the given name."""
    username = (request.form.get("username") or "").strip()
    other = User.find_by_username(username)

    if other is None:
        # Deliberately explicit: you have to know the exact name to add someone,
        # so this leaks nothing that person did not already share with you.
        flash(f"No user called '{username}'", category="error")
    elif other.id == current_user.id:
        flash("You cannot add yourself", category="error")
    else:
        existing = Friendship.between(current_user.id, other.id)
        if existing and existing.status == FriendshipStatus.ACCEPTED:
            flash(f"You are already friends with {other.username}", category="error")
        elif existing and existing.requester_id == current_user.id:
            flash(f"You already asked {other.username}", category="error")
        elif existing:
            # they asked first -- treat this as accepting
            existing.status = FriendshipStatus.ACCEPTED
            db.session.commit()
            flash(f"You and {other.username} are now friends", category="success")
        else:
            db.session.add(
                Friendship(
                    requester_id=current_user.id,
                    addressee_id=other.id,
                    status=FriendshipStatus.PENDING,
                )
            )
            db.session.commit()
            logger.info(f"user {current_user.id} sent a friend request to {other.id}")
            flash(f"Friend request sent to {other.username}", category="success")

    return redirect(url_for("friends.index"))


@friends.route("/friends/<int:friendship_id>/accept", methods=["POST"])
@login_required
def accept(friendship_id: int) -> Response:
    """Accept a request addressed to you."""
    friendship = Friendship.query.filter_by(
        id=friendship_id, addressee_id=current_user.id, status=FriendshipStatus.PENDING
    ).first()

    if friendship is None:
        flash("That request no longer exists", category="error")
    else:
        friendship.status = FriendshipStatus.ACCEPTED
        db.session.commit()
        flash(f"You and {friendship.requester.username} are now friends", category="success")

    return redirect(url_for("friends.index"))


@friends.route("/friends/<int:friendship_id>/remove", methods=["POST"])
@login_required
def remove(friendship_id: int) -> Response:
    """Decline a request, withdraw your own, or unfriend someone.

    All three are the same operation on the same row, and either side may do it.
    """
    friendship = Friendship.query.filter(
        Friendship.id == friendship_id,
        db.or_(
            Friendship.requester_id == current_user.id,
            Friendship.addressee_id == current_user.id,
        ),
    ).first()

    if friendship is None:
        flash("That request no longer exists", category="error")
    else:
        db.session.delete(friendship)
        db.session.commit()
        flash("Removed", category="success")

    return redirect(url_for("friends.index"))
