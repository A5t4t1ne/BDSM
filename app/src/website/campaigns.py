"""Campaigns: create one, invite people to it by username.

Deliberately minimal. The pieces that later features will hang off are the
membership row (which carries a role) and the campaign detail page, so adding
sessions, notes or a hero roster should not require reworking any of this.
"""

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from loguru import logger
from werkzeug import Response

from . import db, limiter
from .models import (
    Campaign,
    CampaignMembership,
    CampaignRole,
    Friendship,
    FriendshipStatus,
    MembershipStatus,
    User,
)

campaigns = Blueprint("campaigns", __name__)

MAX_NAME_LENGTH = 100
MAX_DESCRIPTION_LENGTH = 2000


def _add_member(campaign: Campaign, user: User, status: MembershipStatus) -> None:
    """Attach a user to a campaign as a player."""
    db.session.add(
        CampaignMembership(
            campaign_id=campaign.id,
            user_id=user.id,
            role=CampaignRole.PLAYER,
            status=status,
        )
    )
    db.session.commit()


def _visible_campaign(campaign_id: int) -> Campaign:
    """Load a campaign the current user is involved in, or 404.

    Someone who has only been invited can see the campaign, so they know what
    they are being asked to join.
    """
    campaign = db.session.get(Campaign, campaign_id)
    if campaign is None or campaign.membership_of(current_user.id) is None:
        abort(404)
    return campaign


@campaigns.route("/campaigns")
@login_required
def index() -> str:
    """Campaigns you are in, and invitations waiting for you."""
    invites = (
        CampaignMembership.query.filter_by(
            user_id=current_user.id, status=MembershipStatus.INVITED
        )
        .join(Campaign)
        .order_by(Campaign.name)
        .all()
    )
    return render_template(
        "campaigns.html",
        user=current_user,
        campaigns=current_user.campaigns(),
        invites=invites,
    )


@campaigns.route("/campaigns", methods=["POST"])
@login_required
def create() -> Response:
    """Create a campaign. The creator becomes its game master."""
    name = (request.form.get("name") or "").strip()
    description = (request.form.get("description") or "").strip()

    if not name:
        flash("A campaign needs a name", category="error")
        return redirect(url_for("campaigns.index"))
    if len(name) > MAX_NAME_LENGTH:
        flash(f"Name must be at most {MAX_NAME_LENGTH} characters", category="error")
        return redirect(url_for("campaigns.index"))
    if len(description) > MAX_DESCRIPTION_LENGTH:
        flash(f"Description must be at most {MAX_DESCRIPTION_LENGTH} characters", category="error")
        return redirect(url_for("campaigns.index"))

    campaign = Campaign(name=name, description=description, owner_id=current_user.id)
    campaign.memberships.append(
        CampaignMembership(
            user_id=current_user.id,
            role=CampaignRole.GAME_MASTER,
            status=MembershipStatus.ACTIVE,
        )
    )
    db.session.add(campaign)
    db.session.commit()
    logger.info(f"user {current_user.id} created campaign {campaign.id}")
    flash(f"Campaign '{campaign.name}' created", category="success")

    return redirect(url_for("campaigns.detail", campaign_id=campaign.id))


@campaigns.route("/campaigns/<int:campaign_id>")
@login_required
def detail(campaign_id: int) -> str:
    """One campaign: its members, and the invite form for the game master."""
    campaign = _visible_campaign(campaign_id)
    membership = campaign.membership_of(current_user.id)

    is_game_master = campaign.is_game_master(current_user.id)
    invitable_friends = []
    invite_url = ""
    if is_game_master:
        invitable_friends = [
            f for f in current_user.friends() if campaign.membership_of(f.id) is None
        ]
        if campaign.invite_code:
            invite_url = url_for(
                "campaigns.join_preview", code=campaign.invite_code, _external=True
            )

    return render_template(
        "campaign_detail.html",
        user=current_user,
        campaign=campaign,
        membership=membership,
        is_game_master=is_game_master,
        members=campaign.active_members(),
        pending=campaign.pending_invites(),
        invitable_friends=invitable_friends,
        invite_url=invite_url,
        CampaignRole=CampaignRole,
    )


@campaigns.route("/campaigns/<int:campaign_id>/invite", methods=["POST"])
@login_required
def invite(campaign_id: int) -> Response:
    """Invite someone by username. Game master only."""
    campaign = _visible_campaign(campaign_id)
    if not campaign.is_game_master(current_user.id):
        abort(403)

    username = (request.form.get("username") or "").strip()
    other = User.find_by_username(username)

    if other is None:
        flash(f"No user called '{username}'", category="error")
    elif campaign.membership_of(other.id) is not None:
        flash(f"{other.username} is already in this campaign", category="error")
    else:
        _add_member(campaign, other, MembershipStatus.INVITED)
        logger.info(f"campaign {campaign.id} invited user {other.id}")
        flash(f"Invited {other.username}", category="success")

    return redirect(url_for("campaigns.detail", campaign_id=campaign.id))


@campaigns.route("/campaigns/<int:campaign_id>/invite-friend", methods=["POST"])
@login_required
def invite_friend(campaign_id: int) -> Response:
    """Invite someone from your friend list. Game master only."""
    campaign = _visible_campaign(campaign_id)
    if not campaign.is_game_master(current_user.id):
        abort(403)

    try:
        friend_id = int(request.form.get("user_id") or 0)
    except ValueError:
        friend_id = 0

    friendship = Friendship.between(current_user.id, friend_id)
    if friendship is None or friendship.status != FriendshipStatus.ACCEPTED:
        flash("That person is not on your friend list", category="error")
        return redirect(url_for("campaigns.detail", campaign_id=campaign.id))

    friend = db.session.get(User, friend_id)
    if campaign.membership_of(friend_id) is not None:
        flash(f"{friend.username} is already in this campaign", category="error")
    else:
        _add_member(campaign, friend, MembershipStatus.INVITED)
        logger.info(f"campaign {campaign.id} invited friend {friend_id}")
        flash(f"Invited {friend.username}", category="success")

    return redirect(url_for("campaigns.detail", campaign_id=campaign.id))


@campaigns.route("/campaigns/<int:campaign_id>/invite-code", methods=["POST"])
@login_required
def new_invite_code(campaign_id: int) -> Response:
    """Issue a join code to share with people who are not friends.

    Generating a new code replaces the old one, so a code that has been shared
    too widely can be rotated.
    """
    campaign = _visible_campaign(campaign_id)
    if not campaign.is_game_master(current_user.id):
        abort(403)

    campaign.new_invite_code()
    db.session.commit()
    logger.info(f"campaign {campaign.id} issued a new invite code")
    flash("Invite link ready to share", category="success")

    return redirect(url_for("campaigns.detail", campaign_id=campaign.id))


@campaigns.route("/campaigns/<int:campaign_id>/invite-code/revoke", methods=["POST"])
@login_required
def revoke_invite_code(campaign_id: int) -> Response:
    """Turn the join code off. Anything already shared stops working."""
    campaign = _visible_campaign(campaign_id)
    if not campaign.is_game_master(current_user.id):
        abort(403)

    campaign.invite_code = None
    db.session.commit()
    flash("Invite link revoked", category="success")

    return redirect(url_for("campaigns.detail", campaign_id=campaign.id))


@campaigns.route("/campaigns/join/<code>")
@login_required
@limiter.limit("30 per hour")
def join_preview(code: str) -> Response | str:
    """Landing page for a shared invite link.

    Joining happens on POST, so simply opening a link someone sent -- or a
    crawler following it -- cannot add anyone to a campaign.
    """
    campaign = Campaign.query.filter_by(invite_code=code).first()
    if campaign is None:
        flash("That invite link is not valid any more", category="error")
        return redirect(url_for("campaigns.index"))

    if campaign.membership_of(current_user.id) is not None:
        return redirect(url_for("campaigns.detail", campaign_id=campaign.id))

    return render_template("campaign_join.html", user=current_user, campaign=campaign, code=code)


@campaigns.route("/campaigns/join", methods=["POST"])
@login_required
@limiter.limit("20 per hour")
def join_with_code() -> Response:
    """Join using an invite code.

    Rate limited: the code is a bearer token, so redemption is the one place
    where guessing would pay off.
    """
    code = (request.form.get("code") or "").strip()
    campaign = Campaign.query.filter_by(invite_code=code).first() if code else None

    if campaign is None:
        flash("That invite code is not valid", category="error")
        return redirect(url_for("campaigns.index"))

    membership = campaign.membership_of(current_user.id)
    if membership is None:
        # they were given the code, so no separate confirmation is needed
        _add_member(campaign, current_user, MembershipStatus.ACTIVE)
        logger.info(f"user {current_user.id} joined campaign {campaign.id} with a code")
        flash(f"You joined '{campaign.name}'", category="success")
    elif membership.status == MembershipStatus.INVITED:
        membership.status = MembershipStatus.ACTIVE
        db.session.commit()
        flash(f"You joined '{campaign.name}'", category="success")
    else:
        flash(f"You are already in '{campaign.name}'", category="error")

    return redirect(url_for("campaigns.detail", campaign_id=campaign.id))


@campaigns.route("/campaigns/<int:campaign_id>/accept", methods=["POST"])
@login_required
def accept(campaign_id: int) -> Response:
    """Accept an invitation addressed to you."""
    membership = CampaignMembership.query.filter_by(
        campaign_id=campaign_id, user_id=current_user.id, status=MembershipStatus.INVITED
    ).first()

    if membership is None:
        flash("That invitation no longer exists", category="error")
        return redirect(url_for("campaigns.index"))

    membership.status = MembershipStatus.ACTIVE
    db.session.commit()
    flash(f"You joined '{membership.campaign.name}'", category="success")

    return redirect(url_for("campaigns.detail", campaign_id=campaign_id))


@campaigns.route("/campaigns/<int:campaign_id>/leave", methods=["POST"])
@login_required
def leave(campaign_id: int) -> Response:
    """Decline an invitation, or leave a campaign you are in.

    The owner cannot leave; they delete the campaign instead, so a campaign is
    never left without a game master.
    """
    campaign = _visible_campaign(campaign_id)
    membership = campaign.membership_of(current_user.id)

    if campaign.owner_id == current_user.id:
        flash("You own this campaign -- delete it instead of leaving", category="error")
        return redirect(url_for("campaigns.detail", campaign_id=campaign_id))

    db.session.delete(membership)
    db.session.commit()
    flash(f"You left '{campaign.name}'", category="success")

    return redirect(url_for("campaigns.index"))


@campaigns.route("/campaigns/<int:campaign_id>/members/<int:user_id>/remove", methods=["POST"])
@login_required
def remove_member(campaign_id: int, user_id: int) -> Response:
    """Remove a member or withdraw an invitation. Game master only."""
    campaign = _visible_campaign(campaign_id)
    if not campaign.is_game_master(current_user.id):
        abort(403)

    membership = campaign.membership_of(user_id)
    if membership is None:
        flash("That member is not in this campaign", category="error")
    elif user_id == campaign.owner_id:
        flash("The owner cannot be removed", category="error")
    else:
        db.session.delete(membership)
        db.session.commit()
        flash("Removed from the campaign", category="success")

    return redirect(url_for("campaigns.detail", campaign_id=campaign_id))


@campaigns.route("/campaigns/<int:campaign_id>/delete", methods=["POST"])
@login_required
def delete(campaign_id: int) -> Response:
    """Delete a campaign. Owner only; memberships go with it."""
    campaign = _visible_campaign(campaign_id)
    if campaign.owner_id != current_user.id:
        abort(403)

    name = campaign.name
    db.session.delete(campaign)
    db.session.commit()
    logger.info(f"user {current_user.id} deleted campaign {campaign_id}")
    flash(f"Campaign '{name}' deleted", category="success")

    return redirect(url_for("campaigns.index"))
