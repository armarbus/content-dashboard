# dashboard/queries.py
import streamlit as st
from supabase import create_client, Client


@st.cache_resource
def get_client() -> Client:
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_ANON_KEY"],
    )


@st.cache_data(ttl=300)
def get_available_weeks():
    response = get_client().table("reels").select("week_start_date").execute()
    weeks = sorted(set(r["week_start_date"] for r in response.data), reverse=True)
    return weeks


@st.cache_data(ttl=300)
def get_reels(week=None, min_score=0, handles=None, hook_types=None, themes=None, own_only=False, competitors_only=False):
    q = get_client().table("reels").select("*")
    if week:
        q = q.eq("week_start_date", week)
    if min_score > 0:
        q = q.gte("viral_score", min_score)
    if own_only:
        q = q.eq("is_own_account", True)
    if competitors_only:
        q = q.eq("is_own_account", False)
    if handles:
        q = q.in_("competitor_handle", handles)
    response = q.order("viral_score", desc=True).execute()
    data = response.data
    if hook_types:
        data = [r for r in data if r.get("hook_type") in hook_types]
    if themes:
        data = [r for r in data if r.get("theme") in themes]
    return data


@st.cache_data(ttl=300)
def get_summary(week):
    response = (
        get_client()
        .table("summaries")
        .select("*")
        .eq("week_start_date", week)
        .execute()
    )
    return response.data[0] if response.data else None


@st.cache_data(ttl=300)
def get_niche_reels(week=None, min_score=0):
    """Fetches reels scraped via hashtag discovery (source='hashtag')."""
    q = get_client().table("reels").select("*").eq("source", "hashtag")
    if week:
        q = q.eq("week_start_date", week)
    if min_score > 0:
        q = q.gte("viral_score", min_score)
    response = q.order("viral_score", desc=True).execute()
    return response.data
