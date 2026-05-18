# dashboard/tabs/weekly_summary.py
import json
import streamlit as st
from dashboard.queries import get_summary, get_available_weeks


def _render_top3(raw: str):
    """Renders top3_to_copy — handles JSON list or plain markdown."""
    if not raw or raw.strip() in ("—", ""):
        st.info("Geen top 3 beschikbaar.")
        return

    # Try to parse as JSON list
    try:
        data = json.loads(raw) if isinstance(raw, str) else raw
        if isinstance(data, list):
            for i, item in enumerate(data, 1):
                with st.container(border=True):
                    if isinstance(item, dict):
                        cols = st.columns([1, 9])
                        with cols[0]:
                            st.markdown(
                                f'<div style="font-family:Anton,sans-serif;font-size:36px;'
                                f'color:#E9003A;line-height:1;padding-top:4px">{i}</div>',
                                unsafe_allow_html=True,
                            )
                        with cols[1]:
                            hook = (item.get("hook") or item.get("titel") or
                                    item.get("title") or item.get("idee") or "")
                            suggestie = (item.get("suggestie") or item.get("suggestion") or
                                         item.get("beschrijving") or item.get("uitleg") or "")
                            tag = (item.get("hook_type") or item.get("type") or
                                   item.get("thema") or item.get("theme") or "")

                            if hook:
                                st.markdown(
                                    f'<p style="font-family:Inter,sans-serif;font-size:15px;'
                                    f'font-weight:700;color:#F5F5F5;margin:0 0 6px 0">{hook}</p>',
                                    unsafe_allow_html=True,
                                )
                            if tag:
                                st.markdown(
                                    f'<span style="font-family:Roboto Mono,monospace;font-size:10px;'
                                    f'color:#E9003A;background:rgba(233,0,58,0.10);padding:2px 8px;'
                                    f'border-radius:2px;letter-spacing:0.5px">{tag.upper()}</span>',
                                    unsafe_allow_html=True,
                                )
                                st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
                            if suggestie:
                                st.caption(suggestie)

                            # Any remaining fields as captions
                            shown = {"hook", "titel", "title", "idee", "suggestie",
                                     "suggestion", "beschrijving", "uitleg",
                                     "hook_type", "type", "thema", "theme"}
                            for k, v in item.items():
                                if k not in shown and v:
                                    st.caption(f"**{k}:** {v}")
                    else:
                        st.markdown(f"**{i}.** {item}")
            return
    except Exception:
        pass

    # Fallback: render as plain markdown
    st.markdown(raw)


def render(week):
    st.subheader("Weekly Summary")

    summary = get_summary(week)

    if not summary:
        weeks = get_available_weeks()
        if len(weeks) > 1:
            prev_week = weeks[1]
            summary = get_summary(prev_week)
            if summary:
                st.info(f"Samenvatting van week {week} nog niet beschikbaar. Vorige week ({prev_week}) getoond.")
            else:
                st.info("Nog geen samenvatting. Wordt aangemaakt na de volgende scrape run.")
                return
        else:
            st.info("Nog geen samenvatting. Wordt aangemaakt na de volgende scrape run.")
            return

    st.markdown("### Trending Thema's")
    st.markdown(summary.get("trending_themes", "—"))

    st.markdown("### Beste Hook-types")
    st.markdown(summary.get("best_hook_types", "—"))

    st.markdown("### Top 3 Om Na Te Maken")
    _render_top3(summary.get("top3_to_copy", ""))

    st.markdown("### Jouw Contentadvies Deze Week")
    st.success(summary.get("weekly_advice", "—"))

    st.caption(f"Gegenereerd op {str(summary.get('generated_at', ''))[:10]}")
