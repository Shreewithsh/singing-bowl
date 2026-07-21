"""
Singing Bowl Export Desk
Email Sender Service - Handles personalized bulk email sending
"""
import logging
import smtplib
import time
import random
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, Optional

logger = logging.getLogger(__name__)


def personalize_email(template: str, lead: Dict) -> str:
    """Replace placeholders in email template with lead data."""
    replacements = {
        '{{ownerName}}': lead.get('owner_name') or lead.get('business_name') or 'Business Owner',
        '{{businessName}}': lead.get('business_name') or 'Your Company',
        '{{country}}': lead.get('country') or 'your country',
        '{{website}}': lead.get('website') or '',
        '{{email}}': lead.get('email') or '',
        '{{phone}}': lead.get('phone') or '',
        '{{productCatalogPDF}}': lead.get('product_catalog_pdf') or 'https://yourdomain.com/catalog.pdf',
        '{{whatsAppNumber}}': lead.get('whatsapp_number') or '+977-9800000000',
        '{{unsubscribeUrl}}': lead.get('unsubscribe_url') or 'https://yourdomain.com/unsubscribe',
    }
    result = template
    for placeholder, value in replacements.items():
        result = result.replace(placeholder, str(value))
    return result


def create_smtp_connection(config: Dict) -> Optional[smtplib.SMTP]:
    """Create and authenticate SMTP connection."""
    try:
        server_host = config.get('mail_server', 'smtp.gmail.com')
        server_port = int(config.get('mail_port', 587))
        use_tls = str(config.get('mail_use_tls', 'true')).lower() == 'true'
        username = config.get('mail_username', '')
        password = config.get('mail_password', '')

        if not username or not password:
            raise ValueError("SMTP username and password are required")

        if server_port == 465:
            server = smtplib.SMTP_SSL(server_host, server_port, timeout=30)
        else:
            server = smtplib.SMTP(server_host, server_port, timeout=30)
            if use_tls:
                server.starttls()

        server.login(username, password)
        logger.info(f"SMTP connected to {server_host}:{server_port}")
        return server
    except smtplib.SMTPAuthenticationError:
        logger.error("SMTP authentication failed - check credentials")
        raise
    except smtplib.SMTPConnectError as e:
        logger.error(f"SMTP connection error: {e}")
        raise
    except Exception as e:
        logger.error(f"SMTP setup error: {e}")
        raise


def send_single_email(
    smtp_server: smtplib.SMTP,
    from_email: str,
    to_email: str,
    subject: str,
    html_body: str,
    sender_name: str = 'Singing Bowl Export Desk'
) -> bool:
    """Send a single email. Returns True on success."""
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{sender_name} <{from_email}>"
        msg['To'] = to_email
        msg['X-Mailer'] = 'SingingBowlExportDesk/1.0'

        # Add plain text version
        plain_text = _html_to_plain(html_body)
        msg.attach(MIMEText(plain_text, 'plain', 'utf-8'))
        msg.attach(MIMEText(html_body, 'html', 'utf-8'))

        smtp_server.sendmail(from_email, [to_email], msg.as_string())
        logger.info(f"Email sent to {to_email}")
        return True
    except smtplib.SMTPRecipientsRefused:
        logger.warning(f"Recipient refused: {to_email}")
        return False
    except smtplib.SMTPDataError as e:
        logger.error(f"SMTP data error for {to_email}: {e}")
        return False
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        return False


def _html_to_plain(html: str) -> str:
    """Convert HTML to plain text."""
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        return soup.get_text(separator='\n', strip=True)
    except Exception:
        import re
        return re.sub('<[^<]+?>', '', html)


def run_bulk_email_campaign(
    leads: list,
    subject: str,
    body_template: str,
    smtp_config: Dict,
    extra_placeholders: Dict = None,
    delay_min: float = 2.0,
    delay_max: float = 5.0,
    progress_callback=None
) -> Dict:
    """
    Send bulk emails to a list of leads.
    
    Returns dict with:
    - sent: list of lead IDs successfully sent
    - failed: list of lead IDs that failed
    - skipped: list of lead IDs skipped (already contacted or no email)
    """
    results = {
        'sent': [],
        'failed': [],
        'skipped': [],
        'total': len(leads)
    }

    if not leads:
        return results

    from_email = smtp_config.get('mail_username', '')
    if not from_email:
        raise ValueError("Sender email (MAIL_USERNAME) is not configured")

    # Establish SMTP connection
    try:
        server = create_smtp_connection(smtp_config)
    except Exception as e:
        logger.error(f"Cannot start bulk email campaign: {e}")
        raise

    reconnect_interval = 50  # Reconnect every 50 emails
    emails_sent_count = 0

    for i, lead in enumerate(leads):
        lead_dict = lead if isinstance(lead, dict) else lead.to_dict()
        lead_id = lead_dict.get('id')

        if progress_callback:
            progress_callback({
                'current': i + 1,
                'total': len(leads),
                'email': lead_dict.get('email', ''),
                'sent': len(results['sent']),
                'failed': len(results['failed']),
                'skipped': len(results['skipped'])
            })

        # Skip if already contacted
        if lead_dict.get('contacted'):
            results['skipped'].append(lead_id)
            continue

        email = lead_dict.get('email', '').strip()
        if not email:
            results['skipped'].append(lead_id)
            continue

        # Merge extra placeholders
        lead_with_extras = lead_dict.copy()
        if extra_placeholders:
            lead_with_extras.update(extra_placeholders)

        # Personalize
        personalized_body = personalize_email(body_template, lead_with_extras)
        personalized_subject = personalize_email(subject, lead_with_extras)

        # Reconnect if needed
        if emails_sent_count > 0 and emails_sent_count % reconnect_interval == 0:
            try:
                server.quit()
            except Exception:
                pass
            try:
                server = create_smtp_connection(smtp_config)
            except Exception as e:
                logger.error(f"Reconnect failed: {e}")
                # Mark remaining as failed
                for remaining in leads[i:]:
                    r_dict = remaining if isinstance(remaining, dict) else remaining.to_dict()
                    results['failed'].append(r_dict.get('id'))
                break

        # Send
        success = send_single_email(
            server, from_email, email,
            personalized_subject, personalized_body
        )

        if success:
            results['sent'].append(lead_id)
            emails_sent_count += 1
        else:
            # Retry once
            time.sleep(1)
            success = send_single_email(
                server, from_email, email,
                personalized_subject, personalized_body
            )
            if success:
                results['sent'].append(lead_id)
                emails_sent_count += 1
            else:
                results['failed'].append(lead_id)

        # Delay between emails
        if i < len(leads) - 1:
            delay = random.uniform(delay_min, delay_max)
            time.sleep(delay)

    # Close SMTP connection
    try:
        server.quit()
    except Exception:
        pass

    logger.info(
        f"Campaign complete: {len(results['sent'])} sent, "
        f"{len(results['failed'])} failed, {len(results['skipped'])} skipped"
    )
    return results


def test_smtp_connection(config: Dict) -> Dict:
    """Test SMTP configuration. Returns status dict."""
    try:
        server = create_smtp_connection(config)
        server.quit()
        return {'success': True, 'message': 'SMTP connection successful'}
    except smtplib.SMTPAuthenticationError:
        return {'success': False, 'message': 'Authentication failed. Check email/password.'}
    except smtplib.SMTPConnectError as e:
        return {'success': False, 'message': f'Cannot connect to SMTP server: {str(e)}'}
    except Exception as e:
        return {'success': False, 'message': str(e)}
