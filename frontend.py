"""
frontend.py
============
Streamlit UI — calls backend_server.py over HTTP.
Run with: streamlit run frontend.py

backend_server.py must be running separately on BACKEND_URL (default: http://localhost:7860).
"""

import logging
import os

import requests
import streamlit as st

logger = logging.getLogger("rag_frontend")

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:7860")

st.set_page_config(page_title="Qwen3B RAG Chatbot", page_icon="🤖", layout="wide")


# --------------------------------------------------------------------------
# Backend client helpers
# --------------------------------------------------------------------------
def _get(path: str, timeout: int = 10) -> dict:
    try:
        r = requests.get(f"{BACKEND_URL}{path}", timeout=timeout)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)}


def _post(path: str, json: dict = None, files=None, timeout: int = 120) -> dict:
    try:
        r = requests.post(f"{BACKEND_URL}{path}", json=json, files=files, timeout=timeout)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)}


# --------------------------------------------------------------------------
# Session state
# --------------------------------------------------------------------------
def init_session_state() -> None:
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "indexed_files" not in st.session_state:
        st.session_state.indexed_files = []


# --------------------------------------------------------------------------
# Sidebar
# --------------------------------------------------------------------------
def render_sidebar() -> bool:
    with st.sidebar:
        st.header("Settings")

        if st.button("Check LLM connection"):
            result = _get("/health")
            if "error" in result:
                st.error(f"Backend unreachable: {result['error']}")
            elif result.get("llm_reachable"):
                st.success("Connected to Qwen3B endpoint.")
            else:
                st.warning("Backend is up but Qwen3B endpoint is unreachable.")

        st.divider()
        st.subheader("Documents")
        uploaded_files = st.file_uploader(
            "Upload documents",
            type=["pdf", "docx", "csv", "xlsx", "xls", "txt", "png", "jpg", "jpeg"],
            accept_multiple_files=True,
        )

        if uploaded_files:
            for uploaded_file in uploaded_files:
                if uploaded_file.name in st.session_state.indexed_files:
                    continue
                with st.spinner(f"Indexing '{uploaded_file.name}'..."):
                    result = _post(
                        "/upload",
                        files={"file": (uploaded_file.name, uploaded_file.getbuffer())},
                    )
                if "error" in result:
                    st.error(f"Failed to index '{uploaded_file.name}': {result['error']}")
                else:
                    st.session_state.indexed_files.append(uploaded_file.name)
                    st.success(f"Indexed '{uploaded_file.name}'")

        if st.session_state.indexed_files:
            st.write("Indexed files:")
            for name in st.session_state.indexed_files:
                st.write(f"- {name}")

        st.divider()
        use_web_search = st.toggle("Enable web search for this question", value=False)

        st.divider()
        if st.button("Clear conversation"):
            st.session_state.chat_history = []
            _post("/clear")
            st.rerun()

    return use_web_search


# --------------------------------------------------------------------------
# Chat
# --------------------------------------------------------------------------
def render_chat_history() -> None:
    for turn in st.session_state.chat_history:
        with st.chat_message(turn["role"]):
            st.markdown(turn["content"])


def handle_user_input(use_web_search: bool) -> None:
    question = st.chat_input("Ask a question...")
    if not question:
        return

    st.session_state.chat_history.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            result = _post("/chat", json={
                "question": question,
                "chat_history": st.session_state.chat_history,
                "use_web_search": use_web_search,
            })

        if "error" in result:
            answer = f"Error: {result['error']}"
            sources = []
        else:
            answer = result["answer"]
            sources = result.get("sources", [])

        st.markdown(answer)
        if sources:
            st.caption(f"Sources: {', '.join(sources)}")

    st.session_state.chat_history.append({"role": "assistant", "content": answer})


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------
def main() -> None:
    st.title("Qwen3B RAG Chatbot")
    st.caption("Backed by Qwen2.5-3B running on Kaggle, exposed via ngrok.")

    init_session_state()
    use_web_search = render_sidebar()
    render_chat_history()
    handle_user_input(use_web_search)


if __name__ == "__main__":
    main()