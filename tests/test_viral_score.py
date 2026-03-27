from processor.viral_score import calculate_viral_score, get_week_start_date
from datetime import date, timedelta

def test_score_above_average_is_high():
    score = calculate_viral_score(
        views=20000, likes=500, comments=50,
        days_since_posted=3, avg_views_for_handle=10000
    )
    assert score >= 60

def test_score_below_average_is_low():
    score = calculate_viral_score(
        views=2000, likes=50, comments=5,
        days_since_posted=10, avg_views_for_handle=10000
    )
    assert score < 30

def test_score_capped_at_100():
    score = calculate_viral_score(
        views=1000000, likes=100000, comments=10000,
        days_since_posted=0, avg_views_for_handle=1000
    )
    assert score == 100

def test_score_never_negative():
    score = calculate_viral_score(
        views=0, likes=0, comments=0,
        days_since_posted=30, avg_views_for_handle=10000
    )
    assert score >= 0

def test_cold_start_no_zero_division():
    score = calculate_viral_score(
        views=5000, likes=100, comments=20,
        days_since_posted=2, avg_views_for_handle=0
    )
    assert 0 <= score <= 100

def test_week_start_date_is_monday():
    thursday = date(2026, 3, 26)
    monday = get_week_start_date(thursday)
    assert monday == date(2026, 3, 23)
    assert monday.weekday() == 0
