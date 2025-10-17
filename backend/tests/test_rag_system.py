"""Integration tests for RAG system"""

from unittest.mock import MagicMock, Mock, patch

import pytest
from models import SourceLink
from rag_system import RAGSystem


class TestRAGSystemIntegration:
    """Integration tests for RAGSystem with mocked components"""

    @patch("rag_system.VectorStore")
    @patch("rag_system.AIGenerator")
    @patch("rag_system.SessionManager")
    @patch("rag_system.DocumentProcessor")
    def test_query_without_session(
        self,
        mock_doc_processor,
        mock_session_manager,
        mock_ai_generator_class,
        mock_vector_store_class,
        test_config,
    ):
        """Test query() without session ID"""
        # Setup mocks
        mock_vector_store = Mock()
        mock_vector_store_class.return_value = mock_vector_store

        mock_ai_gen = Mock()
        mock_ai_gen.generate_response.return_value = "AI response"
        mock_ai_generator_class.return_value = mock_ai_gen

        mock_session = Mock()
        mock_session_manager.return_value = mock_session

        # Create RAG system
        rag_system = RAGSystem(test_config)

        # Mock tool manager
        rag_system.tool_manager.get_last_sources = Mock(return_value=[])
        rag_system.tool_manager.reset_sources = Mock()

        # Execute query
        response, sources = rag_system.query("What is testing?")

        # Verify AI generator was called
        assert mock_ai_gen.generate_response.called
        assert response == "AI response"

    @patch("rag_system.VectorStore")
    @patch("rag_system.AIGenerator")
    @patch("rag_system.SessionManager")
    @patch("rag_system.DocumentProcessor")
    def test_query_with_session(
        self,
        mock_doc_processor,
        mock_session_manager_class,
        mock_ai_generator_class,
        mock_vector_store_class,
        test_config,
    ):
        """Test query() with session ID includes conversation history"""
        # Setup mocks
        mock_vector_store = Mock()
        mock_vector_store_class.return_value = mock_vector_store

        mock_ai_gen = Mock()
        mock_ai_gen.generate_response.return_value = "AI response"
        mock_ai_generator_class.return_value = mock_ai_gen

        mock_session_manager = Mock()
        mock_session_manager.get_conversation_history.return_value = (
            "Previous: conversation"
        )
        mock_session_manager_class.return_value = mock_session_manager

        # Create RAG system
        rag_system = RAGSystem(test_config)
        rag_system.tool_manager.get_last_sources = Mock(return_value=[])
        rag_system.tool_manager.reset_sources = Mock()

        # Execute query with session
        response, sources = rag_system.query("What is testing?", session_id="session_1")

        # Verify history was retrieved
        mock_session_manager.get_conversation_history.assert_called_once_with(
            "session_1"
        )

        # Verify AI generator was called with history
        call_args = mock_ai_gen.generate_response.call_args
        assert call_args[1]["conversation_history"] == "Previous: conversation"

    @patch("rag_system.VectorStore")
    @patch("rag_system.AIGenerator")
    @patch("rag_system.SessionManager")
    @patch("rag_system.DocumentProcessor")
    def test_query_passes_tools_to_ai_generator(
        self,
        mock_doc_processor,
        mock_session_manager,
        mock_ai_generator_class,
        mock_vector_store_class,
        test_config,
    ):
        """Test that query() passes tool definitions to AI generator"""
        # Setup mocks
        mock_vector_store = Mock()
        mock_vector_store_class.return_value = mock_vector_store

        mock_ai_gen = Mock()
        mock_ai_gen.generate_response.return_value = "AI response"
        mock_ai_generator_class.return_value = mock_ai_gen

        # Create RAG system
        rag_system = RAGSystem(test_config)
        rag_system.tool_manager.get_last_sources = Mock(return_value=[])
        rag_system.tool_manager.reset_sources = Mock()

        # Execute query
        response, sources = rag_system.query("What is testing?")

        # Verify tools were passed
        call_args = mock_ai_gen.generate_response.call_args
        assert "tools" in call_args[1]
        assert "tool_manager" in call_args[1]

        # Verify tools are the tool definitions
        tools = call_args[1]["tools"]
        assert isinstance(tools, list)
        assert len(tools) >= 1  # At least search tool

    @patch("rag_system.VectorStore")
    @patch("rag_system.AIGenerator")
    @patch("rag_system.SessionManager")
    @patch("rag_system.DocumentProcessor")
    def test_query_retrieves_and_resets_sources(
        self,
        mock_doc_processor,
        mock_session_manager,
        mock_ai_generator_class,
        mock_vector_store_class,
        test_config,
    ):
        """Test that query() retrieves sources and then resets them"""
        # Setup mocks
        mock_vector_store = Mock()
        mock_vector_store_class.return_value = mock_vector_store

        mock_ai_gen = Mock()
        mock_ai_gen.generate_response.return_value = "AI response"
        mock_ai_generator_class.return_value = mock_ai_gen

        # Create RAG system
        rag_system = RAGSystem(test_config)

        # Mock tool manager with sources
        test_sources = [
            SourceLink(
                text="Test Course - Lesson 0", link="http://example.com/lesson-0"
            )
        ]
        rag_system.tool_manager.get_last_sources = Mock(return_value=test_sources)
        rag_system.tool_manager.reset_sources = Mock()

        # Execute query
        response, sources = rag_system.query("What is testing?")

        # Verify sources were retrieved and reset
        rag_system.tool_manager.get_last_sources.assert_called_once()
        rag_system.tool_manager.reset_sources.assert_called_once()

        # Verify sources are returned
        assert sources == test_sources

    @patch("rag_system.VectorStore")
    @patch("rag_system.AIGenerator")
    @patch("rag_system.SessionManager")
    @patch("rag_system.DocumentProcessor")
    def test_query_updates_conversation_history(
        self,
        mock_doc_processor,
        mock_session_manager_class,
        mock_ai_generator_class,
        mock_vector_store_class,
        test_config,
    ):
        """Test that query() updates conversation history after response"""
        # Setup mocks
        mock_vector_store = Mock()
        mock_vector_store_class.return_value = mock_vector_store

        mock_ai_gen = Mock()
        mock_ai_gen.generate_response.return_value = "AI response"
        mock_ai_generator_class.return_value = mock_ai_gen

        mock_session_manager = Mock()
        mock_session_manager_class.return_value = mock_session_manager

        # Create RAG system
        rag_system = RAGSystem(test_config)
        rag_system.tool_manager.get_last_sources = Mock(return_value=[])
        rag_system.tool_manager.reset_sources = Mock()

        # Execute query with session
        query_text = "What is testing?"
        response, sources = rag_system.query(query_text, session_id="session_1")

        # Verify history was updated
        mock_session_manager.add_exchange.assert_called_once_with(
            "session_1", query_text, "AI response"
        )

    @patch("rag_system.VectorStore")
    @patch("rag_system.AIGenerator")
    @patch("rag_system.SessionManager")
    @patch("rag_system.DocumentProcessor")
    def test_query_formats_prompt_correctly(
        self,
        mock_doc_processor,
        mock_session_manager,
        mock_ai_generator_class,
        mock_vector_store_class,
        test_config,
    ):
        """Test that query() formats the prompt correctly"""
        # Setup mocks
        mock_vector_store = Mock()
        mock_vector_store_class.return_value = mock_vector_store

        mock_ai_gen = Mock()
        mock_ai_gen.generate_response.return_value = "AI response"
        mock_ai_generator_class.return_value = mock_ai_gen

        # Create RAG system
        rag_system = RAGSystem(test_config)
        rag_system.tool_manager.get_last_sources = Mock(return_value=[])
        rag_system.tool_manager.reset_sources = Mock()

        # Execute query
        user_query = "What is testing?"
        response, sources = rag_system.query(user_query)

        # Verify prompt includes user query
        call_args = mock_ai_gen.generate_response.call_args
        prompt = call_args[1]["query"]
        assert user_query in prompt
        assert "course materials" in prompt.lower()


class TestRAGSystemToolIntegration:
    """Test RAG system integration with real tools but mocked vector store"""

    @patch("rag_system.VectorStore")
    @patch("rag_system.DocumentProcessor")
    def test_search_tool_registered(
        self, mock_doc_processor, mock_vector_store_class, test_config
    ):
        """Test that CourseSearchTool is registered"""
        mock_vector_store = Mock()
        mock_vector_store_class.return_value = mock_vector_store

        rag_system = RAGSystem(test_config)

        # Verify search tool is registered
        assert "search_course_content" in rag_system.tool_manager.tools

    @patch("rag_system.VectorStore")
    @patch("rag_system.DocumentProcessor")
    def test_outline_tool_registered(
        self, mock_doc_processor, mock_vector_store_class, test_config
    ):
        """Test that CourseOutlineTool is registered"""
        mock_vector_store = Mock()
        mock_vector_store_class.return_value = mock_vector_store

        rag_system = RAGSystem(test_config)

        # Verify outline tool is registered
        assert "get_course_outline" in rag_system.tool_manager.tools

    @patch("rag_system.VectorStore")
    @patch("rag_system.DocumentProcessor")
    def test_tool_definitions_available(
        self, mock_doc_processor, mock_vector_store_class, test_config
    ):
        """Test that tool definitions can be retrieved"""
        mock_vector_store = Mock()
        mock_vector_store_class.return_value = mock_vector_store

        rag_system = RAGSystem(test_config)

        # Get tool definitions
        tool_defs = rag_system.tool_manager.get_tool_definitions()

        # Verify we have definitions
        assert isinstance(tool_defs, list)
        assert len(tool_defs) >= 2  # search and outline tools

        # Verify structure
        tool_names = [tool["name"] for tool in tool_defs]
        assert "search_course_content" in tool_names
        assert "get_course_outline" in tool_names

    @patch("rag_system.VectorStore")
    @patch("rag_system.DocumentProcessor")
    def test_search_tool_execution_through_manager(
        self,
        mock_doc_processor,
        mock_vector_store_class,
        test_config,
        sample_search_results,
    ):
        """Test executing search tool through tool manager"""
        # Setup mock vector store
        mock_vector_store = Mock()
        mock_vector_store.search.return_value = sample_search_results
        mock_vector_store.get_lesson_link.return_value = "https://example.com/lesson"
        mock_vector_store_class.return_value = mock_vector_store

        # Create RAG system
        rag_system = RAGSystem(test_config)

        # Execute tool through manager
        result = rag_system.tool_manager.execute_tool(
            "search_course_content", query="test query"
        )

        # Verify result is a string
        assert isinstance(result, str)
        assert len(result) > 0

        # Verify search was called
        mock_vector_store.search.assert_called_once()


class TestRAGSystemErrorHandling:
    """Test RAG system error handling"""

    @patch("rag_system.VectorStore")
    @patch("rag_system.AIGenerator")
    @patch("rag_system.SessionManager")
    @patch("rag_system.DocumentProcessor")
    def test_query_handles_ai_generator_exception(
        self,
        mock_doc_processor,
        mock_session_manager,
        mock_ai_generator_class,
        mock_vector_store_class,
        test_config,
    ):
        """Test that query() propagates AI generator exceptions"""
        # Setup mocks
        mock_vector_store = Mock()
        mock_vector_store_class.return_value = mock_vector_store

        mock_ai_gen = Mock()
        mock_ai_gen.generate_response.side_effect = Exception("API Error")
        mock_ai_generator_class.return_value = mock_ai_gen

        # Create RAG system
        rag_system = RAGSystem(test_config)

        # Query should raise exception
        with pytest.raises(Exception) as exc_info:
            rag_system.query("What is testing?")

        assert "API Error" in str(exc_info.value)
