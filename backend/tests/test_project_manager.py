"""Tests for app.models.project — Project and ProjectManager."""

import os
import pytest
from unittest.mock import patch, MagicMock

from app.models.project import Project, ProjectStatus, ProjectManager


@pytest.fixture(autouse=True)
def isolate_project_dir(tmp_path):
    """Redirect ProjectManager storage to a temp directory."""
    projects_dir = str(tmp_path / "projects")
    with patch.object(ProjectManager, "PROJECTS_DIR", projects_dir):
        yield projects_dir


class TestProjectStatus:
    def test_enum_values(self):
        assert ProjectStatus.CREATED.value == "created"
        assert ProjectStatus.GRAPH_COMPLETED.value == "graph_completed"
        assert ProjectStatus.FAILED.value == "failed"


class TestProject:
    def test_to_dict_and_from_dict_roundtrip(self):
        p = Project(
            project_id="proj_abc",
            name="Test",
            status=ProjectStatus.CREATED,
            created_at="2025-01-01T00:00:00",
            updated_at="2025-01-01T00:00:00",
            chunk_size=300,
            chunk_overlap=30,
        )
        d = p.to_dict()
        assert d["project_id"] == "proj_abc"
        assert d["status"] == "created"
        assert d["chunk_size"] == 300

        restored = Project.from_dict(d)
        assert restored.project_id == "proj_abc"
        assert restored.status == ProjectStatus.CREATED
        assert restored.chunk_size == 300

    def test_from_dict_defaults(self):
        p = Project.from_dict({"project_id": "p1"})
        assert p.name == "Unnamed Project"
        assert p.status == ProjectStatus.CREATED
        assert p.chunk_size == 500


class TestProjectManager:
    def test_create_project(self):
        p = ProjectManager.create_project(name="My Project")
        assert p.project_id.startswith("proj_")
        assert p.name == "My Project"
        assert p.status == ProjectStatus.CREATED

    def test_get_project(self):
        p = ProjectManager.create_project(name="Get Me")
        fetched = ProjectManager.get_project(p.project_id)
        assert fetched is not None
        assert fetched.name == "Get Me"

    def test_get_nonexistent_returns_none(self):
        assert ProjectManager.get_project("nonexistent") is None

    def test_save_updates_project(self):
        p = ProjectManager.create_project()
        p.status = ProjectStatus.ONTOLOGY_GENERATED
        p.ontology = {"entity_types": []}
        ProjectManager.save_project(p)

        reloaded = ProjectManager.get_project(p.project_id)
        assert reloaded.status == ProjectStatus.ONTOLOGY_GENERATED
        assert reloaded.ontology == {"entity_types": []}

    def test_delete_project(self):
        p = ProjectManager.create_project()
        assert ProjectManager.delete_project(p.project_id) is True
        assert ProjectManager.get_project(p.project_id) is None

    def test_delete_nonexistent_returns_false(self):
        assert ProjectManager.delete_project("nonexistent") is False

    def test_list_projects(self):
        ProjectManager.create_project(name="A")
        ProjectManager.create_project(name="B")
        projects = ProjectManager.list_projects()
        assert len(projects) == 2

    def test_list_projects_respects_limit(self):
        for i in range(5):
            ProjectManager.create_project(name=f"P{i}")
        assert len(ProjectManager.list_projects(limit=3)) == 3

    def test_save_and_get_extracted_text(self):
        p = ProjectManager.create_project()
        ProjectManager.save_extracted_text(p.project_id, "Hello extracted world")
        text = ProjectManager.get_extracted_text(p.project_id)
        assert text == "Hello extracted world"

    def test_get_extracted_text_missing_returns_none(self):
        p = ProjectManager.create_project()
        assert ProjectManager.get_extracted_text(p.project_id) is None

    def test_save_file_to_project(self):
        p = ProjectManager.create_project()
        mock_file = MagicMock()
        mock_file.save = MagicMock(side_effect=lambda path: open(path, "w").close())
        info = ProjectManager.save_file_to_project(p.project_id, mock_file, "report.pdf")
        assert info["original_filename"] == "report.pdf"
        assert info["saved_filename"].endswith(".pdf")
        assert os.path.exists(info["path"])

    def test_get_project_files(self):
        p = ProjectManager.create_project()
        # Initially no files
        assert ProjectManager.get_project_files(p.project_id) == []

        # Save a file
        mock_file = MagicMock()
        mock_file.save = MagicMock(side_effect=lambda path: open(path, "w").close())
        ProjectManager.save_file_to_project(p.project_id, mock_file, "doc.txt")
        files = ProjectManager.get_project_files(p.project_id)
        assert len(files) == 1
