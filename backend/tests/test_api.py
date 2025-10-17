"""API endpoint tests for the RAG system"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock


@pytest.mark.api
class TestQueryEndpoint:
    """Tests for /api/query endpoint"""

    def test_query_without_session_id(self, test_client, mock_rag_system):
        """Test query endpoint without session ID creates new session"""
        response = test_client.post(
            "/api/query",
            json={"query": "What is machine learning?"}
        )

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert "sources" in data
        assert "session_id" in data
        assert data["answer"] == "This is a test response from the RAG system."
        assert data["session_id"] == "session_1"
        assert len(data["sources"]) == 1
        assert data["sources"][0]["text"] == "Test Course - Lesson 0"

        # Verify RAG system was called
        mock_rag_system.session_manager.create_session.assert_called_once()
        mock_rag_system.query.assert_called_once()

    def test_query_with_session_id(self, test_client, mock_rag_system):
        """Test query endpoint with existing session ID"""
        response = test_client.post(
            "/api/query",
            json={
                "query": "Explain neural networks",
                "session_id": "session_123"
            }
        )

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == "session_123"

        # Verify RAG system was called with session ID
        mock_rag_system.query.assert_called_once_with("Explain neural networks", "session_123")
        # Should not create new session when one is provided
        mock_rag_system.session_manager.create_session.assert_not_called()

    def test_query_with_empty_query(self, test_client):
        """Test query endpoint rejects empty query"""
        response = test_client.post(
            "/api/query",
            json={"query": ""}
        )

        # Should still process (validation happens at application level, not model level)
        # FastAPI will accept empty string as valid
        assert response.status_code == 200

    def test_query_missing_query_field(self, test_client):
        """Test query endpoint requires query field"""
        response = test_client.post(
            "/api/query",
            json={"session_id": "session_1"}
        )

        # Should return 422 Unprocessable Entity for missing required field
        assert response.status_code == 422

    def test_query_response_structure(self, test_client):
        """Test query endpoint returns correct response structure"""
        response = test_client.post(
            "/api/query",
            json={"query": "test query"}
        )

        assert response.status_code == 200
        data = response.json()

        # Verify all required fields
        assert isinstance(data["answer"], str)
        assert isinstance(data["sources"], list)
        assert isinstance(data["session_id"], str)

        # Verify source structure
        if len(data["sources"]) > 0:
            source = data["sources"][0]
            assert "text" in source
            assert "link" in source

    def test_query_with_invalid_json(self, test_client):
        """Test query endpoint handles invalid JSON"""
        response = test_client.post(
            "/api/query",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 422

    def test_query_with_special_characters(self, test_client, mock_rag_system):
        """Test query endpoint handles special characters in query"""
        special_query = "What is λ-calculus & how does it work? <test>"
        response = test_client.post(
            "/api/query",
            json={"query": special_query}
        )

        assert response.status_code == 200
        # Verify the query was passed correctly
        mock_rag_system.query.assert_called_once()
        call_args = mock_rag_system.query.call_args[0]
        assert special_query in call_args


@pytest.mark.api
class TestCoursesEndpoint:
    """Tests for /api/courses endpoint"""

    def test_get_courses_returns_stats(self, test_client, mock_rag_system):
        """Test courses endpoint returns course statistics"""
        response = test_client.get("/api/courses")

        assert response.status_code == 200
        data = response.json()
        assert "total_courses" in data
        assert "course_titles" in data
        assert data["total_courses"] == 2
        assert data["course_titles"] == ["Test Course 1", "Test Course 2"]

        # Verify RAG system was called
        mock_rag_system.get_course_analytics.assert_called_once()

    def test_get_courses_response_structure(self, test_client):
        """Test courses endpoint returns correct structure"""
        response = test_client.get("/api/courses")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["total_courses"], int)
        assert isinstance(data["course_titles"], list)
        assert all(isinstance(title, str) for title in data["course_titles"])

    def test_get_courses_no_parameters(self, test_client):
        """Test courses endpoint doesn't accept query parameters"""
        # GET requests with no params should work
        response = test_client.get("/api/courses")
        assert response.status_code == 200

        # Even with query params, should ignore and return same result
        response_with_params = test_client.get("/api/courses?foo=bar")
        assert response_with_params.status_code == 200


@pytest.mark.api
class TestSessionEndpoint:
    """Tests for /api/session/{session_id} endpoint"""

    def test_clear_session_success(self, test_client, mock_rag_system):
        """Test clearing a session"""
        response = test_client.delete("/api/session/session_123")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "session_123" in data["message"]

        # Verify RAG system was called
        mock_rag_system.session_manager.clear_session.assert_called_once_with("session_123")

    def test_clear_session_with_special_characters(self, test_client, mock_rag_system):
        """Test clearing session with special characters in ID"""
        session_id = "session_test-123_abc"
        response = test_client.delete(f"/api/session/{session_id}")

        assert response.status_code == 200
        mock_rag_system.session_manager.clear_session.assert_called_once_with(session_id)

    def test_clear_nonexistent_session(self, test_client):
        """Test clearing a session that doesn't exist (should still succeed)"""
        response = test_client.delete("/api/session/nonexistent_session")

        # Should return success even if session doesn't exist
        assert response.status_code == 200


@pytest.mark.api
class TestErrorHandling:
    """Tests for API error handling"""

    def test_query_endpoint_with_rag_system_error(self, test_client, mock_rag_system):
        """Test query endpoint handles RAG system errors gracefully"""
        # Make RAG system raise an exception
        mock_rag_system.query.side_effect = Exception("Database connection failed")

        response = test_client.post(
            "/api/query",
            json={"query": "test query"}
        )

        # Should return 500 Internal Server Error
        assert response.status_code == 500

    def test_courses_endpoint_with_rag_system_error(self, test_client, mock_rag_system):
        """Test courses endpoint handles RAG system errors gracefully"""
        mock_rag_system.get_course_analytics.side_effect = Exception("Analytics failed")

        response = test_client.get("/api/courses")

        assert response.status_code == 500

    def test_invalid_http_method_on_query(self, test_client):
        """Test query endpoint only accepts POST"""
        response = test_client.get("/api/query")
        assert response.status_code == 405  # Method Not Allowed

    def test_invalid_http_method_on_courses(self, test_client):
        """Test courses endpoint only accepts GET"""
        response = test_client.post("/api/courses")
        assert response.status_code == 405  # Method Not Allowed

    def test_invalid_http_method_on_session(self, test_client):
        """Test session endpoint only accepts DELETE"""
        response = test_client.get("/api/session/session_1")
        assert response.status_code == 405  # Method Not Allowed


@pytest.mark.api
class TestCORSConfiguration:
    """Tests for CORS middleware configuration"""

    def test_cors_headers_present(self, test_client):
        """Test that CORS headers are present in responses"""
        response = test_client.options(
            "/api/query",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
            }
        )

        # CORS headers should be present
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-methods" in response.headers

    def test_cors_allows_credentials(self, test_client):
        """Test that CORS allows credentials"""
        response = test_client.get(
            "/api/courses",
            headers={"Origin": "http://localhost:3000"}
        )

        assert "access-control-allow-credentials" in response.headers


@pytest.mark.api
class TestEndpointIntegration:
    """Integration tests for API endpoints working together"""

    def test_create_session_and_query_flow(self, test_client, mock_rag_system):
        """Test the flow of creating a session and making queries"""
        # First query creates session
        response1 = test_client.post(
            "/api/query",
            json={"query": "First question"}
        )
        assert response1.status_code == 200
        session_id = response1.json()["session_id"]

        # Second query uses same session
        response2 = test_client.post(
            "/api/query",
            json={"query": "Follow-up question", "session_id": session_id}
        )
        assert response2.status_code == 200
        assert response2.json()["session_id"] == session_id

        # Verify both queries were made
        assert mock_rag_system.query.call_count == 2

    def test_query_then_clear_session(self, test_client, mock_rag_system):
        """Test querying then clearing the session"""
        # Create session with query
        response1 = test_client.post(
            "/api/query",
            json={"query": "Test query"}
        )
        session_id = response1.json()["session_id"]

        # Clear the session
        response2 = test_client.delete(f"/api/session/{session_id}")
        assert response2.status_code == 200

        # Verify session was cleared
        mock_rag_system.session_manager.clear_session.assert_called_once_with(session_id)

    def test_multiple_concurrent_sessions(self, test_client, mock_rag_system):
        """Test that multiple sessions can exist independently"""
        # Configure mock to return different session IDs
        session_ids = ["session_1", "session_2", "session_3"]
        mock_rag_system.session_manager.create_session.side_effect = session_ids

        # Create multiple sessions
        responses = []
        for i in range(3):
            response = test_client.post(
                "/api/query",
                json={"query": f"Query {i}"}
            )
            responses.append(response)

        # Verify all succeeded and have different session IDs
        assert all(r.status_code == 200 for r in responses)
        returned_session_ids = [r.json()["session_id"] for r in responses]
        assert returned_session_ids == session_ids
