"""Email integration for SMF Lead Capture - SMTP-based, no APIs needed."""

import logging
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Any, Dict

logger = logging.getLogger(__name__)


class EmailIntegration:
    """Email integration using SMTP - works with Google Workspace, Gmail, or any SMTP server."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize email integration."""
        self.config = config
        self.enabled = config.get("enabled", True)
        
        # SMTP Configuration
        self.smtp_host = config.get("smtp_host", "smtp.gmail.com")
        self.smtp_port = config.get("smtp_port", 587)
        self.smtp_user = config.get("smtp_user")  # michael@smfworks.com
        self.smtp_password = config.get("smtp_password")  # App password
        self.use_tls = config.get("use_tls", True)
        
        # From settings
        self.from_email = config.get("from_email") or self.smtp_user
        self.from_name = config.get("from_name", "SMF Works")
        self.to_email = config.get("to")  # Owner notification email
    
    def send_notification(self, lead, config: Dict[str, Any]) -> str:
        """Send lead notification to owner."""
        if not self.enabled:
            return "email disabled"
        
        to_email = config.get("to") or self.to_email
        if not to_email:
            return "no recipient configured"
        
        template = config.get("template", "default")
        
        subject = f"🔥 New {lead.score_category.upper()} Lead: {lead.name or 'Anonymous'}"
        
        # Build HTML email
        html_body = f"""
        <h2>New Lead Captured!</h2>
        
        <table style="border-collapse: collapse; width: 100%; max-width: 600px;">
            <tr><td style="padding: 8px; border: 1px solid #ddd; font-weight: bold;">Name:</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{lead.name or "N/A"}</td></tr>
            <tr><td style="padding: 8px; border: 1px solid #ddd; font-weight: bold;">Email:</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{lead.email}</td></tr>
            <tr><td style="padding: 8px; border: 1px solid #ddd; font-weight: bold;">Phone:</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{lead.phone or "N/A"}</td></tr>
            <tr><td style="padding: 8px; border: 1px solid #ddd; font-weight: bold;">Source:</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{lead.source}</td></tr>
            <tr><td style="padding: 8px; border: 1px solid #ddd; font-weight: bold;">Score:</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{lead.score} ({lead.score_category})</td></tr>
        </table>
        
        <p><strong>Message:</strong></p>
        <blockquote style="border-left: 3px solid #0066CC; padding-left: 10px; margin-left: 0;">
            {lead.message or "N/A"}
        </blockquote>
        
        <p><strong>Qualification Data:</strong></p>
        <pre style="background: #f5f5f5; padding: 10px; border-radius: 4px;">{lead.qualification_data or {}}</pre>
        <p><a href="{self.config.get('dashboard_url', '')}/leads/{lead.id}" 
             style="background: #0066CC; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px;">
             View in Dashboard
        </a></p>
        """
        
        text_body = f"""
New lead captured!

Name: {lead.name or "N/A"}
Email: {lead.email}
Phone: {lead.phone or "N/A"}
Source: {lead.source}
Score: {lead.score} ({lead.score_category})

Message:
{lead.message or "N/A"}

Qualification Data:
{lead.qualification_data or {}}
        """.strip()
        
        return self._send_email(to_email, subject, text_body, html_body)
    
    def send_confirmation(self, lead, template: str = "default") -> str:
        """Send confirmation email to lead."""
        if not self.enabled:
            return "email disabled"
        
        if not lead.email:
            return "no lead email"
        
        subject = "Thanks for reaching out to SMF Works!"
        
        html_body = f"""
        <h2>Thanks for reaching out, {lead.name or "there"}!</h2>
        
        <p>We've received your message and will get back to you within 24 hours.</p>
        
        <h3>What happens next:</h3>
        <ol>
            <li>Our team reviews your inquiry</li>
            <li>We'll reach out within 24 hours</li>
            <li>We'll discuss how SMF Works can help your business</li>
        </ol>
        
        <p>If you have any urgent questions, just reply to this email.</p>
        
        <p>Best regards,<br>
        The SMF Works Team</p>
        
        <hr>
        <p style="font-size: 12px; color: #666;">
            This email was sent because you contacted us via smfworks.com.
        </p>
        """
        
        text_body = f"""Thanks for reaching out, {lead.name or "there"}!

We've received your message and will get back to you within 24 hours.

What happens next:
1. Our team reviews your inquiry
2. We'll reach out within 24 hours
3. We'll discuss how SMF Works can help your business

If you have any urgent questions, just reply to this email.

Best regards,
The SMF Works Team

---
This email was sent because you contacted us via smfworks.com.
        """.strip()
        
        return self._send_email(lead.email, subject, text_body, html_body)
    
    def _send_email(self, to_email: str, subject: str, text_body: str, html_body: str = None) -> str:
        """Send email via SMTP."""
        if not all([self.smtp_host, self.smtp_user, self.smtp_password]):
            logger.warning("SMTP not fully configured")
            return "smtp not configured"
        
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{self.from_name} <{self.from_email}>"
            msg["To"] = to_email
            
            # Add text part
            msg.attach(MIMEText(text_body, "plain"))
            
            # Add HTML part if provided
            if html_body:
                msg.attach(MIMEText(html_body, "html"))
            
            # Connect and send
            context = ssl.create_default_context()
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls(context=context)
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.from_email, to_email, msg.as_string())
            
            logger.info(f"Email sent to {to_email}")
            return "sent"
            
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP authentication failed: {e}")
            return "auth failed - check credentials"
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error: {e}")
            return f"smtp error: {str(e)}"
        except Exception as e:
            logger.error(f"Email send failed: {e}")
            return f"error: {str(e)}"
