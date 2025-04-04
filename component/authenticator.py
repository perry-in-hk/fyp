import yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth
import streamlit as st
from streamlit_authenticator.utilities import (CredentialsError, ForgotError, Hasher, LoginError, RegisterError, ResetError, UpdateError)

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

# Define a function to handle the authentication process
def handle_authentication(st):
    if 'authentication_status' not in st.session_state:
        st.session_state['authentication_status'] = None

    if st.session_state['authentication_status'] is False:
        st.error('Username/password is incorrect')
    elif st.session_state['authentication_status'] is None:
        option = st.radio("Choose an option", ["Login", "Signup", "Forget Password"])

        if option == "Login":
            try:
                authenticator.login()
            except LoginError as e:
                st.error(e)
            if st.session_state['authentication_status']:
                st.rerun()
            elif st.session_state['authentication_status'] is False:
                st.error('Username/password is incorrect')
            elif st.session_state['authentication_status'] is None:
                st.warning('Please enter your username and password')

        elif option == "Signup":
            try:
                (email_of_registered_user,
                 username_of_registered_user,
                 name_of_registered_user) = authenticator.register_user()
                if email_of_registered_user:
                    st.success('User registered successfully')
            except RegisterError as e:
                st.error(e)
        elif option == "Forget Password":
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

            try:
                (username_of_forgotten_username,
                    email_of_forgotten_username) = authenticator.forgot_username()
                if username_of_forgotten_username:
                    st.success('Username sent securely')
                elif not username_of_forgotten_username:
                    st.error('Email not found')
            except ForgotError as e:
                st.error(e)

# Saving config file - This will be disabled on Streamlit Share Cloud
def save_config():
    # Only save to file when not using Streamlit secrets
    if "cookie" not in st.secrets:
        with open('config.yaml', 'w', encoding='utf-8') as file:
            yaml.dump(config, file, default_flow_style=False)

