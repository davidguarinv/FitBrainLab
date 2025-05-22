import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from datetime import datetime
from flask import current_app

# Email handling functions for form submissions

def format_email_content(form_data):
    """Format the form data into a professional email"""
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #2563eb; border-bottom: 2px solid #2563eb; padding-bottom: 10px;">
                New Lab Application Submission
            </h2>
            
            <div style="background-color: #f8fafc; padding: 15px; border-radius: 8px; margin: 20px 0;">
                <p style="margin: 0; color: #64748b; font-size: 14px;">
                    <strong>Submitted:</strong> {current_time}
                </p>
            </div>
            
            <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                <tr>
                    <td style="padding: 12px; border-bottom: 1px solid #e2e8f0; font-weight: bold; width: 30%; background-color: #f1f5f9;">
                        Name:
                    </td>
                    <td style="padding: 12px; border-bottom: 1px solid #e2e8f0;">
                        {form_data.get('first_name', '')} {form_data.get('last_name', '')}
                    </td>
                </tr>
                <tr>
                    <td style="padding: 12px; border-bottom: 1px solid #e2e8f0; font-weight: bold; background-color: #f1f5f9;">
                        Email:
                    </td>
                    <td style="padding: 12px; border-bottom: 1px solid #e2e8f0;">
                        {form_data.get('email', '')}
                    </td>
                </tr>
                <tr>
                    <td style="padding: 12px; border-bottom: 1px solid #e2e8f0; font-weight: bold; background-color: #f1f5f9;">
                        Phone:
                    </td>
                    <td style="padding: 12px; border-bottom: 1px solid #e2e8f0;">
                        {form_data.get('phone', 'Not provided')}
                    </td>
                </tr>
                <tr>
                    <td style="padding: 12px; border-bottom: 1px solid #e2e8f0; font-weight: bold; background-color: #f1f5f9;">
                        Education/Position:
                    </td>
                    <td style="padding: 12px; border-bottom: 1px solid #e2e8f0;">
                        {form_data.get('education', '')}
                    </td>
                </tr>
                <tr>
                    <td style="padding: 12px; border-bottom: 1px solid #e2e8f0; font-weight: bold; background-color: #f1f5f9;">
                        Area of Interest:
                    </td>
                    <td style="padding: 12px; border-bottom: 1px solid #e2e8f0;">
                        {form_data.get('interest', '')}
                    </td>
                </tr>
            </table>
            
            <div style="margin: 20px 0;">
                <h3 style="color: #2563eb; margin-bottom: 10px;">Message:</h3>
                <div style="background-color: #f8fafc; padding: 15px; border-radius: 8px; border-left: 4px solid #2563eb;">
                    <p style="margin: 0; white-space: pre-wrap;">{form_data.get('message', '')}</p>
                </div>
            </div>
            
            <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #e2e8f0; color: #64748b; font-size: 12px;">
                <p>This email was automatically generated from the lab application form.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html_content

def send_email(form_data):
    """Send email with form data"""
    try:
        # Get configuration values directly from Flask config
        email_user = current_app.config['EMAIL_USER']
        recipient_email = current_app.config['RECIPIENT_EMAIL']
        smtp_server = current_app.config['SMTP_SERVER']
        smtp_port = current_app.config['SMTP_PORT']
        email_password = current_app.config['EMAIL_PASSWORD']
        
        # Validate email configuration
        if not email_user or not email_password:
            raise ValueError("Email user or password not configured")
            
        # Create message
        msg = MIMEMultipart('alternative')
        msg['From'] = email_user
        msg['To'] = recipient_email
        msg['Subject'] = f"New Lab Application - {form_data.get('first_name', '')} {form_data.get('last_name', '')}"
        
        # Create HTML content
        html_content = format_email_content(form_data)
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)
        
        # Send email
        try:
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(email_user, email_password)
                server.send_message(msg)
                current_app.logger.info("Email sent successfully")
                return True
        except smtplib.SMTPAuthenticationError as e:
            current_app.logger.error(f"Authentication error: {e}")
            raise ValueError("Invalid email credentials. Please check your email and password.")
        except smtplib.SMTPException as e:
            current_app.logger.error(f"SMTP error occurred: {e}")
            return False
        
    except Exception as e:
        current_app.logger.error(f"Error sending email: {e}")
        return False
