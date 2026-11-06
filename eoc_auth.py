import streamlit as st
from supabase import create_client

@st.cache_resource
def get_supabase():
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"]
    )

def sign_up(email, password):
    """Register a new user."""
    client = get_supabase()
    return client.auth.sign_up({
        "email": email,
        "password": password
    })


def sign_in(email, password):
    """Sign in an existing user."""
    client = get_supabase()
    return client.auth.sign_in_with_password({
        "email": email,
        "password": password
    })
