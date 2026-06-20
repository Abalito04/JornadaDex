from datetime import datetime, timezone

from app.extensions import db
from app.models import RateLimitEvent


def _window_start(window):
    return datetime.now(timezone.utc) - window


def is_limited(event_type, rate_key, max_attempts, window):
    cutoff = _window_start(window)
    _prune_old(event_type, cutoff)
    count = RateLimitEvent.query.filter(
        RateLimitEvent.event_type == event_type,
        RateLimitEvent.rate_key == rate_key,
        RateLimitEvent.created_at >= cutoff,
    ).count()
    return count >= max_attempts


def record_attempt(event_type, rate_key):
    db.session.add(RateLimitEvent(event_type=event_type, rate_key=rate_key))
    db.session.commit()


def clear_attempts(event_type, rate_key):
    RateLimitEvent.query.filter_by(event_type=event_type, rate_key=rate_key).delete()
    db.session.commit()


def _prune_old(event_type, cutoff):
    RateLimitEvent.query.filter(
        RateLimitEvent.event_type == event_type,
        RateLimitEvent.created_at < cutoff,
    ).delete()
    db.session.commit()
