"""Tests for app.services.ontology_generator — OntologyGenerator."""

import json
import pytest
from unittest.mock import MagicMock

from app.services.ontology_generator import OntologyGenerator


@pytest.fixture()
def mock_llm():
    return MagicMock()


@pytest.fixture()
def generator(mock_llm):
    return OntologyGenerator(llm_client=mock_llm)


class TestValidateAndProcess:
    """Test the _validate_and_process post-processing logic."""

    def test_adds_missing_fallback_types(self, generator):
        raw = {
            "entity_types": [
                {"name": "Student", "description": "A student"},
            ],
            "edge_types": [],
            "analysis_summary": "test",
        }
        result = generator._validate_and_process(raw)
        names = [e["name"] for e in result["entity_types"]]
        assert "Person" in names
        assert "Organization" in names

    def test_does_not_duplicate_existing_fallbacks(self, generator):
        raw = {
            "entity_types": [
                {"name": "Person", "description": "Person fallback"},
                {"name": "Organization", "description": "Org fallback"},
            ],
            "edge_types": [],
        }
        result = generator._validate_and_process(raw)
        person_count = sum(1 for e in result["entity_types"] if e["name"] == "Person")
        assert person_count == 1

    def test_caps_entity_types_at_10(self, generator):
        raw = {
            "entity_types": [
                {"name": f"Type{i}", "description": f"Type {i}"} for i in range(12)
            ],
            "edge_types": [],
        }
        result = generator._validate_and_process(raw)
        assert len(result["entity_types"]) <= 10

    def test_caps_edge_types_at_10(self, generator):
        raw = {
            "entity_types": [],
            "edge_types": [
                {"name": f"EDGE_{i}", "description": f"Edge {i}"} for i in range(15)
            ],
        }
        result = generator._validate_and_process(raw)
        assert len(result["edge_types"]) <= 10

    def test_truncates_long_descriptions(self, generator):
        raw = {
            "entity_types": [
                {"name": "Test", "description": "A" * 200},
            ],
            "edge_types": [
                {"name": "LONG", "description": "B" * 200},
            ],
        }
        result = generator._validate_and_process(raw)
        assert len(result["entity_types"][0]["description"]) <= 100
        assert len(result["edge_types"][0]["description"]) <= 100

    def test_adds_missing_fields(self, generator):
        raw = {
            "entity_types": [{"name": "X"}],
            "edge_types": [{"name": "Y"}],
        }
        result = generator._validate_and_process(raw)
        assert "attributes" in result["entity_types"][0]
        assert "examples" in result["entity_types"][0]
        assert "source_targets" in result["edge_types"][0]

    def test_missing_top_level_keys_default_to_empty(self, generator):
        result = generator._validate_and_process({})
        assert result["entity_types"] is not None
        assert result["edge_types"] is not None
        assert "analysis_summary" in result


class TestGenerate:
    def test_calls_llm_and_postprocesses(self, generator, mock_llm):
        mock_llm.chat_json.return_value = {
            "entity_types": [
                {"name": f"E{i}", "description": f"Entity {i}"} for i in range(8)
            ],
            "edge_types": [
                {"name": "WORKS_FOR", "description": "Employment", "source_targets": []},
            ],
            "analysis_summary": "Test summary",
        }

        result = generator.generate(
            document_texts=["Some document text"],
            simulation_requirement="Test simulation",
        )

        mock_llm.chat_json.assert_called_once()
        assert "entity_types" in result
        assert "edge_types" in result
        names = [e["name"] for e in result["entity_types"]]
        assert "Person" in names
        assert "Organization" in names


class TestBuildUserMessage:
    def test_includes_requirement_and_text(self, generator):
        msg = generator._build_user_message(
            document_texts=["doc content"],
            simulation_requirement="simulate market reaction",
            additional_context=None,
        )
        assert "simulate market reaction" in msg
        assert "doc content" in msg

    def test_includes_additional_context(self, generator):
        msg = generator._build_user_message(
            document_texts=["text"],
            simulation_requirement="req",
            additional_context="extra info",
        )
        assert "extra info" in msg

    def test_truncates_very_long_text(self, generator):
        long_text = "X" * 60000
        msg = generator._build_user_message(
            document_texts=[long_text],
            simulation_requirement="req",
            additional_context=None,
        )
        assert len(msg) < 60000 + 1000  # truncated with note


class TestGeneratePythonCode:
    def test_generates_valid_python_structure(self, generator):
        ontology = {
            "entity_types": [
                {
                    "name": "Student",
                    "description": "A university student",
                    "attributes": [
                        {"name": "full_name", "description": "Full name", "type": "text"},
                    ],
                },
            ],
            "edge_types": [
                {
                    "name": "STUDIES_AT",
                    "description": "Enrollment relationship",
                    "attributes": [],
                    "source_targets": [{"source": "Student", "target": "University"}],
                },
            ],
        }
        code = generator.generate_python_code(ontology)
        assert "class Student(EntityModel):" in code
        assert "class StudiesAt(EdgeModel):" in code
        assert 'ENTITY_TYPES' in code
        assert 'EDGE_TYPES' in code
        assert 'EDGE_SOURCE_TARGETS' in code
