"""
Email Alert Service

Sends notifications about:
- Projects that become delayed or over budget
- Weekly digest summaries
- Critical threshold breaches
"""

import os
import smtplib
import sqlite3
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class AlertConfig:
    """Email alert configuration."""
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    from_email: str = ""
    to_emails: List[str] = None
    enabled: bool = False

    @classmethod
    def from_env(cls) -> 'AlertConfig':
        """Load configuration from environment variables."""
        to_emails_str = os.environ.get('ALERT_EMAIL_TO', '')
        to_emails = [e.strip() for e in to_emails_str.split(',') if e.strip()]

        return cls(
            smtp_host=os.environ.get('SMTP_HOST', ''),
            smtp_port=int(os.environ.get('SMTP_PORT', '587')),
            smtp_user=os.environ.get('SMTP_USER', ''),
            smtp_password=os.environ.get('SMTP_PASSWORD', ''),
            from_email=os.environ.get('SMTP_USER', 'alerts@surtax-oversight.local'),
            to_emails=to_emails,
            enabled=bool(os.environ.get('SMTP_HOST'))
        )


class EmailAlertService:
    """Handles sending email alerts for the oversight dashboard."""

    def __init__(self, config: Optional[AlertConfig] = None):
        self.config = config or AlertConfig.from_env()

    def is_enabled(self) -> bool:
        """Check if email alerts are configured and enabled."""
        return (
            self.config.enabled
            and self.config.smtp_host
            and self.config.to_emails
        )

    def send_email(
        self,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None
    ) -> bool:
        """
        Send an email alert.

        Returns:
            True if sent successfully, False otherwise
        """
        if not self.is_enabled():
            return False

        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"[Surtax Oversight] {subject}"
            msg['From'] = self.config.from_email
            msg['To'] = ', '.join(self.config.to_emails)

            # Add text version (fallback)
            if text_body:
                msg.attach(MIMEText(text_body, 'plain'))

            # Add HTML version
            msg.attach(MIMEText(html_body, 'html'))

            # Send via SMTP
            with smtplib.SMTP(self.config.smtp_host, self.config.smtp_port) as server:
                server.starttls()
                if self.config.smtp_user and self.config.smtp_password:
                    server.login(self.config.smtp_user, self.config.smtp_password)
                server.send_message(msg)

            return True

        except Exception as e:
            print(f"Email send error: {e}")
            return False

    def send_delay_alert(
        self,
        project_title: str,
        school_name: str,
        delay_days: int,
        original_date: str,
        current_date: str
    ) -> bool:
        """Send alert when a project becomes significantly delayed."""
        subject = f"Schedule Alert: {project_title}"

        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: #DC2626; color: white; padding: 20px; border-radius: 8px 8px 0 0;">
                <h2 style="margin: 0;">Schedule Delay Alert</h2>
            </div>
            <div style="padding: 20px; background: #FEF2F2; border: 1px solid #FECACA;">
                <h3 style="color: #991B1B; margin-top: 0;">{project_title}</h3>
                <table style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="padding: 8px 0; color: #666;">School:</td>
                        <td style="padding: 8px 0;"><strong>{school_name}</strong></td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; color: #666;">Days Behind:</td>
                        <td style="padding: 8px 0;"><strong style="color: #DC2626;">{delay_days} days</strong></td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; color: #666;">Original Completion:</td>
                        <td style="padding: 8px 0;">{original_date}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; color: #666;">Revised Completion:</td>
                        <td style="padding: 8px 0;">{current_date}</td>
                    </tr>
                </table>
                <p style="margin-top: 20px; color: #666;">
                    <a href="http://127.0.0.1:5847/concerns" style="color: #2563EB;">View all concerns in the dashboard</a>
                </p>
            </div>
            <div style="padding: 15px; background: #F3F4F6; color: #666; font-size: 12px; text-align: center;">
                Florida School Surtax Oversight Dashboard
            </div>
        </body>
        </html>
        """

        text_body = f"""
Schedule Delay Alert

Project: {project_title}
School: {school_name}
Days Behind: {delay_days} days
Original Completion: {original_date}
Revised Completion: {current_date}

View the dashboard: http://127.0.0.1:5847/concerns
        """

        return self.send_email(subject, html_body, text_body)

    def send_budget_alert(
        self,
        project_title: str,
        school_name: str,
        original_budget: float,
        current_budget: float,
        variance_pct: float
    ) -> bool:
        """Send alert when a project goes over budget."""
        subject = f"Budget Alert: {project_title}"

        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: #F59E0B; color: white; padding: 20px; border-radius: 8px 8px 0 0;">
                <h2 style="margin: 0;">Budget Variance Alert</h2>
            </div>
            <div style="padding: 20px; background: #FFFBEB; border: 1px solid #FDE68A;">
                <h3 style="color: #92400E; margin-top: 0;">{project_title}</h3>
                <table style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="padding: 8px 0; color: #666;">School:</td>
                        <td style="padding: 8px 0;"><strong>{school_name}</strong></td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; color: #666;">Original Budget:</td>
                        <td style="padding: 8px 0;">${original_budget:,.2f}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; color: #666;">Current Budget:</td>
                        <td style="padding: 8px 0;"><strong>${current_budget:,.2f}</strong></td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; color: #666;">Variance:</td>
                        <td style="padding: 8px 0;"><strong style="color: #F59E0B;">+{variance_pct:.1f}%</strong></td>
                    </tr>
                </table>
                <p style="margin-top: 20px; color: #666;">
                    <a href="http://127.0.0.1:5847/concerns" style="color: #2563EB;">View all concerns in the dashboard</a>
                </p>
            </div>
            <div style="padding: 15px; background: #F3F4F6; color: #666; font-size: 12px; text-align: center;">
                Florida School Surtax Oversight Dashboard
            </div>
        </body>
        </html>
        """

        text_body = f"""
Budget Variance Alert

Project: {project_title}
School: {school_name}
Original Budget: ${original_budget:,.2f}
Current Budget: ${current_budget:,.2f}
Variance: +{variance_pct:.1f}%

View the dashboard: http://127.0.0.1:5847/concerns
        """

        return self.send_email(subject, html_body, text_body)

    def send_weekly_digest(
        self,
        stats: Dict[str, Any],
        new_delays: List[Dict],
        new_over_budget: List[Dict],
        completed: List[Dict]
    ) -> bool:
        """Send weekly summary digest."""
        subject = f"Weekly Digest - {datetime.now().strftime('%B %d, %Y')}"

        delays_html = ""
        if new_delays:
            delays_html = "<ul>" + "".join([
                f"<li>{p['title']} - {p['delay_days']} days behind</li>"
                for p in new_delays
            ]) + "</ul>"
        else:
            delays_html = "<p style='color: #22C55E;'>No new schedule delays this week.</p>"

        budget_html = ""
        if new_over_budget:
            budget_html = "<ul>" + "".join([
                f"<li>{p['title']} - {p['variance_pct']:.1f}% over</li>"
                for p in new_over_budget
            ]) + "</ul>"
        else:
            budget_html = "<p style='color: #22C55E;'>No new budget overruns this week.</p>"

        completed_html = ""
        if completed:
            completed_html = "<ul>" + "".join([
                f"<li>{p['title']}</li>"
                for p in completed
            ]) + "</ul>"
        else:
            completed_html = "<p>No projects completed this week.</p>"

        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: #2563EB; color: white; padding: 20px; border-radius: 8px 8px 0 0;">
                <h2 style="margin: 0;">Weekly Surtax Oversight Digest</h2>
                <p style="margin: 5px 0 0 0; opacity: 0.8;">{datetime.now().strftime('%B %d, %Y')}</p>
            </div>

            <div style="padding: 20px; background: white; border: 1px solid #E5E7EB;">
                <!-- Stats Summary -->
                <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin-bottom: 20px;">
                    <div style="text-align: center; padding: 15px; background: #F3F4F6; border-radius: 8px;">
                        <div style="font-size: 24px; font-weight: bold; color: #2563EB;">{stats.get('total_projects', 0)}</div>
                        <div style="font-size: 12px; color: #666;">Total Projects</div>
                    </div>
                    <div style="text-align: center; padding: 15px; background: #FEF2F2; border-radius: 8px;">
                        <div style="font-size: 24px; font-weight: bold; color: #DC2626;">{stats.get('delayed_projects', 0)}</div>
                        <div style="font-size: 12px; color: #666;">Delayed</div>
                    </div>
                    <div style="text-align: center; padding: 15px; background: #FFFBEB; border-radius: 8px;">
                        <div style="font-size: 24px; font-weight: bold; color: #F59E0B;">{stats.get('over_budget_projects', 0)}</div>
                        <div style="font-size: 12px; color: #666;">Over Budget</div>
                    </div>
                </div>

                <!-- New Delays -->
                <h3 style="color: #DC2626; border-bottom: 1px solid #FECACA; padding-bottom: 5px;">
                    New Schedule Delays
                </h3>
                {delays_html}

                <!-- New Budget Issues -->
                <h3 style="color: #F59E0B; border-bottom: 1px solid #FDE68A; padding-bottom: 5px;">
                    New Budget Concerns
                </h3>
                {budget_html}

                <!-- Completed Projects -->
                <h3 style="color: #22C55E; border-bottom: 1px solid #BBF7D0; padding-bottom: 5px;">
                    Completed This Week
                </h3>
                {completed_html}

                <p style="margin-top: 20px; text-align: center;">
                    <a href="http://127.0.0.1:5847" style="display: inline-block; padding: 10px 20px; background: #2563EB; color: white; text-decoration: none; border-radius: 5px;">
                        Open Dashboard
                    </a>
                </p>
            </div>

            <div style="padding: 15px; background: #F3F4F6; color: #666; font-size: 12px; text-align: center;">
                Florida School Surtax Oversight Dashboard
            </div>
        </body>
        </html>
        """

        return self.send_email(subject, html_body)


def check_and_send_alerts(cursor: sqlite3.Cursor) -> Dict[str, int]:
    """
    Check for alert conditions and send notifications.

    Returns:
        Dictionary with counts of alerts sent by type
    """
    service = EmailAlertService()

    if not service.is_enabled():
        return {'status': 'disabled', 'reason': 'Email not configured'}

    sent = {
        'delay_alerts': 0,
        'budget_alerts': 0,
    }

    # Find projects that just became delayed (no previous alert sent)
    cursor.execute('''
        SELECT title, school_name, delay_days, original_end_date, current_end_date
        FROM contracts
        WHERE is_deleted = 0
        AND surtax_category IS NOT NULL
        AND is_delayed = 1
        AND delay_days >= 30
        AND (last_delay_alert_date IS NULL
             OR julianday('now') - julianday(last_delay_alert_date) > 7)
    ''')

    for row in cursor.fetchall():
        title, school, days, orig_date, curr_date = row
        if service.send_delay_alert(title, school or 'Unknown', days, orig_date or 'N/A', curr_date or 'N/A'):
            sent['delay_alerts'] += 1
            # Update alert timestamp
            cursor.execute('''
                UPDATE contracts SET last_delay_alert_date = date('now')
                WHERE title = ?
            ''', (title,))

    # Find projects that just went over budget
    cursor.execute('''
        SELECT title, school_name, original_amount, current_amount, budget_variance_pct
        FROM contracts
        WHERE is_deleted = 0
        AND surtax_category IS NOT NULL
        AND is_over_budget = 1
        AND budget_variance_pct >= 10
        AND (last_budget_alert_date IS NULL
             OR julianday('now') - julianday(last_budget_alert_date) > 7)
    ''')

    for row in cursor.fetchall():
        title, school, orig, curr, pct = row
        if service.send_budget_alert(title, school or 'Unknown', orig, curr, pct):
            sent['budget_alerts'] += 1
            cursor.execute('''
                UPDATE contracts SET last_budget_alert_date = date('now')
                WHERE title = ?
            ''', (title,))

    return sent
