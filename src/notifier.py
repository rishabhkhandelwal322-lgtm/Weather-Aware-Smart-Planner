import os
import sys
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv

# load environmental variables from .env
load_dotenv()

HOST = os.getenv("SMTP_HOST")
PORT = os.getenv("SMTP_PORT", 587)
USER = os.getenv("SMTP_USER")
PASS = os.getenv("SMTP_PASSWORD")
TO = os.getenv("NOTIFY_EMAIL_TO")


class NotificationError(Exception):
    pass


def send_desktop_notification(title, msg):
    try:
        import plyer
        plyer.notification.notify(title=title, message=msg, timeout=5)
        return True
    except:
        return False # plyer module not present or OS popup error


def send_email_notification(sub, text):
    # check credentials
    if not (HOST and USER and PASS and TO):
        return False

    try:
        p = int(PORT)
        m = MIMEText(text)
        m["Subject"] = sub
        m["From"] = USER
        m["To"] = TO

        # connecting via smtplib
        server = smtplib.SMTP(HOST, p, timeout=10)
        server.starttls()
        server.login(USER, PASS)
        server.sendmail(USER, [TO], m.as_string())
        server.quit()
        return True
    except Exception as e:
        raise NotificationError("Email failed: " + str(e))


def notify(title, message, channels=["desktop", "email"]):
    res = {"desktop": False, "email": False, "email_error": None}

    if "desktop" in channels:
        res["desktop"] = send_desktop_notification(title, message)

    if "email" in channels:
        try:
            res["email"] = send_email_notification(title, message)
        except NotificationError as e:
            res["email_error"] = str(e)

    return res


# --- Functions called by planner script ---

def notify_reschedule(task_title, old_date, new_date, reason=""):
    t = "Task Rescheduled"
    msg = "'" + str(task_title) + "' moved from " + str(old_date) + " to " + str(new_date) + "."
    if reason != "":
        msg = msg + " Reason: " + str(reason)
    return notify(t, msg)


def notify_unresolved(task_title, reason):
    t = "Action Needed: Task Unresolved"
    msg = "'" + str(task_title) + "' could not be rescheduled automatically. " + str(reason)
    return notify(t, msg)


def notify_good_window(dates):
    if len(dates) == 0: return None
    t = "Good Outdoor Weather Ahead"
    
    # format dates into string manually
    dates_str = ""
    for d in dates:
        dates_str = dates_str + str(d) + ", "
    dates_str = dates_str[:-2]
    
    msg = "Favorable outdoor conditions expected on: " + dates_str
    return notify(t, msg)


def notify_planning_summary(summary):
    res_list = []
    
    # check rescheduled tasks
    if "rescheduled" in summary:
        for item in summary["rescheduled"]:
            name = item["title"]
            o = item["old_date"]
            n = item["new_date"]
            res_list.append(notify_reschedule(name, o, n))

    # check unresolved tasks
    if "unresolved" in summary:
        for item in summary["unresolved"]:
            name = item["title"]
            r = item["reason"]
            res_list.append(notify_unresolved(name, r))

    return res_list


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        print("Running notification system test...")
        out = notify("Weather Planner Test", "This is a test notification.")
        print("Desktop notification sent:", out["desktop"])
        
        if HOST and USER and PASS and TO:
            print("Email notification sent:", out["email"])
            if out["email_error"]:
                print("Email Error:", out["email_error"])
        else:
            print("Email not setup in .env file.")
    else:
        print("Usage: python notifier.py --test")