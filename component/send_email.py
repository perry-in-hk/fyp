from email.mime.text import MIMEText
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os

def send_email(receiver_email, subject, attachment_path):
    sender_email = "hkustesgmodel@gmail.com"  # Replace with your email
    password = "qrmh ghyn viys kfqt"  # Replace with your email password or app-specific password

    # Create the email
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject

    body = """
    Dear user,

    I hope this email finds you well.

    Please find attached the ESG report for your review. The report provides comprehensive insights into our environmental, social, and governance performance.

    Please note, this email was sent by an automated system. For any further information or inquiries, kindly contact phwongar@connect.ust.hk.

    Yours sincerely,
    Perry Wong
    Lead Engineer
    Kerry Logistic FYP
    """


    # Attach the body with the msg instance
    msg.attach(MIMEText(body, 'plain'))

    # Attach the PDF file
    if attachment_path and os.path.exists(attachment_path):
        with open(attachment_path, "rb") as attachment:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f"attachment; filename= {os.path.basename(attachment_path)}")
        msg.attach(part)

    # Create SMTP session
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()  # Enable security
        server.login(sender_email, password)  # Log in to your email account
        server.send_message(msg)  # Send the email

    print("Email sent successfully!")