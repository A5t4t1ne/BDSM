from datetime import datetime, timezone
from enum import IntEnum

from flask_login import UserMixin
from sqlalchemy import CheckConstraint, UniqueConstraint

from . import db


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Level(IntEnum):
    """Access level of a user account. Lower is more privileged."""

    ADMIN = 0
    SYSADMIN = 1
    USER = 2
    GUEST = 3


class FriendshipStatus(IntEnum):
    """A friendship is requested by one side and confirmed by the other."""

    PENDING = 0
    ACCEPTED = 1


class CampaignRole(IntEnum):
    """What a member may do inside a campaign.

    Only the game master can invite or remove members. New roles can be added
    here without touching the membership table.
    """

    GAME_MASTER = 0
    PLAYER = 1


class MembershipStatus(IntEnum):
    """An invited member becomes active once they accept."""

    INVITED = 0
    ACTIVE = 1


class Hero(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150))
    secure_name = db.Column(db.String(150), index=True)
    path = db.Column(db.String(1000))
    stats = db.Column(db.JSON)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), index=True)


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(150))
    access_lvl = db.Column(db.Integer, default=Level.USER)
    email = db.Column(db.String(150))  # not used yet
    heroes_path = db.Column(db.String(1000))
    # one to many -> relationship connects the "one" to another class of which it can possess multiples.
    # heroes will be a list type variable with all Hero-objects created by the indivial user
    heroes = db.relationship("Hero", cascade="all, delete-orphan")

    @classmethod
    def find_by_username(cls, username: str) -> "User | None":
        """Look up a user case-insensitively, so 'Dave' and 'dave' are one account."""
        if not username:
            return None
        return cls.query.filter(db.func.lower(cls.username) == username.lower()).first()

    def friends(self) -> list["User"]:
        """Every user this one is actually friends with.

        A friendship is stored once, in the direction it was requested, so both
        directions have to be checked.
        """
        rows = Friendship.query.filter(
            Friendship.status == FriendshipStatus.ACCEPTED,
            db.or_(Friendship.requester_id == self.id, Friendship.addressee_id == self.id),
        ).all()
        other_ids = [r.addressee_id if r.requester_id == self.id else r.requester_id for r in rows]
        if not other_ids:
            return []
        return User.query.filter(User.id.in_(other_ids)).order_by(User.username).all()

    def campaigns(self) -> list["Campaign"]:
        """Campaigns this user has joined."""
        return (
            Campaign.query.join(CampaignMembership)
            .filter(
                CampaignMembership.user_id == self.id,
                CampaignMembership.status == MembershipStatus.ACTIVE,
            )
            .order_by(Campaign.name)
            .all()
        )


class Friendship(db.Model):
    """A friend link between two users.

    Stored once, in the direction it was requested. The pair is unique, and a
    user cannot befriend themselves.
    """

    __table_args__ = (
        UniqueConstraint("requester_id", "addressee_id", name="uq_friendship_pair"),
        CheckConstraint("requester_id != addressee_id", name="ck_friendship_not_self"),
    )

    id = db.Column(db.Integer, primary_key=True)
    requester_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    addressee_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    status = db.Column(db.Integer, nullable=False, default=FriendshipStatus.PENDING)
    created_at = db.Column(db.DateTime, default=_utcnow)

    requester = db.relationship("User", foreign_keys=[requester_id])
    addressee = db.relationship("User", foreign_keys=[addressee_id])

    @classmethod
    def between(cls, user_a_id: int, user_b_id: int) -> "Friendship | None":
        """The friendship linking two users, whichever way round it was made."""
        return cls.query.filter(
            db.or_(
                db.and_(cls.requester_id == user_a_id, cls.addressee_id == user_b_id),
                db.and_(cls.requester_id == user_b_id, cls.addressee_id == user_a_id),
            )
        ).first()


class Campaign(db.Model):
    """A group of players. Deliberately thin: everything a campaign will later
    carry (sessions, shared notes, a hero roster) hangs off the membership or a
    new table, not off extra columns here."""

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(2000), default="")
    owner_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=_utcnow)

    owner = db.relationship("User", foreign_keys=[owner_id])
    memberships = db.relationship(
        "CampaignMembership", cascade="all, delete-orphan", back_populates="campaign"
    )

    def membership_of(self, user_id: int) -> "CampaignMembership | None":
        return next((m for m in self.memberships if m.user_id == user_id), None)

    def active_members(self) -> list["CampaignMembership"]:
        return sorted(
            (m for m in self.memberships if m.status == MembershipStatus.ACTIVE),
            key=lambda m: (m.role, m.user.username or ""),
        )

    def pending_invites(self) -> list["CampaignMembership"]:
        return [m for m in self.memberships if m.status == MembershipStatus.INVITED]

    def is_game_master(self, user_id: int) -> bool:
        membership = self.membership_of(user_id)
        return (
            membership is not None
            and membership.status == MembershipStatus.ACTIVE
            and membership.role == CampaignRole.GAME_MASTER
        )


class CampaignMembership(db.Model):
    """One user's place in one campaign, invited or active."""

    __table_args__ = (
        UniqueConstraint("campaign_id", "user_id", name="uq_campaign_member"),
    )

    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey("campaign.id"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    role = db.Column(db.Integer, nullable=False, default=CampaignRole.PLAYER)
    status = db.Column(db.Integer, nullable=False, default=MembershipStatus.INVITED)
    created_at = db.Column(db.DateTime, default=_utcnow)

    campaign = db.relationship("Campaign", back_populates="memberships")
    user = db.relationship("User", foreign_keys=[user_id])
