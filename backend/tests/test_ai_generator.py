"""Tests for AI generator functionality"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from ai_generator import AIGenerator


class TestAIGenerator:
    """Tests for AIGenerator class"""

    def test_initialization(self):
        """Test that AIGenerator initializes correctly"""
        generator = AIGenerator(api_key="test-key", model="claude-sonnet-4-20250514")

        assert generator.model == "claude-sonnet-4-20250514"
        assert generator.base_params["model"] == "claude-sonnet-4-20250514"
        assert generator.base_params["temperature"] == 0
        assert generator.base_params["max_tokens"] == 800

    @patch('ai_generator.anthropic.Anthropic')
    def test_generate_response_without_tools(self, mock_anthropic_class):
        """Test generate_response() without tools returns text response"""
        # Setup mock
        mock_client = Mock()
        mock_anthropic_class.return_value = mock_client

        mock_response = Mock()
        mock_response.stop_reason = "end_turn"
        mock_response.content = [Mock(text="Test response")]

        mock_client.messages.create.return_value = mock_response

        # Create generator and call
        generator = AIGenerator(api_key="test-key", model="test-model")
        result = generator.generate_response(query="test query")

        # Verify
        assert result == "Test response"
        assert mock_client.messages.create.called
        call_args = mock_client.messages.create.call_args[1]
        assert call_args["messages"][0]["content"] == "test query"
        assert call_args["system"] == AIGenerator.SYSTEM_PROMPT

    @patch('ai_generator.anthropic.Anthropic')
    def test_generate_response_with_conversation_history(self, mock_anthropic_class):
        """Test that conversation history is included in system prompt"""
        # Setup mock
        mock_client = Mock()
        mock_anthropic_class.return_value = mock_client

        mock_response = Mock()
        mock_response.stop_reason = "end_turn"
        mock_response.content = [Mock(text="Test response")]

        mock_client.messages.create.return_value = mock_response

        # Create generator and call with history
        generator = AIGenerator(api_key="test-key", model="test-model")
        history = "User: Previous question\nAssistant: Previous answer"
        result = generator.generate_response(query="test query", conversation_history=history)

        # Verify history is in system content
        call_args = mock_client.messages.create.call_args[1]
        assert history in call_args["system"]
        assert AIGenerator.SYSTEM_PROMPT in call_args["system"]

    @patch('ai_generator.anthropic.Anthropic')
    def test_generate_response_with_tools(self, mock_anthropic_class):
        """Test that tools are passed to the API when provided"""
        # Setup mock
        mock_client = Mock()
        mock_anthropic_class.return_value = mock_client

        mock_response = Mock()
        mock_response.stop_reason = "end_turn"
        mock_response.content = [Mock(text="Test response")]

        mock_client.messages.create.return_value = mock_response

        # Create generator
        generator = AIGenerator(api_key="test-key", model="test-model")

        tool_definitions = [
            {
                "name": "test_tool",
                "description": "A test tool",
                "input_schema": {"type": "object", "properties": {}}
            }
        ]

        result = generator.generate_response(
            query="test query",
            tools=tool_definitions,
            tool_manager=Mock()
        )

        # Verify tools were passed
        call_args = mock_client.messages.create.call_args[1]
        assert "tools" in call_args
        assert call_args["tools"] == tool_definitions
        assert call_args["tool_choice"] == {"type": "auto"}

    @patch('ai_generator.anthropic.Anthropic')
    def test_generate_response_triggers_tool_execution(self, mock_anthropic_class):
        """Test that tool_use stop_reason triggers _handle_tool_execution"""
        # Setup mock
        mock_client = Mock()
        mock_anthropic_class.return_value = mock_client

        # First response with tool use
        tool_use_response = Mock()
        tool_use_response.stop_reason = "tool_use"
        tool_block = Mock()
        tool_block.type = "tool_use"
        tool_block.name = "test_tool"
        tool_block.id = "tool_123"
        tool_block.input = {"param": "value"}
        tool_use_response.content = [tool_block]

        # Second response after tool execution
        final_response = Mock()
        final_response.stop_reason = "end_turn"
        final_response.content = [Mock(text="Final response after tool")]

        mock_client.messages.create.side_effect = [tool_use_response, final_response]

        # Create mock tool manager
        mock_tool_manager = Mock()
        mock_tool_manager.execute_tool.return_value = "Tool result"

        # Create generator and call
        generator = AIGenerator(api_key="test-key", model="test-model")
        result = generator.generate_response(
            query="test query",
            tools=[{"name": "test_tool"}],
            tool_manager=mock_tool_manager
        )

        # Verify tool was executed
        assert result == "Final response after tool"
        mock_tool_manager.execute_tool.assert_called_once_with(
            "test_tool",
            param="value"
        )

        # Verify second API call was made
        assert mock_client.messages.create.call_count == 2

    @patch('ai_generator.anthropic.Anthropic')
    def test_handle_tool_execution_formats_messages_correctly(self, mock_anthropic_class):
        """Test that _handle_tool_execution formats message history correctly"""
        # Setup mock
        mock_client = Mock()
        mock_anthropic_class.return_value = mock_client

        # First response with tool use
        tool_use_response = Mock()
        tool_use_response.stop_reason = "tool_use"
        tool_block = Mock()
        tool_block.type = "tool_use"
        tool_block.name = "test_tool"
        tool_block.id = "tool_123"
        tool_block.input = {"query": "test"}
        tool_use_response.content = [tool_block]

        # Second response
        final_response = Mock()
        final_response.stop_reason = "end_turn"
        final_response.content = [Mock(text="Final")]

        mock_client.messages.create.side_effect = [tool_use_response, final_response]

        # Create mock tool manager
        mock_tool_manager = Mock()
        mock_tool_manager.execute_tool.return_value = "Tool executed successfully"

        # Create generator and call
        generator = AIGenerator(api_key="test-key", model="test-model")
        result = generator.generate_response(
            query="user query",
            tools=[{"name": "test_tool"}],
            tool_manager=mock_tool_manager
        )

        # Get the second API call (after tool execution)
        second_call_args = mock_client.messages.create.call_args_list[1][1]

        # Verify message structure
        messages = second_call_args["messages"]
        assert len(messages) == 3  # user, assistant with tool_use, user with tool_result

        # First message: user query
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "user query"

        # Second message: assistant with tool use
        assert messages[1]["role"] == "assistant"
        assert messages[1]["content"] == tool_use_response.content

        # Third message: tool results
        assert messages[2]["role"] == "user"
        assert isinstance(messages[2]["content"], list)
        assert messages[2]["content"][0]["type"] == "tool_result"
        assert messages[2]["content"][0]["tool_use_id"] == "tool_123"
        assert messages[2]["content"][0]["content"] == "Tool executed successfully"

    @patch('ai_generator.anthropic.Anthropic')
    def test_handle_tool_execution_no_tools_in_final_call(self, mock_anthropic_class):
        """Test that final API call after tool execution doesn't include tools"""
        # Setup mock
        mock_client = Mock()
        mock_anthropic_class.return_value = mock_client

        # First response with tool use
        tool_use_response = Mock()
        tool_use_response.stop_reason = "tool_use"
        tool_block = Mock()
        tool_block.type = "tool_use"
        tool_block.name = "test_tool"
        tool_block.id = "tool_123"
        tool_block.input = {}
        tool_use_response.content = [tool_block]

        # Second response
        final_response = Mock()
        final_response.stop_reason = "end_turn"
        final_response.content = [Mock(text="Final")]

        mock_client.messages.create.side_effect = [tool_use_response, final_response]

        # Create generator and call
        generator = AIGenerator(api_key="test-key", model="test-model")
        mock_tool_manager = Mock()
        mock_tool_manager.execute_tool.return_value = "Result"

        result = generator.generate_response(
            query="test",
            tools=[{"name": "test_tool"}],
            tool_manager=mock_tool_manager
        )

        # Verify final call doesn't have tools
        final_call_args = mock_client.messages.create.call_args_list[1][1]
        assert "tools" not in final_call_args

    @patch('ai_generator.anthropic.Anthropic')
    def test_system_prompt_contains_tool_guidance(self, mock_anthropic_class):
        """Test that system prompt contains guidance for both tools"""
        mock_client = Mock()
        mock_anthropic_class.return_value = mock_client

        mock_response = Mock()
        mock_response.stop_reason = "end_turn"
        mock_response.content = [Mock(text="Test")]

        mock_client.messages.create.return_value = mock_response

        generator = AIGenerator(api_key="test-key", model="test-model")
        generator.generate_response(query="test")

        # Check that system prompt mentions both tools
        assert "search_course_content" in AIGenerator.SYSTEM_PROMPT
        assert "get_course_outline" in AIGenerator.SYSTEM_PROMPT
        # Check guidance is present
        assert "When to Use Each Tool" in AIGenerator.SYSTEM_PROMPT
