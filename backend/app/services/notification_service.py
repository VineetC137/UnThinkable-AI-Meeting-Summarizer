"""
Notification service for sending emails.
"""

from datetime import datetime
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from app.core.config import settings
from app.core.logging import get_logger
from app.models.meeting import Meeting

logger = get_logger(__name__)


class NotificationService:
    """Service to handle sending email notifications and summaries."""
    
    def __init__(self):
        # Configure SMTP connection
        self.config = ConnectionConfig(
            MAIL_USERNAME=settings.SMTP_USERNAME or "",
            MAIL_PASSWORD=settings.SMTP_PASSWORD or "",
            MAIL_FROM=settings.EMAIL_FROM,
            MAIL_PORT=settings.SMTP_PORT,
            MAIL_SERVER=settings.SMTP_SERVER,
            MAIL_STARTTLS=True,
            MAIL_SSL_TLS=False,
            USE_CREDENTIALS=bool(settings.SMTP_USERNAME),
            VALIDATE_CERTS=False
        )
        self.fastmail = FastMail(self.config)
        
    async def send_meeting_summary_email(self, meeting: Meeting, recipient_email: str) -> bool:
        """
        Send meeting summary report via email to the recipient.
        """
        try:
            # Build HTML body
            html_content = self._build_meeting_summary_html(meeting)
            
            message = MessageSchema(
                subject=f"Meeting Summary: {meeting.title}",
                recipients=[recipient_email],
                body=html_content,
                subtype=MessageType.html
            )
            
            await self.fastmail.send_message(message)
            logger.info(f"Meeting summary email sent to {recipient_email} for meeting {meeting.id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {recipient_email} for meeting {meeting.id}: {e}")
            return False
            
    def _build_meeting_summary_html(self, meeting: Meeting) -> str:
        """Build a clean, responsive HTML email for the meeting summary."""
        # Extract summaries and structured lists
        exec_summary = (
            meeting.summaries.get('executive_summary', 'No executive summary generated.') 
            if meeting.summaries else 'No summary generated.'
        )
        
        decisions_html = ""
        if meeting.key_decisions:
            decisions_html = "<h3>🔑 Key Decisions</h3><ul>"
            for decision in meeting.key_decisions:
                desc = decision.get('description', 'N/A')
                maker = f" (Maker: {decision['decision_maker']})" if decision.get('decision_maker') else ""
                decisions_html += f"<li><strong>{desc}</strong>{maker}</li>"
            decisions_html += "</ul>"
            
        actions_html = ""
        if meeting.action_items:
            actions_html = "<h3>📋 Action Items</h3><ul>"
            for item in meeting.action_items:
                desc = item.get('description', 'N/A')
                owner = f" - <em>Owner: {item['owner']}</em>" if item.get('owner') else ""
                deadline = f" (Deadline: {item['deadline']})" if item.get('deadline') else ""
                actions_html += f"<li>{desc}{owner}{deadline}</li>"
            actions_html += "</ul>"
            
        risks_html = ""
        if meeting.risks:
            risks_html = "<h3>⚠️ Risks & Concerns</h3><ul>"
            for risk in meeting.risks:
                desc = risk.get('description', 'N/A')
                impact = f" (Impact: {risk['impact']})" if risk.get('impact') else ""
                risks_html += f"<li>{desc}{impact}</li>"
            risks_html += "</ul>"
            
        questions_html = ""
        if meeting.open_questions:
            questions_html = "<h3>❓ Open Questions</h3><ul>"
            for question in meeting.open_questions:
                q = question.get('question', 'N/A')
                assigned = f" - <em>Assigned: {question['assigned_to']}</em>" if question.get('assigned_to') else ""
                questions_html += f"<li>{q}{assigned}</li>"
            questions_html += "</ul>"

        # Combine into complete responsive HTML page
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{
                    font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
                    line-height: 1.6;
                    color: #333333;
                    background-color: #f9f9f9;
                    margin: 0;
                    padding: 20px;
                }}
                .container {{
                    max-width: 600px;
                    background: #ffffff;
                    margin: 0 auto;
                    padding: 30px;
                    border-radius: 8px;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.05);
                    border: 1px solid #e1e1e1;
                }}
                h1 {{
                    font-size: 24px;
                    color: #1a0dab;
                    margin-top: 0;
                    border-bottom: 2px solid #f0f0f0;
                    padding-bottom: 10px;
                }}
                h2 {{
                    font-size: 18px;
                    color: #2b2b2b;
                    margin-top: 20px;
                }}
                h3 {{
                    font-size: 16px;
                    color: #4a4a4a;
                    margin-top: 20px;
                    border-bottom: 1px solid #eeeeee;
                    padding-bottom: 5px;
                }}
                p {{
                    margin: 0 0 15px;
                    font-size: 14px;
                }}
                ul {{
                    padding-left: 20px;
                    margin: 0 0 20px;
                    font-size: 14px;
                }}
                li {{
                    margin-bottom: 8px;
                }}
                .metadata {{
                    font-size: 12px;
                    color: #888888;
                    margin-bottom: 20px;
                    background-color: #f5f5f5;
                    padding: 10px;
                    border-radius: 4px;
                }}
                .footer {{
                    margin-top: 30px;
                    font-size: 11px;
                    color: #aaaaaa;
                    text-align: center;
                    border-top: 1px solid #eeeeee;
                    padding-top: 15px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>📝 Meeting Summary</h1>
                <div class="metadata">
                    <strong>Meeting Title:</strong> {meeting.title}<br>
                    <strong>Date Processed:</strong> {datetime.utcnow().strftime('%Y-%m-%d')}<br>
                    <strong>Speakers Detected:</strong> {meeting.num_speakers or 'N/A'}
                </div>
                
                <h2>Executive Summary</h2>
                <p>{exec_summary.replace('\n', '<br>')}</p>
                
                {decisions_html}
                {actions_html}
                {risks_html}
                {questions_html}
                
                <div class="footer">
                    Sent automatically by the Enterprise Meeting Summarizer.
                </div>
            </div>
        </body>
        </html>
        """
        return html


# Create global service instance
notification_service = NotificationService()
