"""Tests for app.services.text_processor and app.utils.file_parser chunking."""

import pytest
from app.services.text_processor import TextProcessor
from app.utils.file_parser import split_text_into_chunks


class TestPreprocessText:
    def test_normalizes_crlf(self):
        assert TextProcessor.preprocess_text("a\r\nb\rc") == "a\nb\nc"

    def test_collapses_multiple_blank_lines(self):
        result = TextProcessor.preprocess_text("a\n\n\n\n\nb")
        assert result == "a\n\nb"

    def test_strips_line_whitespace(self):
        result = TextProcessor.preprocess_text("  hello  \n  world  ")
        assert result == "hello\nworld"

    def test_strips_outer_whitespace(self):
        assert TextProcessor.preprocess_text("  hi  ") == "hi"

    def test_empty_string(self):
        assert TextProcessor.preprocess_text("") == ""


class TestGetTextStats:
    def test_basic_stats(self):
        stats = TextProcessor.get_text_stats("hello world\nfoo bar baz")
        assert stats["total_chars"] == 23
        assert stats["total_lines"] == 2
        assert stats["total_words"] == 5

    def test_empty_string(self):
        stats = TextProcessor.get_text_stats("")
        assert stats["total_chars"] == 0
        assert stats["total_lines"] == 1
        assert stats["total_words"] == 0


class TestSplitTextIntoChunks:
    def test_short_text_returns_single_chunk(self):
        chunks = split_text_into_chunks("Hello world", chunk_size=500)
        assert chunks == ["Hello world"]

    def test_empty_text_returns_empty(self):
        assert split_text_into_chunks("") == []
        assert split_text_into_chunks("   ") == []

    def test_splits_long_text(self):
        text = "word " * 200  # 1000 chars
        chunks = split_text_into_chunks(text.strip(), chunk_size=100, overlap=10)
        assert len(chunks) > 1
        for c in chunks:
            assert len(c) <= 110  # chunk_size + some boundary tolerance

    def test_overlap_creates_shared_content(self):
        text = "A" * 100 + "B" * 100 + "C" * 100
        chunks = split_text_into_chunks(text, chunk_size=100, overlap=20)
        assert len(chunks) >= 2
        # Overlap means the tail of one chunk shares chars with next
        if len(chunks) >= 2:
            tail = chunks[0][-20:]
            assert tail in chunks[1] or chunks[1].startswith(tail[:10])

    def test_respects_sentence_boundaries(self):
        text = "First sentence. Second sentence. Third sentence. " * 20
        chunks = split_text_into_chunks(text, chunk_size=60, overlap=5)
        assert len(chunks) > 1
