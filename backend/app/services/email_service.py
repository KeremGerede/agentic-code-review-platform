import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List

from app.core.config import settings

logger = logging.getLogger(__name__)

SEVERITY_EMOJI = {
    "critical": "🔴",
    "high": "🟠",
    "warning": "🟡",
    "info": "⚪",
}

RISK_COLOR = {
    "critical": "#dc2626",
    "high": "#ea580c",
    "medium": "#d97706",
    "low": "#16a34a",
}


def _resolve_recipients(notification_emails: str | None) -> List[str]:
    if notification_emails:
        emails = [e.strip() for e in notification_emails.split(",") if e.strip()]
        if emails:
            return emails
    return settings.recipient_emails


def _build_html(run_data: dict, findings: list, repository_data: dict) -> str:
    risk = run_data.get("risk_level", "low")
    risk_color = RISK_COLOR.get(risk, "#6b7280")

    findings_html = ""
    if not findings:
        findings_html = """
        <div style="background:#f0fdf4;border-left:4px solid #16a34a;padding:16px;border-radius:4px;margin-top:16px;">
            ✅ <strong>No rule violations were found in this push.</strong>
        </div>"""
    else:
        # Group by severity
        from collections import defaultdict
        grouped = defaultdict(list)
        for f in findings:
            grouped[f.get("severity", "info")].append(f)

        for sev in ["critical", "high", "warning", "info"]:
            group = grouped.get(sev, [])
            if not group:
                continue
            emoji = SEVERITY_EMOJI.get(sev, "⚪")
            color = RISK_COLOR.get(sev, "#6b7280") if sev in RISK_COLOR else "#6b7280"
            findings_html += f"""
            <h3 style="color:{color};margin-top:24px;">{emoji} {sev.upper()} ({len(group)})</h3>"""
            for f in group:
                snippet = ""
                if f.get("code_snippet"):
                    snippet = f"""
                    <pre style="background:#1e1e1e;color:#d4d4d4;padding:12px;border-radius:4px;overflow-x:auto;font-size:12px;">{f['code_snippet']}</pre>"""
                line_info = f" · Line {f['line_number']}" if f.get("line_number") else ""
                findings_html += f"""
                <div style="background:#f9fafb;border:1px solid #e5e7eb;border-radius:6px;padding:16px;margin:8px 0;">
                    <div style="font-weight:600;margin-bottom:4px;">📄 {f['file_path']}{line_info}</div>
                    <div style="color:#374151;margin-bottom:4px;"><strong>Rule:</strong> {f['rule_title']} &nbsp;·&nbsp; <em>{f.get('category','')}</em></div>
                    <div style="margin-bottom:4px;"><strong>Issue:</strong> {f['issue']}</div>
                    <div style="margin-bottom:4px;"><strong>Explanation:</strong> {f['explanation']}</div>
                    <div style="margin-bottom:4px;"><strong>Suggestion:</strong> {f['suggestion']}</div>
                    {snippet}
                </div>"""

    commit_short = run_data.get("commit_sha", "")[:7]

    return f"""
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>Code Analysis Report</title></head>
<body style="font-family:system-ui,sans-serif;max-width:860px;margin:0 auto;padding:24px;color:#111827;">
  <div style="background:{risk_color};color:#fff;padding:20px 24px;border-radius:8px 8px 0 0;">
    <h1 style="margin:0;font-size:20px;">🔍 Code Analysis Report</h1>
    <div style="margin-top:4px;opacity:0.9;">{repository_data.get('full_name')} — {run_data.get('branch')}</div>
  </div>

  <div style="border:1px solid #e5e7eb;border-top:none;padding:20px 24px;border-radius:0 0 8px 8px;">
    <table style="width:100%;border-collapse:collapse;margin-bottom:16px;">
      <tr>
        <td style="padding:6px 0;color:#6b7280;width:180px;">Repository</td>
        <td style="padding:6px 0;font-weight:500;">{repository_data.get('full_name')}</td>
      </tr>
      <tr>
        <td style="padding:6px 0;color:#6b7280;">Branch</td>
        <td style="padding:6px 0;">{run_data.get('branch')}</td>
      </tr>
      <tr>
        <td style="padding:6px 0;color:#6b7280;">Commit</td>
        <td style="padding:6px 0;font-family:monospace;">{commit_short}</td>
      </tr>
      <tr>
        <td style="padding:6px 0;color:#6b7280;">Author</td>
        <td style="padding:6px 0;">{run_data.get('author', 'N/A')}</td>
      </tr>
      <tr>
        <td style="padding:6px 0;color:#6b7280;">Risk Level</td>
        <td style="padding:6px 0;"><span style="background:{risk_color};color:#fff;padding:2px 10px;border-radius:999px;font-size:13px;">{risk.upper()}</span></td>
      </tr>
      <tr>
        <td style="padding:6px 0;color:#6b7280;">Files Analyzed</td>
        <td style="padding:6px 0;">{run_data.get('total_files_analyzed', 0)}</td>
      </tr>
      <tr>
        <td style="padding:6px 0;color:#6b7280;">Total Findings</td>
        <td style="padding:6px 0;">{run_data.get('total_findings', 0)}</td>
      </tr>
    </table>

    <div style="background:#f3f4f6;padding:14px;border-radius:6px;margin-bottom:16px;">
      <strong>Summary:</strong><br>{run_data.get('summary', '')}
    </div>

    <h2 style="font-size:16px;margin-bottom:8px;">Findings</h2>
    {findings_html}
  </div>
  <div style="text-align:center;color:#9ca3af;font-size:12px;margin-top:16px;">
    Generated by AI Code Review Agent
  </div>
</body>
</html>
"""


def _build_plaintext(run_data: dict, findings: list, repository_data: dict) -> str:
    lines = [
        "=" * 60,
        "CODE ANALYSIS REPORT",
        "=" * 60,
        f"Repository : {repository_data.get('full_name')}",
        f"Branch     : {run_data.get('branch')}",
        f"Commit     : {run_data.get('commit_sha', '')[:7]}",
        f"Author     : {run_data.get('author', 'N/A')}",
        f"Risk Level : {run_data.get('risk_level', '').upper()}",
        f"Files      : {run_data.get('total_files_analyzed', 0)}",
        f"Findings   : {run_data.get('total_findings', 0)}",
        "",
        "SUMMARY",
        "-" * 40,
        run_data.get("summary", ""),
        "",
    ]

    if not findings:
        lines.append("✅ No rule violations were found in this push.")
    else:
        lines.append("FINDINGS")
        lines.append("-" * 40)
        for i, f in enumerate(findings, 1):
            line_info = f" (line {f['line_number']})" if f.get("line_number") else ""
            lines += [
                f"{i}. [{f.get('severity','').upper()}] {f['file_path']}{line_info}",
                f"   Rule       : {f['rule_title']}",
                f"   Category   : {f.get('category','')}",
                f"   Issue      : {f['issue']}",
                f"   Explanation: {f['explanation']}",
                f"   Suggestion : {f['suggestion']}",
                "",
            ]

    return "\n".join(lines)


def send_report(run_data: dict, findings: list, repository_data: dict) -> None:
    """
    Build and send the analysis email report.
    Raises on SMTP failure — caller is responsible for catching and recording errors.
    """
    recipients = _resolve_recipients(repository_data.get("notification_emails"))
    if not recipients:
        logger.warning("No email recipients configured. Skipping email.")
        return

    risk = run_data.get("risk_level", "low").upper()
    full_name = repository_data.get("full_name", "unknown/repo")
    subject = f"[Code Analysis Report] {full_name} - {risk}"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_FROM_EMAIL
    msg["To"] = ", ".join(recipients)

    plaintext = _build_plaintext(run_data, findings, repository_data)
    html = _build_html(run_data, findings, repository_data)

    msg.attach(MIMEText(plaintext, "plain", "utf-8"))
    msg.attach(MIMEText(html, "html", "utf-8"))

    logger.info(
        "Sending report email to %s (subject: %s)",
        recipients, subject,
    )

    if settings.SMTP_USE_TLS:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.sendmail(settings.SMTP_FROM_EMAIL, recipients, msg.as_string())
    else:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.sendmail(settings.SMTP_FROM_EMAIL, recipients, msg.as_string())

    logger.info("Report email sent successfully.")
