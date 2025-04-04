import yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth
import streamlit as st
from streamlit_authenticator.utilities import (CredentialsError, ForgotError, Hasher, LoginError, RegisterError, ResetError, UpdateError)
import os
import base64
from component.style import KERRY_ORANGE

# Global config variable
config = None

# Function to load config
def load_config():
    global config
    
    # If running on Streamlit Cloud, use secrets for cookie configuration
    if st.secrets and "cookie" in st.secrets:
        cookie_config = {
            "name": st.secrets["cookie"]["name"],
            "key": st.secrets["cookie"]["key"],
            "expiry_days": st.secrets["cookie"]["expiry_days"]
        }
        
        # Initialize empty credentials if they don't exist yet (first deployment)
        credentials_config = {
            "usernames": {
                # Add default admin account
                "1234": {
                    "email": "1234",
                    "name": "Admin",
                    "password": "$2b$12$FrRPv8b/6TKko/yMpu93.OMfr13mTLelfNPwuuq7LhmLn1J41AAVK"
                }
            }
        }
        
        config = {
            "cookie": cookie_config,
            "credentials": credentials_config
        }
    else:
        # When running locally, use config.yaml
        try:
            with open('config.yaml', 'r', encoding='utf-8') as file:
                config = yaml.load(file, Loader=SafeLoader)
        except FileNotFoundError:
            st.error("Configuration file not found. Please set up Streamlit secrets or create a config.yaml file.")
            st.stop()

# Load config when module is imported
load_config()

# Pre-hashing all plain text passwords once
stauth.Hasher.hash_passwords(config['credentials'])

# Creating the authenticator object
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

def get_kerry_logo_html():
    """Returns Kerry Logistics logo HTML for login screen"""
    # Path to the logo file - check if it exists or use a default
    logo_path = os.path.join(os.path.dirname(__file__), 'logo.png')
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            logo_data = base64.b64encode(f.read()).decode()
        return f'<img src="data:image/png;base64,{logo_data}" class="kerry-logo" alt="Kerry Logistics">'
    else:
        # Fallback to text if no logo image is found
        return f'<h1 style="color:{KERRY_ORANGE}; margin-bottom:1rem;">KERRY</h1>'

# Define a function to handle the authentication process
def handle_authentication(st):
    if 'authentication_status' not in st.session_state:
        st.session_state['authentication_status'] = None

    # Apply Kerry Logistics styled login UI 
    if st.session_state['authentication_status'] is False:
        st.markdown('<div class="kerry-login-container">', unsafe_allow_html=True)
        
        # Login header with logo
        st.markdown(f"""
        <div class="kerry-login-header">
            {get_kerry_logo_html()}
            <h2 class="kerry-login-title">Sign in to Kerry Logistics</h2>
            <p class="kerry-login-subtitle">Enter your credentials to access the dashboard</p>
            <div class="fleet-tracker-badge">Fleet Intelligence Tracker</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.error('Username/password is incorrect')
        
        # Custom login form - we'll still use the authenticator's login function
        try:
            authenticator.login()
        except LoginError as e:
            st.error(e)
            
        # Footer with copyright
        st.markdown(f"""
        <div class="kerry-login-footer">
            <div class="copyright">Kerry Logistics © {st.session_state.get('current_year', 2023)}</div>
            <div>Optimizing fleet performance and logistics</div>
        </div>
        """, unsafe_allow_html=True)
            
        st.markdown('</div>', unsafe_allow_html=True)
    
    elif st.session_state['authentication_status'] is None:
        # Container for the Kerry Login UI
        st.markdown('<div class="kerry-login-container">', unsafe_allow_html=True)
        
        # Login header with logo
        st.markdown(f"""
        <div class="kerry-login-header">
            {get_kerry_logo_html()}
            <h2 class="kerry-login-title">Kerry Logistics</h2>
            <p class="kerry-login-subtitle">Advanced Analytics Platform</p>
            <div class="fleet-tracker-badge">Fleet Intelligence Tracker</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Tabs for different authentication options
        login_tab, signup_tab, forgot_tab = st.tabs(["Sign In", "Sign Up", "Forgot Password"])
        
        with login_tab:
            try:
                authenticator.login()
            except LoginError as e:
                st.error(e)
            if st.session_state['authentication_status']:
                st.rerun()
            elif st.session_state['authentication_status'] is False:
                st.error('Username/password is incorrect')
            
            # Environmental message for login tab
            st.markdown("""
            <div style="margin-top: 2rem; text-align: center; opacity: 0.8;">
                <p style="font-size: 0.9rem;">Intelligent fleet monitoring and management</p>
            </div>
            """, unsafe_allow_html=True)

        with signup_tab:
            st.markdown("""
            <div style="text-align: center; margin-bottom: 1rem;">
                <h3 style="font-size: 1.2rem;">Create Account</h3>
                <p style="font-size: 0.9rem; color: #8A9AB0;">Join the Kerry Logistics network</p>
            </div>
            """, unsafe_allow_html=True)
            
            try:
                (email_of_registered_user,
                 username_of_registered_user,
                 name_of_registered_user) = authenticator.register_user()
                if email_of_registered_user:
                    st.success('User registered successfully')
            except RegisterError as e:
                st.error(e)

        with forgot_tab:
            st.markdown("""
            <div style="text-align: center; margin-bottom: 1rem;">
                <h3 style="font-size: 1.2rem;">Reset Access</h3>
                <p style="font-size: 0.9rem; color: #8A9AB0;">Recover your account credentials</p>
            </div>
            """, unsafe_allow_html=True)
            
            forgot_pw, forgot_username = st.tabs(["Forgot Password", "Forgot Username"])
            
            with forgot_pw:
                try:
                    (username_of_forgotten_password,
                        email_of_forgotten_password,
                        new_random_password) = authenticator.forgot_password()
                    if username_of_forgotten_password:
                        st.success('New password sent securely')
                    elif not username_of_forgotten_password:
                        st.error('Username not found')
                except ForgotError as e:
                    st.error(e)
            
            with forgot_username:
                try:
                    (username_of_forgotten_username,
                        email_of_forgotten_username) = authenticator.forgot_username()
                    if username_of_forgotten_username:
                        st.success('Username sent securely')
                    elif not username_of_forgotten_username:
                        st.error('Email not found')
                except ForgotError as e:
                    st.error(e)
        
        # Footer with contact info
        st.markdown(f"""
        <div class="kerry-login-footer">
            <div class="copyright">Kerry Logistics Network Limited © {st.session_state.get('current_year', 2023)}</div>
            <div>Smart logistics for a connected future</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Close the container
        st.markdown('</div>', unsafe_allow_html=True)

# Saving config file - This will be disabled on Streamlit Share Cloud
def save_config():
    # Only save to file when not using Streamlit secrets
    if "cookie" not in st.secrets:
        with open('config.yaml', 'w', encoding='utf-8') as file:
            yaml.dump(config, file, default_flow_style=False)

