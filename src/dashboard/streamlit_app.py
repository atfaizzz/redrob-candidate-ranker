"""Streamlit recruiter dashboard for explainable ranking exploration."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config.settings import load_config, parse_app_settings
from src.dashboard.service import RecruiterDashboardService
from src.dashboard.view_models import (
    apply_candidate_filters,
    build_explainability_panel,
    compare_candidates,
    semantic_search_candidates,
)


def _load_streamlit():
    try:
        import streamlit as st  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "Streamlit is required for dashboard UI. Install with: pip install streamlit"
        ) from exc
    return st


def run_dashboard(config_path: str = "configs/base.yaml") -> None:
    """Run recruiter dashboard application."""

    st = _load_streamlit()
    st.set_page_config(page_title="AI Recruiter Intelligence", layout="wide")

    st.title("Redrob Candidate Ranking System")
    st.caption("Explainable ranking and recruiter decision support")

    raw_config = load_config(config_path)
    settings = parse_app_settings(raw_config)
    service = RecruiterDashboardService(settings)

    with st.sidebar:
        st.header("Controls")
        st.write("Use filters and search to refine ranked recommendations.")
        run_button = st.button("Run Ranking")

    if run_button or "dashboard_state" not in st.session_state:
        with st.spinner("Running ranking pipeline..."):
            try:
                st.session_state.dashboard_state = service.run_ranking()
                st.session_state.error_message = ""
            except Exception as exc:
                st.session_state.error_message = str(exc)

    error = st.session_state.get("error_message", "")
    if error:
        st.error(f"Ranking failed: {error}")
        return

    state = st.session_state.get("dashboard_state")
    if state is None:
        st.info("Click 'Run Ranking' to generate recommendations.")
        return

    summary = state.summary
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Candidates", summary["total_candidates"])
    col2.metric("Retrieved", summary["retrieved_candidates"])
    col3.metric("Ranked", summary["ranked_candidates"])

    st.subheader("Search and Filters")
    query = st.text_input("Semantic Search", placeholder="e.g., retrieval ranking product ML")
    min_exp = st.slider("Minimum Experience (years)", 0.0, 20.0, 0.0, 0.5)
    min_conf = st.slider("Minimum Confidence", 0.0, 1.0, 0.0, 0.05)
    location_filter = st.text_input("Location Contains", placeholder="Noida")

    cards = semantic_search_candidates(state.cards, query)
    cards = apply_candidate_filters(cards, min_exp, location_filter, min_conf)

    st.subheader("Top Candidates")
    if not cards:
        st.warning("No candidates match current search/filter criteria.")
    else:
        table_rows = [
            {
                "candidate_id": card.candidate_id,
                "rank": card.rank,
                "score": card.score,
                "confidence": card.confidence,
                "confidence_label": card.confidence_label,
                "title": card.title,
                "location": card.location,
                "years_of_experience": card.years_of_experience,
            }
            for card in cards
        ]
        st.dataframe(table_rows, use_container_width=True, hide_index=True)

    st.subheader("Candidate Details & Explainability")
    ranked_by_id = {row.candidate_id: row for row in state.ranked}
    selected_id = st.selectbox(
        "Select candidate",
        options=[card.candidate_id for card in cards] if cards else [row.candidate_id for row in state.ranked],
    )

    selected_candidate = state.candidates_by_id[selected_id]
    selected_ranked = ranked_by_id[selected_id]
    panel = build_explainability_panel(selected_ranked, selected_candidate)

    st.write("Overall Match:", panel.overall_match)
    st.write("Strongest Evidence:")
    st.write(panel.strongest_evidence)
    st.write("Potential Gaps:")
    st.write(panel.potential_gaps or ["No major gaps identified"])
    st.write("Career Analysis:", panel.career_analysis)
    st.write("Skill Analysis:", panel.skill_analysis)
    st.write("Behavior Signals:", panel.behavior_analysis)
    st.write("Confidence Analysis:", panel.confidence_analysis)
    st.write("Reasoning Summary:", panel.reasoning_summary)

    st.subheader("Candidate Comparison")
    compare_candidates_ids = st.multiselect(
        "Select up to 2 candidates",
        options=[card.candidate_id for card in cards] if cards else [row.candidate_id for row in state.ranked],
        max_selections=2,
    )
    if len(compare_candidates_ids) == 2:
        first_id, second_id = compare_candidates_ids
        comparison = compare_candidates(
            state.candidates_by_id[first_id],
            ranked_by_id[first_id],
            state.candidates_by_id[second_id],
            ranked_by_id[second_id],
        )
        st.json(comparison)

    st.subheader("Shortlist and Export")
    shortlisted_ids = st.multiselect(
        "Choose shortlisted candidates",
        options=[card.candidate_id for card in cards] if cards else [row.candidate_id for row in state.ranked],
        default=[card.candidate_id for card in cards[: min(5, len(cards))]],
    )
    if st.button("Export Shortlist"):
        output_path = service.export_shortlist(state.ranked, shortlisted_ids)
        st.success(f"Shortlist exported to {output_path}")

    if settings.dashboard.enable_engineering_view:
        st.subheader("Engineering View")
        st.write("Ranking Summary")
        st.json(summary["ranking_summary"])
        st.write("Retrieval Summary")
        st.json(summary["retrieval_summary"])
        st.write("Pipeline Metrics")
        st.json(summary["metrics"])


def main() -> None:
    run_dashboard()


if __name__ == "__main__":
    main()
