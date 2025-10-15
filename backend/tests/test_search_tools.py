"""Tests for search tools functionality"""
import pytest
from unittest.mock import Mock
from search_tools import CourseSearchTool, CourseOutlineTool, ToolManager
from models import SourceLink
from vector_store import SearchResults


class TestCourseSearchTool:
    """Tests for CourseSearchTool"""

    def test_get_tool_definition(self, mock_vector_store):
        """Test that tool definition is correctly structured"""
        tool = CourseSearchTool(mock_vector_store)
        definition = tool.get_tool_definition()

        assert definition["name"] == "search_course_content"
        assert "description" in definition
        assert "input_schema" in definition
        assert definition["input_schema"]["type"] == "object"
        assert "query" in definition["input_schema"]["properties"]
        assert "query" in definition["input_schema"]["required"]

    def test_execute_with_valid_query(self, mock_vector_store, sample_search_results):
        """Test execute() returns formatted results for valid query"""
        tool = CourseSearchTool(mock_vector_store)
        mock_vector_store.search.return_value = sample_search_results

        result = tool.execute(query="test query")

        # Should return formatted string with content
        assert isinstance(result, str)
        assert len(result) > 0
        # Should contain the document content
        assert "introduction to testing" in result.lower()
        # Should have been called with correct parameters
        mock_vector_store.search.assert_called_once_with(
            query="test query",
            course_name=None,
            lesson_number=None
        )

    def test_execute_with_course_filter(self, mock_vector_store, sample_search_results):
        """Test execute() with course_name filter"""
        tool = CourseSearchTool(mock_vector_store)
        mock_vector_store.search.return_value = sample_search_results

        result = tool.execute(query="test query", course_name="Test Course")

        mock_vector_store.search.assert_called_once_with(
            query="test query",
            course_name="Test Course",
            lesson_number=None
        )

    def test_execute_with_lesson_filter(self, mock_vector_store, sample_search_results):
        """Test execute() with lesson_number filter"""
        tool = CourseSearchTool(mock_vector_store)
        mock_vector_store.search.return_value = sample_search_results

        result = tool.execute(query="test query", lesson_number=1)

        mock_vector_store.search.assert_called_once_with(
            query="test query",
            course_name=None,
            lesson_number=1
        )

    def test_execute_handles_empty_results(self, mock_vector_store, empty_search_results):
        """Test execute() handles empty results gracefully"""
        tool = CourseSearchTool(mock_vector_store)
        mock_vector_store.search.return_value = empty_search_results

        result = tool.execute(query="nonexistent query")

        assert "No relevant content found" in result

    def test_execute_handles_empty_results_with_filters(self, mock_vector_store, empty_search_results):
        """Test execute() includes filter info in empty results message"""
        tool = CourseSearchTool(mock_vector_store)
        mock_vector_store.search.return_value = empty_search_results

        result = tool.execute(
            query="test",
            course_name="Nonexistent Course",
            lesson_number=99
        )

        assert "No relevant content found" in result
        assert "Nonexistent Course" in result
        assert "lesson 99" in result

    def test_execute_handles_error_results(self, mock_vector_store, error_search_results):
        """Test execute() returns error message when search fails"""
        tool = CourseSearchTool(mock_vector_store)
        mock_vector_store.search.return_value = error_search_results

        result = tool.execute(query="test query")

        assert "Test error" in result
        assert "Search failed" in result

    def test_format_results_creates_source_links(self, mock_vector_store, sample_search_results):
        """Test that _format_results() creates SourceLink objects"""
        tool = CourseSearchTool(mock_vector_store)
        mock_vector_store.get_lesson_link.return_value = "https://example.com/lesson-0"

        formatted = tool._format_results(sample_search_results)

        # Check that last_sources was populated
        assert len(tool.last_sources) == 2
        assert all(isinstance(source, SourceLink) for source in tool.last_sources)

        # Check SourceLink properties
        first_source = tool.last_sources[0]
        assert first_source.text is not None
        assert "Test Course" in first_source.text

    def test_format_results_includes_lesson_links(self, mock_vector_store, sample_search_results):
        """Test that _format_results() includes lesson links when available"""
        tool = CourseSearchTool(mock_vector_store)
        lesson_link = "https://example.com/lesson-0"
        mock_vector_store.get_lesson_link.return_value = lesson_link

        formatted = tool._format_results(sample_search_results)

        # Check that lesson links were fetched
        assert mock_vector_store.get_lesson_link.called

        # Check that source has the link
        sources_with_links = [s for s in tool.last_sources if s.link is not None]
        assert len(sources_with_links) > 0

    def test_format_results_sorts_sources(self, mock_vector_store):
        """Test that _format_results() sorts sources by course and lesson"""
        # Create search results with mixed order
        mixed_results = SearchResults(
            documents=["doc1", "doc2", "doc3"],
            metadata=[
                {"course_title": "B Course", "lesson_number": 2},
                {"course_title": "A Course", "lesson_number": 1},
                {"course_title": "A Course", "lesson_number": 0}
            ],
            distances=[0.1, 0.2, 0.3]
        )

        tool = CourseSearchTool(mock_vector_store)
        mock_vector_store.get_lesson_link.return_value = None

        formatted = tool._format_results(mixed_results)

        # Sources should be sorted: A Course L0, A Course L1, B Course L2
        assert len(tool.last_sources) == 3
        assert "A Course" in tool.last_sources[0].text
        assert "Lesson 0" in tool.last_sources[0].text
        assert "A Course" in tool.last_sources[1].text
        assert "Lesson 1" in tool.last_sources[1].text
        assert "B Course" in tool.last_sources[2].text


class TestCourseOutlineTool:
    """Tests for CourseOutlineTool"""

    def test_get_tool_definition(self, mock_vector_store):
        """Test that tool definition is correctly structured"""
        tool = CourseOutlineTool(mock_vector_store)
        definition = tool.get_tool_definition()

        assert definition["name"] == "get_course_outline"
        assert "description" in definition
        assert "course_name" in definition["input_schema"]["properties"]
        assert "course_name" in definition["input_schema"]["required"]

    def test_execute_returns_outline(self, mock_vector_store):
        """Test execute() returns formatted course outline"""
        tool = CourseOutlineTool(mock_vector_store)

        result = tool.execute(course_name="Test Course")

        assert isinstance(result, str)
        assert "Test Course" in result
        assert "Lesson" in result
        mock_vector_store.get_course_outline.assert_called_once_with("Test Course")

    def test_execute_handles_course_not_found(self, mock_vector_store):
        """Test execute() handles course not found gracefully"""
        tool = CourseOutlineTool(mock_vector_store)
        mock_vector_store.get_course_outline.return_value = None

        result = tool.execute(course_name="Nonexistent Course")

        assert "No course found" in result
        assert "Nonexistent Course" in result

    def test_format_outline_includes_all_info(self, mock_vector_store, sample_course):
        """Test that _format_outline() includes all course information"""
        tool = CourseOutlineTool(mock_vector_store)

        outline_data = {
            'title': sample_course.title,
            'course_link': sample_course.course_link,
            'instructor': sample_course.instructor,
            'lessons': [
                {
                    'lesson_number': lesson.lesson_number,
                    'lesson_title': lesson.title
                }
                for lesson in sample_course.lessons
            ],
            'lesson_count': len(sample_course.lessons)
        }

        formatted = tool._format_outline(outline_data)

        assert sample_course.title in formatted
        assert sample_course.course_link in formatted
        assert sample_course.instructor in formatted
        assert "3 total" in formatted  # 3 lessons
        assert "Getting Started with Tests" in formatted


class TestToolManager:
    """Tests for ToolManager"""

    def test_register_tool(self, mock_vector_store):
        """Test that tools can be registered"""
        manager = ToolManager()
        tool = CourseSearchTool(mock_vector_store)

        manager.register_tool(tool)

        assert "search_course_content" in manager.tools

    def test_register_multiple_tools(self, mock_vector_store):
        """Test that multiple tools can be registered"""
        manager = ToolManager()
        search_tool = CourseSearchTool(mock_vector_store)
        outline_tool = CourseOutlineTool(mock_vector_store)

        manager.register_tool(search_tool)
        manager.register_tool(outline_tool)

        assert len(manager.tools) == 2
        assert "search_course_content" in manager.tools
        assert "get_course_outline" in manager.tools

    def test_get_tool_definitions(self, mock_vector_store):
        """Test that tool definitions can be retrieved"""
        manager = ToolManager()
        tool = CourseSearchTool(mock_vector_store)
        manager.register_tool(tool)

        definitions = manager.get_tool_definitions()

        assert len(definitions) == 1
        assert definitions[0]["name"] == "search_course_content"

    def test_execute_tool(self, mock_vector_store, sample_search_results):
        """Test that tools can be executed by name"""
        manager = ToolManager()
        tool = CourseSearchTool(mock_vector_store)
        manager.register_tool(tool)

        mock_vector_store.search.return_value = sample_search_results
        result = manager.execute_tool("search_course_content", query="test")

        assert isinstance(result, str)
        assert len(result) > 0

    def test_execute_tool_not_found(self, mock_vector_store):
        """Test that executing nonexistent tool returns error"""
        manager = ToolManager()

        result = manager.execute_tool("nonexistent_tool", query="test")

        assert "not found" in result.lower()

    def test_get_last_sources(self, mock_vector_store, sample_search_results):
        """Test that last sources can be retrieved"""
        manager = ToolManager()
        tool = CourseSearchTool(mock_vector_store)
        manager.register_tool(tool)

        # Execute search to populate sources
        mock_vector_store.search.return_value = sample_search_results
        manager.execute_tool("search_course_content", query="test")

        sources = manager.get_last_sources()

        assert isinstance(sources, list)
        assert len(sources) > 0
        assert all(isinstance(s, SourceLink) for s in sources)

    def test_reset_sources(self, mock_vector_store, sample_search_results):
        """Test that sources can be reset"""
        manager = ToolManager()
        tool = CourseSearchTool(mock_vector_store)
        manager.register_tool(tool)

        # Execute search to populate sources
        mock_vector_store.search.return_value = sample_search_results
        manager.execute_tool("search_course_content", query="test")

        # Reset sources
        manager.reset_sources()

        sources = manager.get_last_sources()
        assert len(sources) == 0
