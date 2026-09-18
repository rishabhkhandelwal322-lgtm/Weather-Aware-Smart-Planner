"""
task_manager.py
-----------------
User-facing task management layer on top of storage.py.

Adds input validation, date parsing, and friendly formatting on top
of the raw CRUD in storage.py, and exposes a simple CLI so tasks can
be managed directly from the terminal without the dashboard.

    python task_manager.py add "Wash car" outdoor --priority high --date 2026-09-20
    python task_manager.py list
    python task_manager.py list --status pending --type outdoor
    python task_manager.py complete 3
    python task_manager.py delete 3
"""

import argparse
from datetime import datetime

import storage

VALID_TYPES = ("outdoor", "indoor")
VALID_PRIORITIES = ("low", "medium", "high")


class ValidationError(Exception):
    """Raised when user-supplied task data fails validation."""


def _validate_date(date_str):
    """Ensure a date string is in YYYY-MM-DD format. Returns it unchanged if valid."""
    if date_str is None:
        return None
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        raise ValidationError(f"Invalid date '{date_str}'. Use YYYY-MM-DD format.")
    return date_str


def _validate_type(task_type):
    if task_type not in VALID_TYPES:
        raise ValidationError(f"task_type must be one of {VALID_TYPES}, got '{task_type}'")
    return task_type


def _validate_priority(priority):
    if priority not in VALID_PRIORITIES:
        raise ValidationError(f"priority must be one of {VALID_PRIORITIES}, got '{priority}'")
    return priority


def create_task(title, task_type, description="", priority="medium",
                 deadline=None, scheduled_date=None):
    """Validate inputs and create a new task. Returns the new task's id."""
    if not title or not title.strip():
        raise ValidationError("Task title cannot be empty.")

    task_type = _validate_type(task_type)
    priority = _validate_priority(priority)
    deadline = _validate_date(deadline)
    scheduled_date = _validate_date(scheduled_date)

    return storage.add_task(
        title=title.strip(),
        task_type=task_type,
        description=description,
        priority=priority,
        deadline=deadline,
        scheduled_date=scheduled_date,
    )


def list_tasks(status=None, task_type=None):
    """Return tasks matching the given filters, already sorted by storage.py."""
    return storage.get_tasks(status=status, task_type=task_type)


def mark_complete(task_id):
    task = storage.get_task(task_id)
    if not task:
        raise ValidationError(f"No task found with id {task_id}")
    storage.complete_task(task_id)


def remove_task(task_id):
    task = storage.get_task(task_id)
    if not task:
        raise ValidationError(f"No task found with id {task_id}")
    storage.delete_task(task_id)


def edit_task(task_id, **fields):
    """Validate and apply an update to an existing task."""
    task = storage.get_task(task_id)
    if not task:
        raise ValidationError(f"No task found with id {task_id}")

    if "task_type" in fields:
        fields["task_type"] = _validate_type(fields["task_type"])
    if "priority" in fields:
        fields["priority"] = _validate_priority(fields["priority"])
    if "deadline" in fields:
        fields["deadline"] = _validate_date(fields["deadline"])
    if "scheduled_date" in fields:
        fields["scheduled_date"] = _validate_date(fields["scheduled_date"])

    storage.update_task(task_id, **fields)


def format_task_line(task):
    """One-line human-readable representation of a task, for CLI/logging output."""
    status_marker = {
        "pending": " ",
        "rescheduled": "R",
        "completed": "x",
        "cancelled": "-",
    }.get(task["status"], "?")

    date_part = task["scheduled_date"] or "unscheduled"
    return (f"[{status_marker}] #{task['id']:<3} {task['title']:<30} "
            f"({task['task_type']}, {task['priority']} priority) -> {date_part}")


# --------------------------------------------------------------- CLI ----

def _build_parser():
    parser = argparse.ArgumentParser(description="Manage Weather-Aware Smart Planner tasks.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_p = subparsers.add_parser("add", help="Add a new task")
    add_p.add_argument("title")
    add_p.add_argument("task_type", choices=VALID_TYPES)
    add_p.add_argument("--description", default="")
    add_p.add_argument("--priority", choices=VALID_PRIORITIES, default="medium")
    add_p.add_argument("--deadline", help="YYYY-MM-DD")
    add_p.add_argument("--date", dest="scheduled_date", help="YYYY-MM-DD, when the task is scheduled for")

    list_p = subparsers.add_parser("list", help="List tasks")
    list_p.add_argument("--status", choices=("pending", "rescheduled", "completed", "cancelled"))
    list_p.add_argument("--type", dest="task_type", choices=VALID_TYPES)

    complete_p = subparsers.add_parser("complete", help="Mark a task complete")
    complete_p.add_argument("task_id", type=int)

    delete_p = subparsers.add_parser("delete", help="Delete a task")
    delete_p.add_argument("task_id", type=int)

    return parser


def main():
    storage.init_db()
    parser = _build_parser()
    args = parser.parse_args()

    try:
        if args.command == "add":
            task_id = create_task(
                title=args.title,
                task_type=args.task_type,
                description=args.description,
                priority=args.priority,
                deadline=args.deadline,
                scheduled_date=args.scheduled_date,
            )
            print(f"Added task #{task_id}: {args.title}")

        elif args.command == "list":
            tasks = list_tasks(status=args.status, task_type=args.task_type)
            if not tasks:
                print("No tasks found.")
            for task in tasks:
                print(format_task_line(task))

        elif args.command == "complete":
            mark_complete(args.task_id)
            print(f"Task #{args.task_id} marked complete.")

        elif args.command == "delete":
            remove_task(args.task_id)
            print(f"Task #{args.task_id} deleted.")

    except ValidationError as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
