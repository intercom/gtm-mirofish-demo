"""Tests for app.utils.file_parser — FileParser class."""

import os
import pytest
from app.utils.file_parser import FileParser


@pytest.fixture()
def txt_file(tmp_path):
    p = tmp_path / "sample.txt"
    p.write_text("Hello from a text file.\nSecond line.", encoding="utf-8")
    return str(p)


@pytest.fixture()
def md_file(tmp_path):
    p = tmp_path / "readme.md"
    p.write_text("# Heading\n\nBody text here.", encoding="utf-8")
    return str(p)


class TestExtractText:
    def test_txt_extraction(self, txt_file):
        text = FileParser.extract_text(txt_file)
        assert "Hello from a text file" in text
        assert "Second line" in text

    def test_md_extraction(self, md_file):
        text = FileParser.extract_text(md_file)
        assert "# Heading" in text
        assert "Body text here" in text

    def test_unsupported_extension_raises(self, tmp_path):
        p = tmp_path / "data.csv"
        p.write_text("a,b,c")
        with pytest.raises(ValueError, match="不支持"):
            FileParser.extract_text(str(p))

    def test_missing_file_raises(self):
        with pytest.raises(FileNotFoundError):
            FileParser.extract_text("/nonexistent/path.txt")


class TestExtractFromMultiple:
    def test_combines_files(self, txt_file, md_file):
        combined = FileParser.extract_from_multiple([txt_file, md_file])
        assert "文档 1" in combined
        assert "文档 2" in combined
        assert "Hello from a text file" in combined
        assert "# Heading" in combined

    def test_handles_missing_file_gracefully(self, txt_file):
        combined = FileParser.extract_from_multiple([txt_file, "/no/such/file.txt"])
        assert "Hello from a text file" in combined
        assert "提取失败" in combined

    def test_empty_list(self):
        assert FileParser.extract_from_multiple([]) == ""


class TestNonUtf8File:
    def test_latin1_encoded_file(self, tmp_path):
        p = tmp_path / "latin.txt"
        p.write_bytes("café résumé".encode("latin-1"))
        text = FileParser.extract_text(str(p))
        assert "caf" in text
        assert "sum" in text
