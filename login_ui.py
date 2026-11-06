import streamlit as st
from eoc_auth import sign_up, sign_in

def show_login():
    st.title("PA EOC Practice")
    st.subheader("Your Personal Study Account")

    tab1, tab2 = st.tabs(["Log In", "Create Account"])

    with tab1:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")

            if st.form_submit_button("Log In"):
                try:
                    result = sign_in(email, password)
                    st.session_state["user"] = result.user
                    st.session_state["access_token"] = result.session.access_token
                    st.success("Login successful!")
                except Exception:
                    st.error("Unable to log in. Check your email and password.")

    with tab2:
        with st.form("signup_form"):
            email = st.text_input("Email", key="signup_email")
            password = st.text_input(
                "Password", type="password", key="signup_password"
            )

            if st.form_submit_button("Create Account"):
                try:
                    result = sign_up(email, password)
                    if result.user:
                        st.success(
                            "Account created. Check your email for a confirmation link."
                        )
                    else:
                        st.info("Check your email for further instructions.")
                except Exception:
                    st.error("Unable to create account. Please try again.")

if __name__ == "__main__":
    show_login()
