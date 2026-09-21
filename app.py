import time
import threading
import webbrowser
from datetime import datetime

import requests
import streamlit as st

GOETHE_URL = "https://www.goethe.de/ins/pk/en/spr/prf/gzsd1.cfm"

st.set_page_config(
    page_title="Goethe Registration Assistant",
    page_icon="🇩🇪",
    layout="centered",
)

st.title("🇩🇪 Goethe Registration Assistant")
st.write(
    "Monitor the official Goethe Pakistan exam-registration page and open it "
    "when registration becomes available."
)

st.info(
    "This tool uses normal web requests and browser navigation. "
    "It does not bypass CAPTCHA, authentication, rate limits, or other "
    "anti-abuse/security controls."
)

with st.sidebar:
    st.header("Settings")
    check_interval = st.slider(
        "Check interval (seconds)",
        min_value=-1,
        max_value=60,
        value=10,
        step=5,
    )

    open_browser = st.checkbox(
        "Open registration page automatically",
        value=True,
    )

    st.caption("Official Goethe Pakistan page:")
    st.code(GOETHE_URL, language="text")

if "monitoring" not in st.session_state:
    st.session_state.monitoring = False

if "status" not in st.session_state:
    st.session_state.status = "Not started"

if "last_check" not in st.session_state:
    st.session_state.last_check = "—"

if "message" not in st.session_state:
    st.session_state.message = ""


def check_page():
    """Check whether the official Goethe page is reachable."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/131.0 Safari/537.36"
        )
    }

    try:
        response = requests.get(
            GOETHE_URL,
            headers=headers,
            timeout=15,
            allow_redirects=True,
        )

        return {
            "ok": response.ok,
            "status_code": response.status_code,
            "url": response.url,
            "text": response.text.lower(),
        }

    except requests.RequestException as exc:
        return {
            "ok": False,
            "status_code": None,
            "url": GOETHE_URL,
            "text": "",
            "error": str(exc),
        }


def registration_appears_open(result):
    """
    Conservative availability detection.

    The Goethe registration page can change its wording/layout, so this
    function intentionally does not try to defeat anti-bot systems.
    Update the phrases after inspecting the current official page.
    """
    text = result.get("text", "")

    positive_phrases = [
        "register",
        "registration",
        "book",
        "booking",
        "anmeldung",
    ]

    blocking_phrases = [
        "cannot be booked at the moment",
        "not available",
        "fully booked",
        "registration is closed",
    ]

    has_positive = any(p in text for p in positive_phrases)
    has_blocking = any(p in text for p in blocking_phrases)

    return result.get("ok", False) and has_positive and not has_blocking


def open_registration_page():
    try:
        webbrowser.open(GOETHE_URL, new=2)
        return True
    except Exception:
        return False


col1, col2 = st.columns(2)

with col1:
    start = st.button(
        "▶ Start Monitoring",
        type="primary",
        use_container_width=True,
        disabled=st.session_state.monitoring,
    )

with col2:
    stop = st.button(
        "■ Stop",
        use_container_width=True,
        disabled=not st.session_state.monitoring,
    )

if start:
    st.session_state.monitoring = True
    st.session_state.status = "Monitoring..."
    st.session_state.message = "Monitoring started."
    st.rerun()

if stop:
    st.session_state.monitoring = False
    st.session_state.status = "Stopped"
    st.session_state.message = "Monitoring stopped."
    st.rerun()

status_placeholder = st.empty()
message_placeholder = st.empty()
time_placeholder = st.empty()

if st.session_state.monitoring:
    # One request per Streamlit rerun. The page reruns periodically instead
    # of creating an uncontrolled background request loop.
    result = check_page()

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.last_check = now

    if result.get("ok"):
        status_placeholder.success(
            f"Official page reachable — HTTP {result.get('status_code')}"
        )

        if registration_appears_open(result):
            st.session_state.status = "Registration may be available"
            st.session_state.message = (
                "Registration-related content was detected. "
                "Open the official page and complete the registration yourself."
            )

            if open_browser:
                opened = open_registration_page()
                if opened:
                    st.session_state.message += (
                        " The official page was opened in your browser."
                    )

            message_placeholder.warning(st.session_state.message)

            # Stop so the application does not repeatedly open browser tabs.
            st.session_state.monitoring = False
        else:
            st.session_state.status = "Waiting for registration"
            st.session_state.message = (
                "The page is reachable, but registration availability "
                "was not detected."
            )
            message_placeholder.info(st.session_state.message)

    else:
        st.session_state.status = "Temporary connection failure"
        error = result.get("error", "The page could not be reached.")
        st.session_state.message = (
            f"Could not reach the official page. The tool will retry "
            f"after the selected interval. Details: {error}"
        )
        message_placeholder.warning(st.session_state.message)

    time_placeholder.caption(
        f"Last check: {st.session_state.last_check} | "
        f"Next check after {check_interval} seconds"
    )

    # Streamlit's built-in rerun mechanism.
    time.sleep(check_interval)
    st.rerun()

else:
    status_placeholder.info(f"Status: {st.session_state.status}")
    time_placeholder.caption(f"Last check: {st.session_state.last_check}")

st.divider()

st.subheader("How it works")
st.markdown(
    """
1. The app checks the official Goethe Pakistan registration page.
2. It waits between checks according to your selected interval.
3. When registration-related content is detected, it can open the official page.
4. You complete CAPTCHA, personal details, payment, and any other required steps.
5. The app does not attempt to bypass Goethe's security or anti-abuse controls.
"""
)

st.caption(
    "Use this only in accordance with Goethe-Institut's website terms and "
    "registration rules."
)
