# Kerry Logistics Display App

A Streamlit-based application for visualizing and analyzing GPS routes data.

## Deployment Guide for Streamlit Share

This application contains sensitive information that needs to be properly handled during deployment. Follow these steps to securely deploy to Streamlit Share:

### 1. Set Up Streamlit Secrets

When deploying to Streamlit Share, you need to set up the secrets through the Streamlit Share dashboard:

1. Go to your app dashboard on Streamlit Share
2. Navigate to the "Secrets" section
3. Add the following secrets configuration (replace with your actual values):

```toml
# Firebase credentials
[firebase]
type = "service_account"
project_id = "your-project-id"
private_key_id = "your-private-key-id"
private_key = """your-private-key-with-proper-newlines"""
client_email = "your-client-email"
client_id = "your-client-id"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "your-client-x509-cert-url"
universe_domain = "googleapis.com"

# Google Maps API key
[google]
maps_api_key = "your-google-maps-api-key"

# Cookie settings from config.yaml
[cookie]
expiry_days = 30
key = "your-cookie-key"
name = "your-cookie-name"
```

### 2. Configure GitHub Repository

Make sure your GitHub repository has the following files:

1. `.gitignore` - to prevent sensitive files from being committed
2. `requirements.txt` - with all the necessary dependencies
3. `.streamlit/` directory without secrets file

### 3. Never Commit Sensitive Files

The following sensitive files should NEVER be committed to your GitHub repository:

- `fyp-gps.json` - Firebase service account credentials
- `config.yaml` - User credentials and authentication settings
- `.env` - Environment variables file (if used)
- `.streamlit/secrets.toml` - Local secrets file

These files are already included in the `.gitignore` file.

## Local Development Setup

For local development, you can use the actual files:

1. Place `fyp-gps.json` in the root directory
2. Create `config.yaml` with user credentials
3. Or create a `.streamlit/secrets.toml` file with the same structure as shown above

## Requirements

See `requirements.txt` for the full list of dependencies. 