"""
test_task_manager.py
----------------------
Unit tests for task_manager.py's validation layer and CRUD wrapper.
Uses a fresh temporary SQLite database per test so tests never touch
the real planner.db or affect each other.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import storage
import task_manager


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    """Point storage at a fresh temporary database for every test."""
    monkeypatch.setattr(storage, "DB_PATH", tmp_path / "test_planner.db")
    storage.init_db()
    yield


def test_create_task_valid():
    task_id = task_manager.create_task(
        title="Wash car", task_type="outdoor", priority="high",
        scheduled_date="2026-09-20",
    )
    task = storage.get_task(task_id)
    assert task["title"] == "Wash car"
    assert task["task_type"] == "outdoor"
    assert task["priority"] == "high"
    assert task["status"] == "pending"


def test_create_task_empty_title_rejected():
    with pytest.raises(task_manager.ValidationError):
        task_manager.create_task(title="   ", task_type="outdoor")


def test_create_task_invalid_type_rejected():
    with pytest.raises(task_manager.ValidationError):
        task_manager.create_task(title="Read", task_type="sideways")


def test_create_task_invalid_priority_rejected():
    with pytest.raises(task_manager.ValidationError):
        task_manager.create_task(title="Read", task_type="indoor", priority="urgent")


def test_create_task_invalid_date_rejected():
    with pytest.raises(task_manager.ValidationError):
        task_manager.create_task(title="Read", task_type="indoor", scheduled_date="20-09-2026")


def test_list_tasks_filters_by_status_and_type():
    id1 = task_manager.create_task(title="Jog", task_type="outdoor")
    id2 = task_manager.create_task(title="Read", task_type="indoor")
    task_manager.mark_complete(id1)

    completed = task_manager.list_tasks(status="completed")
    assert len(completed) == 1
    assert completed[0]["id"] == id1

    outdoor = task_manager.list_tasks(task_type="outdoor")
    assert len(outdoor) == 1
    assert outdoor[0]["id"] == id1

    indoor_pending = task_manager.list_tasks(status="pending", task_type="indoor")
    assert len(indoor_pending) == 1
    assert indoor_pending[0]["id"] == id2


def test_mark_complete_updates_status():
    task_id = task_manager.create_task(title="Study", task_type="indoor")
    task_manager.mark_complete(task_id)
    task = storage.get_task(task_id)
    assert task["status"] == "completed"


def test_mark_complete_nonexistent_task_raises():
    with pytest.raises(task_manager.ValidationError):
        task_manager.mark_complete(99999)


def test_remove_task_deletes_it():
    task_id = task_manager.create_task(title="Temp task", task_type="indoor")
    task_manager.remove_task(task_id)
    assert storage.get_task(task_id) is None


def test_remove_nonexistent_task_raises():
    with pytest.raises(task_manager.ValidationError):
        task_manager.remove_task(99999)


def test_edit_task_updates_fields():
    task_id = task_manager.create_task(title="Draft", task_type="indoor", priority="low")
    task_manager.edit_task(task_id, priority="high", title="Final draft")
    task = storage.get_task(task_id)
    assert task["priority"] == "high"
    assert task["title"] == "Final draft"


def test_edit_task_invalid_field_value_raises():
    task_id = task_manager.create_task(title="Draft", task_type="indoor")
    with pytest.raises(task_manager.ValidationError):
        task_manager.edit_task(task_id, priority="extreme")
