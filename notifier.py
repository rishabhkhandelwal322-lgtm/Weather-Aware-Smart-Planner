"""
notifier.py
------------
Sends notifications when the planner reschedules a task or finds a
favorable outdoor window. Supports two channels, both optional and
independently configured via environment variables:

  - Desktop notifications (via plyer) -- works out of the box, no
    configuration needed, but only shows on the machine actually
    running the script.
  - Email (via smtplib) -- requires SMTP credentials in .env:
        SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, NOTIFY_EMAIL_TO

If email isn't configured, notifier silently skips it and falls back
to desktop only -- it never crashes the planning run just because
notifications aren't fully set up.
"""

import os
import smtplib
from email.mime.text import MIMEText

from dotenv import load_dotenv

load_dotenv()

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
NOTIFY_EMAIL_TO = os.getenv("NOTIFY_EMAIL_TO")


class NotificationError(Exception):
    """Raised when a notification channel fails to send."""


def _email_configured():
    return all([SMTP_HOST, SMTP_USER, SMTP_PASSWORD, NOTIFY_EMAIL_TO])


def send_desktop_notification(title, message):
    """
    Show a desktop popup notification. Fails silently (returns False)
    on platforms/environments where this isn't supported, rather than
    crashing the app -- desktop notifications are a nice-to-have.
    """
    try:
        from plyer import notification
        notification.notify(title=title, message=message, timeout=8)
        return True
    except Exception:
        return False


def send_email_notification(subject, body):
    """
    Send an email notification via SMTP. Raises NotificationError on
    failure. Returns True on success. If email isn't configured at
    all, returns False without raising (nothing to send).
    """
    if not _email_configured():
        return False

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = SMTP_USER
    msg["To"] = NOTIFY_EMAIL_TO

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, [NOTIFY_EMAIL_TO], msg.as_string())
        return True
    except (smtplib.SMTPException, OSError) as exc:
        raise NotificationError(f"Failed to send email: {exc}") from exc


def notify(title, message, channels=("desktop", "email")):
    """
    Send a notification through the requested channels. Returns a
    dict reporting which channels actually succeeded, so callers
    (e.g. planner.py) can log or display the outcome without the
    notifier ever raising and interrupting the planning cycle.
    """
    results = {"desktop": False, "email": False, "email_error": None}

    if "desktop" in channels:
        results["desktop"] = send_desktop_notification(title, message)

    if "email" in channels:
        try:
            results["email"] = send_email_notification(title, message)
        except NotificationError as exc:
            results["email_error"] = str(exc)

    return results


# ---------------------------------------------------- planner integration ----

def notify_reschedule(task_title, old_date, new_date, reason=""):
    """Notify the user that a task was automatically rescheduled."""
    title = "Task Rescheduled"
    message = f"'{task_title}' moved from {old_date} to {new_date}."
    if reason:
        message += f" Reason: {reason}"
    return notify(title, message)


def notify_unresolved(task_title, reason):
    """Notify the user that a task could NOT be automatically rescheduled."""
    title = "Action Needed: Task Unresolved"
    message = f"'{task_title}' could not be rescheduled automatically. {reason}"
    return notify(title, message)


def notify_good_window(dates):
    """Notify the user about upcoming favorable outdoor windows."""
    if not dates:
        return None
    title = "Good Outdoor Weather Ahead"
    message = f"Favorable outdoor conditions expected on: {', '.join(dates)}"
    return notify(title, message)


def notify_planning_summary(summary):
    """
    Convenience wrapper: takes the dict returned by
    planner.run_planning_cycle() and fires the appropriate
    notifications for every rescheduled/unresolved task.
    """
    outcomes = []
    for item in summary.get("rescheduled", []):
        outcomes.append(notify_reschedule(
            item["title"], item["old_date"], item["new_date"]
        ))
    for item in summary.get("unresolved", []):
        outcomes.append(notify_unresolved(item["title"], item["reason"]))
    return outcomes


if __name__ == "__main__":
    import sys

    if "--test" in sys.argv:
        print("Sending test notification...")
        result = notify("Weather Planner Test", "This is a test notification.")
        print(f"  Desktop: {'sent' if result['desktop'] else 'not available/failed'}")
        if _email_configured():
            print(f"  Email: {'sent' if result['email'] else 'failed - ' + str(result['email_error'])}")
        else:
            print("  Email: not configured (set SMTP_HOST, SMTP_USER, SMTP_PASSWORD, NOTIFY_EMAIL_TO in .env)")
    else:
        print("Usage: python notifier.py --test")
