from datetime import date, timedelta


def calculate_viral_score(
    views: int,
    likes: int,
    comments: int,
    days_since_posted: float,
    avg_views_for_handle: float,
) -> int:
    """
    Returns a 0-100 score relative to the account's own average views.
    A video with 2x avg views scores ~70 from the view component alone.
    """
    # View component: relative to account average (max 70 pts)
    view_ratio = views / max(avg_views_for_handle, 1)
    view_score = min(70, view_ratio * 35)

    # Engagement rate component (max 20 pts)
    engagement = (likes + comments * 2) / max(views, 1)
    engagement_score = min(20, engagement * 200)

    # Recency bonus: full points within 14 days, zero after (max 10 pts)
    recency = max(0.0, 1.0 - (days_since_posted / 14))
    recency_score = recency * 10

    return min(100, int(view_score + engagement_score + recency_score))


def get_week_start_date(reference_date: date) -> date:
    """Returns the Monday of the week containing reference_date."""
    return reference_date - timedelta(days=reference_date.weekday())
