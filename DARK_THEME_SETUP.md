# Dark Theme Setup

This application uses a dark theme for better visibility and reduced eye strain. The dark theme is enforced for all users through the `.streamlit/config.toml` file.

## Theme Configuration

The theme is configured with Kerry Logistics branded colors:

```toml
[theme]
primaryColor = "#FF6600"  # Kerry Logistics orange
backgroundColor = "#0A0F16"  # Dark background
secondaryBackgroundColor = "#121920"  # Dark secondary background
textColor = "#E0E7FF"  # Light text for dark mode
base = "dark"  # Force dark theme for all users
```

## Custom Styling

Additional custom styling is applied through the `component/style.py` file, which provides consistent branding and enhanced user experience across the application.
