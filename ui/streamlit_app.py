import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st

from app.config import get_settings
from agent.groq_client import GroqAssistant
from agent.kb_search import KnowledgeBaseSearch
from agent.triage_agent import TriageAgent


@st.cache_resource(show_spinner=False)
def get_agent() -> TriageAgent:
    settings = get_settings()
    llm_client = GroqAssistant(
        provider=settings.llm_provider,
        api_key=settings.groq_api_key,
        match_threshold=settings.kb_similarity_threshold,
    )
    kb = KnowledgeBaseSearch(kb_path=settings.kb_path)
    return TriageAgent(
        llm_client=llm_client,
        kb_search=kb,
        match_threshold=settings.kb_similarity_threshold,
        max_related=settings.max_related_results,
    )


def main() -> None:
    st.set_page_config(page_title="Support Triage Agent")
    st.title("Support Ticket Triage")
    st.write("Enter a support description to identify likely category, severity, and next steps.")

    description = st.text_area("Ticket description", height=160)
    if st.button("Run triage"):
        if len(description.strip()) < 10:
            st.error("Description must be at least 10 characters long.")
            return
        agent = get_agent()
        with st.spinner("Analyzing ticket..."):
            result = agent.triage(description)

        st.subheader("Summary")
        st.write(f"**Summary:** {result['summary']}")
        st.write(f"**Category:** {result['category']}")
        st.write(f"**Severity:** {result['severity']}")
        st.write(f"**Known issue:** {'Yes' if result['known_issue'] else 'No'}")
        st.write(f"**Suggested next step:** {result['suggested_next_step']}")

        related = result.get("related_issues", [])
        if related:
            st.subheader("Related KB articles")
            st.table(related)
        else:
            st.info("No related KB entries found.")


if __name__ == "__main__":
    main()
