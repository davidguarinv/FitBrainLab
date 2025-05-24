import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from datetime import datetime
from flask import current_app
import json
import os

# Email handling functions for form submissions

def format_email_content(form_data, email_type):
    """Format the form data into a professional email"""
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if email_type == 'community_submission':
        # Get the base URL for confirmation links
        base_url = current_app.config.get('BASE_URL', 'http://localhost:5000')
        submission_id = form_data.get('submission_id')
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2563eb; border-bottom: 2px solid #2563eb; padding-bottom: 10px;">
                    New Community Submission
                </h2>
                
                <div style="background-color: #f8fafc; padding: 15px; border-radius: 8px; margin: 20px 0;">
                    <p style="margin: 0; color: #64748b; font-size: 14px;">
                        <strong>Submitted:</strong> {current_time}
                    </p>
                </div>
                
                <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                    <tr>
                        <td style="padding: 12px; border-bottom: 1px solid #e2e8f0; font-weight: bold; width: 30%; background-color: #f1f5f9;">
                            Community Name:
                        </td>
                        <td style="padding: 12px; border-bottom: 1px solid #e2e8f0;">
                            {form_data.get('Name', '')}
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 12px; border-bottom: 1px solid #e2e8f0; font-weight: bold; background-color: #f1f5f9;">
                            Contact Email:
                        </td>
                        <td style="padding: 12px; border-bottom: 1px solid #e2e8f0;">
                            {form_data.get('email', '')}
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 12px; border-bottom: 1px solid #e2e8f0; font-weight: bold; background-color: #f1f5f9;">
                            Location:
                        </td>
                        <td style="padding: 12px; border-bottom: 1px solid #e2e8f0;">
                            {form_data.get('Location', '')}
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 12px; border-bottom: 1px solid #e2e8f0; font-weight: bold; background-color: #f1f5f9;">
                            Sport:
                        </td>
                        <td style="padding: 12px; border-bottom: 1px solid #e2e8f0;">
                            {form_data.get('Sport', '')}
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 12px; border-bottom: 1px solid #e2e8f0; font-weight: bold; background-color: #f1f5f9;">
                            Website:
                        </td>
                        <td style="padding: 12px; border-bottom: 1px solid #e2e8f0;">
                            <a href="{form_data.get('website', '')}" style="color: #2563eb;">{form_data.get('website', 'Not provided')}</a>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 12px; border-bottom: 1px solid #e2e8f0; font-weight: bold; background-color: #f1f5f9;">
                            Logo URL:
                        </td>
                        <td style="padding: 12px; border-bottom: 1px solid #e2e8f0;">
                            {form_data.get('image_url', 'Not provided')}
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 12px; border-bottom: 1px solid #e2e8f0; font-weight: bold; background-color: #f1f5f9;">
                            Cost:
                        </td>
                        <td style="padding: 12px; border-bottom: 1px solid #e2e8f0;">
                            {form_data.get('Cost', 'Not specified')}
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 12px; border-bottom: 1px solid #e2e8f0; font-weight: bold; background-color: #f1f5f9;">
                            International/Dutch:
                        </td>
                        <td style="padding: 12px; border-bottom: 1px solid #e2e8f0;">
                            {form_data.get('Int/Dutch', 'Both')}
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 12px; border-bottom: 1px solid #e2e8f0; font-weight: bold; background-color: #f1f5f9;">
                            Student-based:
                        </td>
                        <td style="padding: 12px; border-bottom: 1px solid #e2e8f0;">
                            {form_data.get('Student-based', 'No')}
                        </td>
                    </tr>
                </table>
                
                <div style="margin: 20px 0;">
                    <h3 style="color: #2563eb; margin-bottom: 10px;">Message:</h3>
                    <div style="background-color: #f8fafc; padding: 15px; border-radius: 8px; border-left: 4px solid #2563eb;">
                        <p style="margin: 0; white-space: pre-wrap;">{form_data.get('message', '')}</p>
                    </div>
                </div>
                
                <div style="margin: 30px 0; text-align: center; background-color: #fef3c7; padding: 20px; border-radius: 8px;">
                    <h3 style="color: #92400e; margin-bottom: 15px;">Action Required:</h3>
                    <p style="margin-bottom: 20px; color: #92400e;">Please review the community submission and click one of the buttons below:</p>
                    <div style="display: flex; gap: 15px; justify-content: center; flex-wrap: wrap;">
                        <a href="{base_url}/confirm-community/{submission_id}/accept" 
                           style="background-color: #059669; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block;">
                            ✅ Accept Community
                        </a>
                        <a href="{base_url}/confirm-community/{submission_id}/reject" 
                           style="background-color: #dc2626; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block;">
                            ❌ Reject Community
                        </a>
                    </div>
                </div>
                
                <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #e2e8f0; color: #64748b; font-size: 12px;">
                    <p>This email was automatically generated from the community submission form.</p>
                    <p><strong>Submission ID:</strong> {submission_id}</p>
                </div>
            </div>
        </body>
        </html>
        """
    else:
        # Keep the existing email format for lab applications
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

def send_email(form_data, email_type='application'):
    """Send email with form data"""
    try:
        # Get configuration values from Flask config
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
        
        if email_type == 'community_submission':
            msg['Subject'] = f"New Community Submission - {form_data.get('Name', 'Unknown')}"
        else:
            msg['Subject'] = f"New Lab Application - {form_data.get('first_name', '')} {form_data.get('last_name', '')}"
        
        # Create HTML content
        html_content = format_email_content(form_data, email_type)
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)
        
        # Send email
        try:
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(email_user, email_password)
                server.send_message(msg)
                current_app.logger.info(f"Email sent successfully for {email_type}")
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