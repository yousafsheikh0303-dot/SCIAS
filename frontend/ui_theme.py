"""
Shared visual design system for every SCIAS Streamlit page.

Import apply_theme() once at the top of each page, then use render_header(),
render_answer(), and render_agent_badge() instead of raw st.title/st.write,
so every page stays visually consistent and the palette only needs to
change in one place.
"""

import html
import streamlit as st

# ---------------------------------------------------------------------------
# Palette: white + light green throughout. Agent badges vary only by shade
# and icon within this same green family, not by switching hue, so the
# app reads as one consistent identity rather than six unrelated colors.
# ---------------------------------------------------------------------------
PALETTE = {
    "bg": "#FFFFFF",
    "bg_soft": "#EEF7F1",
    "border": "#B7DCC4",
    "green_deep": "#1B4332",
    "green": "#2D6A4F",
    "green_mid": "#40916C",
    "ink": "#1D2620",
    "muted": "#5C6B60",
}

AGENT_STYLE = {
    "weather":       {"icon": "\u2601\uFE0F", "label": "Weather",    "bg": "#1B4332", "fg": "#FFFFFF"},
    "irrigation":    {"icon": "\U0001F4A7",   "label": "Irrigation", "bg": "#2D6A4F", "fg": "#FFFFFF"},
    "disease":       {"icon": "\U0001F343",   "label": "Disease",    "bg": "#40916C", "fg": "#FFFFFF"},
    "market":        {"icon": "\U0001F3F7\uFE0F", "label": "Market", "bg": "#52B788", "fg": "#0F241B"},
    "yield":         {"icon": "\U0001F33E",   "label": "Yield",      "bg": "#74C69D", "fg": "#0F241B"},
    "knowledge_rag": {"icon": "\U0001F4D6",   "label": "Knowledge",  "bg": "#95D5B2", "fg": "#0F241B"},
}

# Session state keys
HEADER_VISIBLE_KEY = "scias_header_visible"
SIDEBAR_VISIBLE_KEY = "scias_sidebar_visible"


def apply_theme(hide_header: bool = True):
    """
    Apply the SCIAS theme to the Streamlit app.

    Args:
        hide_header: If True, hides the Streamlit header (including the deploy button,
                    decoration, and collapse toggle). Default is True for a clean,
                    app-only look.
    """
    # Initialize header/sidebar visibility in session state if not set
    if HEADER_VISIBLE_KEY not in st.session_state:
        st.session_state[HEADER_VISIBLE_KEY] = not hide_header
    if SIDEBAR_VISIBLE_KEY not in st.session_state:
        st.session_state[SIDEBAR_VISIBLE_KEY] = True

    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    #MainMenu, footer {visibility: hidden;}

    /* Hide only the Deploy button and top decoration bar -- keep the header
       container itself intact, since it also holds the sidebar collapse/
       expand toggle control. Hiding the whole header removes that toggle,
       which can leave the sidebar permanently collapsed with no way to
       reopen it. */
    div[data-testid="stToolbarActions"] {
        visibility: hidden;
    }
    div[data-testid="stDecoration"] {
        visibility: hidden;
        height: 0;
    }
    header[data-testid="stHeader"] {
        background: transparent;
        height: 3rem;
    }

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    .stApp { background: #FFFFFF; }

    /* Force full width -- covers multiple Streamlit internal class names/versions
       since the exact selector Streamlit uses has changed across releases. */
    .block-container,
    div[data-testid="stAppViewContainer"] .block-container,
    div[data-testid="stMain"] .block-container,
    section.main .block-container {
        max-width: 100% !important;
        width: 100% !important;
        padding-top: 1.5rem !important;
        padding-left: 3rem !important;
        padding-right: 3rem !important;
    }

    /* Sidebar: match the white/light-green theme instead of default grey */
    section[data-testid="stSidebar"] {
        background: #EEF7F1;
        border-right: 1px solid #B7DCC4;
    }
    section[data-testid="stSidebar"] a,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] p {
        color: #1B4332 !important;
    }
    section[data-testid="stSidebar"] a:hover {
        background: #DCEFE2 !important;
    }
    section[data-testid="stSidebar"] [aria-current="page"] {
        background: #DCEFE2 !important;
        border-radius: 8px;
    }

    /* Compact page header -- replaces st.title() + st.caption() */
    .scias-header {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        gap: 0.25rem;
        margin-bottom: 1.1rem;
        padding-bottom: 0.8rem;
        border-bottom: 1px solid #B7DCC4;
    }
    .scias-header .icon-title-row {
        display: flex;
        align-items: baseline;
        justify-content: center;
        gap: 0.55rem;
    }
    .scias-header .icon { font-size: 1.6rem; }
    .scias-header .title { font-size: 1.55rem; font-weight: 700; color: #1B4332; }
    .scias-header .sub { font-size: 0.9rem; color: #5C6B60; }

    /* Form surface */
    div[data-testid="stForm"] {
        background: #EEF7F1;
        border: 1px solid #B7DCC4;
        border-radius: 12px;
        padding: 1.1rem 1.2rem 0.6rem 1.2rem;
    }

    div[data-testid="stTextInput"] input,
    div[data-testid="stNumberInput"] input {
        background: #FFFFFF;
        border: 1px solid #B7DCC4;
        border-radius: 8px;
        color: #1D2620;
    }
    div[data-testid="stTextInput"] input:focus,
    div[data-testid="stNumberInput"] input:focus {
        border-color: #2D6A4F;
        box-shadow: 0 0 0 1px #2D6A4F;
    }

    div[data-testid="stSelectbox"] > div > div {
        background: #FFFFFF;
        border-radius: 8px;
    }

    /* Primary button / form submit button */
    button[kind="primary"], button[kind="primaryFormSubmit"] {
        background: #1B4332 !important;
        color: #FFFFFF !important;
        border: none !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
    }
    button[kind="primary"]:hover, button[kind="primaryFormSubmit"]:hover {
        background: #2D6A4F !important;
    }

    /* Answer card */
    .scias-answer {
        background: #EEF7F1;
        border-left: 4px solid #2D6A4F;
        border-radius: 8px;
        padding: 1rem 1.2rem;
        margin-top: 0.7rem;
    }
    .scias-answer p { color: #1D2620; font-size: 0.97rem; line-height: 1.55; margin: 0; }

    /* Agent routing badge */
    .scias-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.76rem;
        font-weight: 500;
        padding: 0.28rem 0.7rem;
        border-radius: 20px;
        margin-bottom: 0.6rem;
    }

    /* Quick-suggestion chips */
    .scias-chip-row { display: flex; flex-wrap: wrap; gap: 0.4rem; margin-bottom: 0.8rem; }

    .scias-footer {
        text-align: center;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.72rem;
        color: #8A968E;
        margin-top: 1.8rem;
    }

    /* Toggle button style */
    .scias-toggle-header {
        position: fixed;
        top: 0.5rem;
        right: 0.5rem;
        z-index: 999999;
        background: #EEF7F1;
        border: 1px solid #B7DCC4;
        border-radius: 8px;
        padding: 0.3rem 0.8rem;
        font-size: 0.75rem;
        font-family: 'Inter', sans-serif;
        color: #1B4332;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    .scias-toggle-header:hover {
        background: #DCEFE2;
        border-color: #2D6A4F;
    }

    /* Sidebar logout block */
    .scias-user-tag {
        font-family: 'Inter', sans-serif;
        font-size: 0.82rem;
        color: #1B4332 !important;
        margin-bottom: 0.4rem;
    }
    </style>
    """, unsafe_allow_html=True)

    # Apply header/sidebar visibility based on session state
    toggle_header_visibility(st.session_state[HEADER_VISIBLE_KEY])
    toggle_sidebar_visibility(st.session_state[SIDEBAR_VISIBLE_KEY])


def toggle_header_visibility(show: bool = False):
    """
    Toggle the Streamlit header visibility.

    Args:
        show: If True, shows the header. If False, hides it.
    """
    if show:
        st.markdown("""
        <style>
        header[data-testid="stHeader"] {
            display: block !important;
            visibility: visible !important;
            height: 3rem !important;
        }
        button[data-testid="baseButton-header"] {
            display: flex !important;
            visibility: visible !important;
        }
        </style>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <style>
        header[data-testid="stHeader"] {
            display: none !important;
            visibility: hidden !important;
            height: 0 !important;
        }
        button[data-testid="baseButton-header"] {
            display: none !important;
            visibility: hidden !important;
        }
        </style>
        """, unsafe_allow_html=True)

    st.session_state[HEADER_VISIBLE_KEY] = show


def toggle_sidebar_visibility(show: bool = True):
    """
    Toggle the sidebar open/closed. Unlike the old forced-open behavior,
    this lets the sidebar actually collapse when show=False, and forces
    it back open when show=True -- driven by our own toggle button rather
    than only Streamlit's native (and easy-to-lose) collapse arrow.
    """
    if show:
        st.markdown("""
        <style>
        section[data-testid="stSidebar"] {
            visibility: visible !important;
            transform: none !important;
            min-width: 244px !important;
            width: 244px !important;
        }
        </style>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <style>
        section[data-testid="stSidebar"] {
            transform: translateX(-100%) !important;
            min-width: 0px !important;
            width: 0px !important;
            visibility: hidden !important;
        }
        </style>
        """, unsafe_allow_html=True)

    st.session_state[SIDEBAR_VISIBLE_KEY] = show


def render_header_toggle_button():
    """
    Render a small toggle button in the top-right corner to show/hide the Streamlit header.
    Place this at the top of your page after apply_theme() to allow users to control
    header visibility.
    """
    current_state = st.session_state.get(HEADER_VISIBLE_KEY, False)
    label = "Hide Header" if current_state else "Show Header"

    if st.button(
        label,
        key="scias_toggle_header_btn",
        help="Toggle Streamlit header visibility",
        use_container_width=False,
    ):
        toggle_header_visibility(not current_state)
        st.rerun()


def render_sidebar_toggle_button():
    """
    Render a small button (in the main page area, not inside the sidebar --
    so it's still reachable even when the sidebar is fully collapsed) that
    opens/closes the sidebar. Place this at the top of your page after
    apply_theme(), e.g. right before render_header().
    """
    current_state = st.session_state.get(SIDEBAR_VISIBLE_KEY, True)
    label = "☰ Close Sidebar" if current_state else "☰ Open Sidebar"

    if st.button(
        label,
        key="scias_toggle_sidebar_btn",
        help="Show or hide the sidebar",
        use_container_width=False,
    ):
        toggle_sidebar_visibility(not current_state)
        st.rerun()


def render_header(icon: str, title: str, sub: str = ""):
    """Centered page header -- icon + title on one line, subtitle below."""
    sub_html = f'<div class="sub">{html.escape(sub)}</div>' if sub else ""
    st.markdown(
        f'<div class="scias-header">'
        f'<div class="icon-title-row"><span class="icon">{icon}</span> '
        f'<span class="title">{html.escape(title)}</span></div>'
        f'{sub_html}</div>',
        unsafe_allow_html=True,
    )


def render_agent_badge(agent_used: str):
    style = AGENT_STYLE.get(agent_used, {"icon": "\U0001F916", "label": agent_used, "bg": "#40916C", "fg": "#FFFFFF"})
    st.markdown(
        f'<span class="scias-badge" style="background:{style["bg"]};color:{style["fg"]}">'
        f'{style["icon"]} {html.escape(str(style["label"]))}</span>',
        unsafe_allow_html=True,
    )


def render_answer(text: str):
    """
    Renders the agent's answer as HTML. Escapes the text first so characters
    like < > & (which show up in real answers -- e.g. "ETo < 10mm", Urdu
    punctuation) don't break the markup, then converts \\n to <br> since raw
    newlines don't create line breaks inside an HTML <p> tag.
    """
    safe_text = html.escape(text).replace("\n", "<br>")
    st.markdown(f'<div class="scias-answer"><p>{safe_text}</p></div>', unsafe_allow_html=True)


def render_footer(session_id: str, extra: str = ""):
    extra_html = f" &middot; {html.escape(extra)}" if extra else ""
    st.markdown(
        f'<div class="scias-footer">SESSION {html.escape(session_id[:8])}'
        f'{extra_html} &middot; theme v6-safehtml</div>',
        unsafe_allow_html=True,
    )


def render_logout():
    """
    Renders the logged-in username and a Logout button in the sidebar.
    Only shows anything if the user is currently authenticated. Call this
    from any page after check_login() has already run -- e.g. right after
    apply_theme().
    """
    if not st.session_state.get("authenticated"):
        return

    username = st.session_state.get("username", "")
    st.sidebar.markdown(f'<div class="scias-user-tag">Logged in as <b>{html.escape(username)}</b></div>', unsafe_allow_html=True)
    if st.sidebar.button("Logout", key="scias_logout_btn"):
        st.session_state.authenticated = False
        st.session_state.username = None
        st.session_state.role = None
        st.rerun()