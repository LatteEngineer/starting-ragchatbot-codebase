import anthropic
from typing import List, Optional, Dict, Any

# Maximum number of tool execution rounds per query
MAX_TOOL_ROUNDS = 2

class AIGenerator:
    """Handles interactions with Anthropic's Claude API for generating responses"""
    
    # Static system prompt to avoid rebuilding on each call
    SYSTEM_PROMPT = """ You are an AI assistant specialized in course materials and educational content with access to tools for searching course content and retrieving course outlines.

Tool Usage:
- **search_course_content**: Use for questions about specific course content, lessons, or detailed educational materials
- **get_course_outline**: Use for questions about course structure, outline, lesson list, or what a course covers
- **Sequential tool calling**: You can use tools in multiple rounds (up to 2 rounds total) for complex queries
- Synthesize tool results into accurate, fact-based responses
- If tool yields no results, state this clearly without offering alternatives

Multi-Round Tool Examples:
- "Find courses about X" → Round 1: get_course_outline for candidate courses → Round 2: search_course_content to verify relevance
- "What does lesson 4 of Course X discuss, and find other courses on that topic" → Round 1: search_course_content for lesson 4 → Round 2: search or outline based on findings

When to Use Each Tool:
- Questions like "What does the course cover?", "Show me the lessons", "What's the outline?" → use get_course_outline
- Questions like "How do I...", "Explain...", "What is..." about course content → use search_course_content

For Outline Queries:
- Return the complete course information: course title, course link, instructor, and all lessons with their numbers and titles
- Present the information clearly and comprehensively

Response Protocol:
- **General knowledge questions**: Answer using existing knowledge without using tools
- **Course-specific questions**: Use appropriate tool first, then answer
- **No meta-commentary**:
 - Provide direct answers only — no reasoning process, tool explanations, or question-type analysis
 - Do not mention "based on the search results" or "based on the outline"

All responses must be:
1. **Brief, Concise and focused** - Get to the point quickly
2. **Educational** - Maintain instructional value
3. **Clear** - Use accessible language
4. **Example-supported** - Include relevant examples when they aid understanding
Provide only the direct answer to what was asked.
"""
    
    def __init__(self, api_key: str, model: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        
        # Pre-build base API parameters
        self.base_params = {
            "model": self.model,
            "temperature": 0,
            "max_tokens": 800
        }
    
    def generate_response(self, query: str,
                         conversation_history: Optional[str] = None,
                         tools: Optional[List] = None,
                         tool_manager=None) -> str:
        """
        Generate AI response with optional tool usage and conversation context.
        Supports up to MAX_TOOL_ROUNDS of sequential tool calling.

        Args:
            query: The user's question or request
            conversation_history: Previous messages for context
            tools: Available tools the AI can use
            tool_manager: Manager to execute tools

        Returns:
            Generated response as string
        """

        # Build system content efficiently - avoid string ops when possible
        system_content = (
            f"{self.SYSTEM_PROMPT}\n\nPrevious conversation:\n{conversation_history}"
            if conversation_history
            else self.SYSTEM_PROMPT
        )

        # Initialize message history
        messages = [{"role": "user", "content": query}]

        # Prepare initial API call parameters
        api_params = {
            **self.base_params,
            "messages": messages,
            "system": system_content
        }

        # Add tools if available
        if tools:
            api_params["tools"] = tools
            api_params["tool_choice"] = {"type": "auto"}

        # Get initial response from Claude
        response = self.client.messages.create(**api_params)

        # Handle sequential tool execution
        tool_round = 0
        while (response.stop_reason == "tool_use"
               and tool_round < MAX_TOOL_ROUNDS
               and tool_manager):
            tool_round += 1

            # Execute tools and update messages
            messages = self._execute_tools_and_build_messages(response, messages, tool_manager)

            # Check if this is the final round
            is_final_round = (tool_round >= MAX_TOOL_ROUNDS)

            # Prepare next API call
            next_params = {
                **self.base_params,
                "messages": messages,
                "system": system_content
            }

            # Only include tools if not the final round
            if not is_final_round and tools:
                next_params["tools"] = tools
                next_params["tool_choice"] = {"type": "auto"}

            # Get next response
            response = self.client.messages.create(**next_params)

        # Return final text response
        return response.content[0].text
    
    def _execute_tools_and_build_messages(self, response, messages: List[Dict[str, Any]], tool_manager) -> List[Dict[str, Any]]:
        """
        Execute tools from a response and build updated message list.

        Args:
            response: The API response containing tool use requests
            messages: Current message history
            tool_manager: Manager to execute tools

        Returns:
            Updated messages list with assistant tool use and user tool results
        """
        # Add AI's tool use response
        messages.append({"role": "assistant", "content": response.content})

        # Execute all tool calls and collect results
        tool_results = []
        for content_block in response.content:
            if content_block.type == "tool_use":
                tool_result = tool_manager.execute_tool(
                    content_block.name,
                    **content_block.input
                )

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": content_block.id,
                    "content": tool_result
                })

        # Add tool results as single message
        if tool_results:
            messages.append({"role": "user", "content": tool_results})

        return messages

    def _handle_tool_execution(self, initial_response, base_params: Dict[str, Any], tool_manager):
        """
        Handle execution of tool calls and get follow-up response.

        Args:
            initial_response: The response containing tool use requests
            base_params: Base API parameters
            tool_manager: Manager to execute tools

        Returns:
            Final response text after tool execution
        """
        # Start with existing messages
        messages = base_params["messages"].copy()

        # Execute tools and build messages
        messages = self._execute_tools_and_build_messages(initial_response, messages, tool_manager)

        # Prepare final API call without tools
        final_params = {
            **self.base_params,
            "messages": messages,
            "system": base_params["system"]
        }

        # Get final response
        final_response = self.client.messages.create(**final_params)
        return final_response.content[0].text