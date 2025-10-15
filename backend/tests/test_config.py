"""Tests for configuration validation"""
import pytest
from config import config


class TestConfigValidation:
    """Test that configuration values are valid"""

    def test_max_results_is_positive(self):
        """
        CRITICAL TEST: MAX_RESULTS must be greater than 0

        This test catches the bug where MAX_RESULTS=0 causes
        all vector searches to return 0 results, breaking the
        entire search functionality.
        """
        assert config.MAX_RESULTS > 0, (
            f"MAX_RESULTS must be > 0, got {config.MAX_RESULTS}. "
            "Setting MAX_RESULTS=0 causes vector searches to return no results!"
        )

    def test_max_results_is_reasonable(self):
        """MAX_RESULTS should be a reasonable number (typically 1-20)"""
        assert 1 <= config.MAX_RESULTS <= 20, (
            f"MAX_RESULTS should be between 1 and 20, got {config.MAX_RESULTS}"
        )

    def test_chunk_size_is_positive(self):
        """CHUNK_SIZE must be greater than 0"""
        assert config.CHUNK_SIZE > 0, "CHUNK_SIZE must be positive"

    def test_chunk_size_is_reasonable(self):
        """CHUNK_SIZE should be reasonable (typically 100-2000 characters)"""
        assert 100 <= config.CHUNK_SIZE <= 2000, (
            f"CHUNK_SIZE should be between 100 and 2000, got {config.CHUNK_SIZE}"
        )

    def test_chunk_overlap_is_non_negative(self):
        """CHUNK_OVERLAP must be non-negative"""
        assert config.CHUNK_OVERLAP >= 0, "CHUNK_OVERLAP must be non-negative"

    def test_chunk_overlap_less_than_chunk_size(self):
        """CHUNK_OVERLAP must be less than CHUNK_SIZE"""
        assert config.CHUNK_OVERLAP < config.CHUNK_SIZE, (
            f"CHUNK_OVERLAP ({config.CHUNK_OVERLAP}) must be less than "
            f"CHUNK_SIZE ({config.CHUNK_SIZE})"
        )

    def test_max_history_is_non_negative(self):
        """MAX_HISTORY must be non-negative"""
        assert config.MAX_HISTORY >= 0, "MAX_HISTORY must be non-negative"

    def test_max_history_is_reasonable(self):
        """MAX_HISTORY should be reasonable (typically 0-10)"""
        assert config.MAX_HISTORY <= 10, (
            f"MAX_HISTORY should be <= 10, got {config.MAX_HISTORY}"
        )

    def test_anthropic_api_key_is_set(self):
        """ANTHROPIC_API_KEY should be configured"""
        # In production, this should be set. In tests, we can allow empty
        # but warn if it's missing
        if not config.ANTHROPIC_API_KEY:
            pytest.skip("ANTHROPIC_API_KEY not set (OK for unit tests)")

    def test_embedding_model_is_set(self):
        """EMBEDDING_MODEL must be configured"""
        assert config.EMBEDDING_MODEL, "EMBEDDING_MODEL must be set"
        assert len(config.EMBEDDING_MODEL) > 0, "EMBEDDING_MODEL cannot be empty"

    def test_chroma_path_is_set(self):
        """CHROMA_PATH must be configured"""
        assert config.CHROMA_PATH, "CHROMA_PATH must be set"
        assert len(config.CHROMA_PATH) > 0, "CHROMA_PATH cannot be empty"

    def test_anthropic_model_is_valid(self):
        """ANTHROPIC_MODEL should be a valid Claude model"""
        assert config.ANTHROPIC_MODEL, "ANTHROPIC_MODEL must be set"
        # Check it's a reasonable model name
        assert "claude" in config.ANTHROPIC_MODEL.lower(), (
            f"ANTHROPIC_MODEL should contain 'claude', got {config.ANTHROPIC_MODEL}"
        )
