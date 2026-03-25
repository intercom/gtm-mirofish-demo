"""Tests for app.models.task — Task, TaskStatus, TaskManager."""

import threading
import pytest

from app.models.task import Task, TaskStatus, TaskManager


class TestTaskStatus:
    def test_enum_values(self):
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.PROCESSING.value == "processing"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.FAILED.value == "failed"


class TestTask:
    def test_to_dict(self):
        from datetime import datetime
        now = datetime.now()
        task = Task(
            task_id="t1",
            task_type="build",
            status=TaskStatus.PENDING,
            created_at=now,
            updated_at=now,
            progress=50,
            message="halfway",
        )
        d = task.to_dict()
        assert d["task_id"] == "t1"
        assert d["status"] == "pending"
        assert d["progress"] == 50
        assert d["message"] == "halfway"
        assert d["result"] is None
        assert d["error"] is None


class TestTaskManager:
    def test_is_singleton(self):
        a = TaskManager()
        b = TaskManager()
        assert a is b

    def test_create_and_get_task(self):
        tm = TaskManager()
        tid = tm.create_task("test_type", metadata={"key": "val"})
        task = tm.get_task(tid)
        assert task is not None
        assert task.task_type == "test_type"
        assert task.status == TaskStatus.PENDING
        assert task.metadata == {"key": "val"}

    def test_get_nonexistent_returns_none(self):
        tm = TaskManager()
        assert tm.get_task("nonexistent-id") is None

    def test_update_task(self):
        tm = TaskManager()
        tid = tm.create_task("t")
        tm.update_task(tid, status=TaskStatus.PROCESSING, progress=30, message="working")
        task = tm.get_task(tid)
        assert task.status == TaskStatus.PROCESSING
        assert task.progress == 30
        assert task.message == "working"

    def test_complete_task(self):
        tm = TaskManager()
        tid = tm.create_task("t")
        tm.complete_task(tid, result={"graph_id": "g1"})
        task = tm.get_task(tid)
        assert task.status == TaskStatus.COMPLETED
        assert task.progress == 100
        assert task.result == {"graph_id": "g1"}

    def test_fail_task(self):
        tm = TaskManager()
        tid = tm.create_task("t")
        tm.fail_task(tid, error="something broke")
        task = tm.get_task(tid)
        assert task.status == TaskStatus.FAILED
        assert task.error == "something broke"

    def test_list_tasks_all(self):
        tm = TaskManager()
        tm.create_task("a")
        tm.create_task("b")
        tm.create_task("a")
        tasks = tm.list_tasks()
        assert len(tasks) == 3

    def test_list_tasks_filtered(self):
        tm = TaskManager()
        tm.create_task("build")
        tm.create_task("report")
        tm.create_task("build")
        build_tasks = tm.list_tasks(task_type="build")
        assert len(build_tasks) == 2
        assert all(t["task_type"] == "build" for t in build_tasks)

    def test_cleanup_old_tasks(self):
        from datetime import datetime, timedelta
        tm = TaskManager()
        tid = tm.create_task("old")
        task = tm.get_task(tid)
        task.created_at = datetime.now() - timedelta(hours=48)
        task.status = TaskStatus.COMPLETED
        tm.cleanup_old_tasks(max_age_hours=24)
        assert tm.get_task(tid) is None

    def test_cleanup_keeps_recent_tasks(self):
        tm = TaskManager()
        tid = tm.create_task("recent")
        tm.complete_task(tid, result={})
        tm.cleanup_old_tasks(max_age_hours=24)
        assert tm.get_task(tid) is not None

    def test_thread_safety(self):
        tm = TaskManager()
        ids = []
        errors = []

        def create_tasks():
            try:
                for _ in range(50):
                    ids.append(tm.create_task("concurrent"))
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=create_tasks) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors
        assert len(ids) == 200
        assert len(tm.list_tasks()) == 200
