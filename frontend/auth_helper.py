import streamlit as st
from db_helper import verify_user, create_user, init_users_table

init_users_table()


def _login_form():
    col_left, col_center, col_right = st.columns([1, 1.2, 1])
    with col_center:
        st.markdown(
            "<h1 style='text-align: center; white-space: nowrap;'>SCIAS Login</h1>",
            unsafe_allow_html=True,
        )
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")

        col1, col2 = st.columns(2)
        with col1:
            login_clicked = st.button("Login", type="primary", use_container_width=True)
        with col2:
            signup_clicked = st.button("Create Account", use_container_width=True)

        if login_clicked:
            user = verify_user(username, password)
            if user:
                st.session_state.authenticated = True
                st.session_state.username = user["username"]
                st.session_state.role = user["role"]
                st.rerun()
            else:
                st.error("Invalid username or password")

        if signup_clicked:
            st.session_state.show_signup = True
            st.rerun()


def _signup_form():
    col_left, col_center, col_right = st.columns([1, 1.2, 1])
    with col_center:
        st.markdown(
            "<h1 style='text-align: center; white-space: nowrap;'>Create Account</h1>",
            unsafe_allow_html=True,
        )
        new_username = st.text_input("Choose a username", key="signup_username")
        new_password = st.text_input("Choose a password", type="password", key="signup_password")
        confirm_password = st.text_input("Confirm password", type="password", key="signup_confirm")

        col1, col2 = st.columns(2)
        with col1:
            create_clicked = st.button("Create Account", type="primary", use_container_width=True)
        with col2:
            back_clicked = st.button("Back to Login", use_container_width=True)

        if create_clicked:
            if not new_username or not new_password:
                st.error("Username and password are required")
            elif new_password != confirm_password:
                st.error("Passwords do not match")
            elif len(new_password) < 4:
                st.error("Password must be at least 4 characters")
            else:
                success = create_user(new_username, new_password, role="farmer")
                if success:
                    st.success("Account created. You can log in now.")
                    st.session_state.show_signup = False
                    st.rerun()
                else:
                    st.error("That username is already taken")

        if back_clicked:
            st.session_state.show_signup = False
            st.rerun()


def check_login():
    """Call this at the very top of every page. Stops execution if not logged in."""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "show_signup" not in st.session_state:
        st.session_state.show_signup = False

    if st.session_state.authenticated:
        return  # already logged in, let the page render

    if st.session_state.show_signup:
        _signup_form()
    else:
        _login_form()

    st.stop()  # prevents rest of the page from rendering


def logout_button():
    """Call this in the sidebar (or wherever you want a logout control) on any page.
    Only renders if the user is currently logged in."""
    if st.session_state.get("authenticated"):
        st.sidebar.markdown(f"Logged in as **{st.session_state.get('username', '')}**")
        if st.sidebar.button("Logout"):
            st.session_state.authenticated = False
            st.session_state.username = None
            st.session_state.role = None
            st.rerun()