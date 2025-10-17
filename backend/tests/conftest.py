"""Pytest configuration and fixtures for RAG system tests"""

from typing import Any, Dict, List
from unittest.mock import MagicMock, Mock

import pytest
from models import Course, CourseChunk, Lesson, SourceLink
from vector_store import SearchResults


@pytest.fixture
def sample_course():
    """Create a sample course for testing"""
    return Course(
        title="Test Course: Introduction to Testing",
        course_link="https://example.com/test-course",
        instructor="Test Instructor",
        lessons=[
            Lesson(
                lesson_number=0,
                title="Getting Started with Tests",
                lesson_link="https://example.com/lesson-0",
            ),
            Lesson(
                lesson_number=1,
                title="Writing Unit Tests",
                lesson_link="https://example.com/lesson-1",
            ),
            Lesson(
                lesson_number=2,
                title="Integration Testing",
                lesson_link="https://example.com/lesson-2",
            ),
        ],
    )


@pytest.fixture
def sample_chunks(sample_course):
    """Create sample course chunks for testing"""
    return [
        CourseChunk(
            content="This is the introduction to testing. Testing is important for code quality.",
            course_title=sample_course.title,
            lesson_number=0,
            chunk_index=0,
        ),
        CourseChunk(
            content="Unit tests verify individual components work correctly. Use pytest for Python.",
            course_title=sample_course.title,
            lesson_number=1,
            chunk_index=1,
        ),
        CourseChunk(
            content="Integration tests verify components work together. End-to-end testing is crucial.",
            course_title=sample_course.title,
            lesson_number=2,
            chunk_index=2,
        ),
    ]


@pytest.fixture
def sample_search_results(sample_chunks):
    """Create sample SearchResults for testing"""
    return SearchResults(
        documents=[chunk.content for chunk in sample_chunks[:2]],  # First 2 chunks
        metadata=[
            {
                "course_title": sample_chunks[0].course_title,
                "lesson_number": sample_chunks[0].lesson_number,
                "chunk_index": 0,
            },
            {
                "course_title": sample_chunks[1].course_title,
                "lesson_number": sample_chunks[1].lesson_number,
                "chunk_index": 1,
            },
        ],
        distances=[0.1, 0.2],
        error=None,
    )


@pytest.fixture
def empty_search_results():
    """Create empty SearchResults for testing"""
    return SearchResults(documents=[], metadata=[], distances=[], error=None)


@pytest.fixture
def error_search_results():
    """Create SearchResults with error for testing"""
    return SearchResults.empty("Test error: Search failed")


@pytest.fixture
def mock_vector_store(sample_search_results, sample_course):
    """Create a mock VectorStore for testing"""
    mock = Mock()
    mock.search = Mock(return_value=sample_search_results)
    mock.get_lesson_link = Mock(return_value="https://example.com/lesson-0")
    mock.get_course_link = Mock(return_value="https://example.com/course")
    mock.get_course_outline = Mock(
        return_value={
            "title": sample_course.title,
            "course_link": sample_course.course_link,
            "instructor": sample_course.instructor,
            "lessons": [
                {
                    "lesson_number": lesson.lesson_number,
                    "lesson_title": lesson.title,
                    "lesson_link": lesson.lesson_link,
                }
                for lesson in sample_course.lessons
            ],
            "lesson_count": len(sample_course.lessons),
        }
    )
    mock.max_results = 5
    return mock


@pytest.fixture
def mock_anthropic_response_no_tools():
    """Mock Anthropic API response without tool use"""
    mock_response = Mock()
    mock_response.stop_reason = "end_turn"
    mock_response.content = [Mock(text="This is a test response.")]
    return mock_response


@pytest.fixture
def mock_anthropic_response_with_tools():
    """Mock Anthropic API response with tool use"""
    mock_response = Mock()
    mock_response.stop_reason = "tool_use"

    # Create mock tool use block
    tool_block = Mock()
    tool_block.type = "tool_use"
    tool_block.name = "search_course_content"
    tool_block.id = "test_tool_123"
    tool_block.input = {"query": "test query"}

    mock_response.content = [tool_block]
    return mock_response


@pytest.fixture
def mock_anthropic_final_response():
    """Mock Anthropic API final response after tool execution"""
    mock_response = Mock()
    mock_response.stop_reason = "end_turn"
    mock_response.content = [Mock(text="Based on the search, here is the answer.")]
    return mock_response


@pytest.fixture
def mock_anthropic_client(
    mock_anthropic_response_no_tools, mock_anthropic_final_response
):
    """Create a mock Anthropic client"""
    mock_client = Mock()
    mock_client.messages = Mock()
    # Default to no-tools response, can be overridden in tests
    mock_client.messages.create = Mock(
        side_effect=[mock_anthropic_response_no_tools, mock_anthropic_final_response]
    )
    return mock_client


@pytest.fixture
def mock_tool_manager():
    """Create a mock ToolManager"""
    mock = Mock()
    mock.get_tool_definitions = Mock(
        return_value=[
            {
                "name": "search_course_content",
                "description": "Search course materials",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"}
                    },
                    "required": ["query"],
                },
            }
        ]
    )
    mock.execute_tool = Mock(return_value="[Test Course]\nTest search result content")
    mock.get_last_sources = Mock(
        return_value=[
            SourceLink(
                text="Test Course - Lesson 0", link="https://example.com/lesson-0"
            )
        ]
    )
    mock.reset_sources = Mock()
    return mock


@pytest.fixture
def test_config():
    """Create test configuration"""
    from dataclasses import dataclass

    @dataclass
    class TestConfig:
        ANTHROPIC_API_KEY: str = "test-api-key"
        ANTHROPIC_MODEL: str = "claude-sonnet-4-20250514"
        EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
        CHUNK_SIZE: int = 800
        CHUNK_OVERLAP: int = 100
        MAX_RESULTS: int = 5  # Proper value for testing
        MAX_HISTORY: int = 2
        CHROMA_PATH: str = "./test_chroma_db"

    return TestConfig()
