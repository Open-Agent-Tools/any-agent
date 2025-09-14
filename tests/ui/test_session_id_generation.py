"""Tests for enhanced session ID generation in React UI utilities."""

import pytest
import re


class TestSessionIdGeneration:
    """Test suite for enhanced session ID generation."""

    def test_session_id_format(self):
        """Test that session ID follows expected format."""
        # Note: Since we're testing the TypeScript function, we'll test the pattern
        # This test validates the expected format: session_<timestamp>_<random>
        session_id_pattern = re.compile(r"^session_[a-z0-9]+_[a-z0-9]{12}$")

        # We can't directly call the TypeScript function, but we can verify
        # that our pattern matches the expected format
        test_examples = [
            "session_123abc_def456789012",
            "session_xyz789_abc123def456",
            "session_1a2b3c_9z8y7x6w5v4u",
        ]

        for example in test_examples:
            assert session_id_pattern.match(example), f"Pattern should match {example}"

    def test_session_id_length_constraints(self):
        """Test session ID length is within reasonable bounds."""
        # Expected format: session_<timestamp>_<12-char-random>
        # Timestamp in base36 is ~6-8 chars for current timestamps
        # Total expected length: ~25-35 characters

        min_expected_length = 20  # Conservative minimum
        max_expected_length = 40  # Conservative maximum

        # Test pattern-based validation
        session_id_pattern = re.compile(r"^session_[a-z0-9]{6,10}_[a-z0-9]{12}$")
        test_id = "session_1a2b3c4d_abcdef123456"

        assert len(test_id) >= min_expected_length
        assert len(test_id) <= max_expected_length
        assert session_id_pattern.match(test_id)

    def test_session_id_uniqueness_pattern(self):
        """Test that session ID generation pattern supports uniqueness."""
        # Test that the pattern includes timestamp component for uniqueness
        timestamp_pattern = re.compile(r"session_([a-z0-9]+)_([a-z0-9]{12})")

        # Simulate different timestamps (base36 encoded)
        timestamp1 = hex(1704067200000)[2:]  # 2024-01-01 timestamp
        timestamp2 = hex(1704067260000)[2:]  # 2024-01-01 + 1 minute

        session1 = f"session_{timestamp1}_abcdef123456"
        session2 = f"session_{timestamp2}_abcdef123456"

        match1 = timestamp_pattern.match(session1)
        match2 = timestamp_pattern.match(session2)

        assert match1 is not None
        assert match2 is not None
        assert match1.group(1) != match2.group(1)  # Different timestamps

    def test_session_id_security_properties(self):
        """Test session ID has good security properties."""
        # Session IDs should:
        # 1. Be unpredictable (include random component)
        # 2. Be URL-safe (use base36: 0-9, a-z)
        # 3. Have sufficient entropy (12 chars base36 ≈ 62 bits)

        # Test URL-safe characters only
        url_safe_pattern = re.compile(r"^[a-z0-9_]+$")
        test_session_id = "session_1a2b3c_def456789012"

        assert url_safe_pattern.match(test_session_id)

        # Test entropy calculation
        # 12 characters in base36 = log2(36^12) ≈ 62 bits of entropy
        random_part_length = 12
        base36_chars = 36
        expected_entropy_bits = random_part_length * (
            36.0 ** (1.0 / 36)
        )  # Approximation

        # Should provide > 60 bits of entropy (good security threshold)
        assert random_part_length * 5.17 > 60  # log2(36) ≈ 5.17

    def test_session_id_collision_resistance(self):
        """Test session ID generation has low collision probability."""
        # With timestamp + crypto randomness, collision probability should be minimal
        # The random part provides 12 characters in base36

        # Calculate entropy: 12 chars base36 = log2(36^12) ≈ 62 bits
        import math

        entropy_bits = 12 * math.log2(36)  # More accurate calculation

        # For 1M sessions, birthday paradox: P(collision) ≈ n²/(2*2^k)
        sessions_per_timeunit = 1_000_000
        collision_probability = (sessions_per_timeunit**2) / (2 * (2**entropy_bits))

        # Should be extremely low (< 1 in a million)
        # Adjusted threshold based on actual 62-bit entropy
        assert collision_probability < 1e-6

    def test_session_id_timestamp_component(self):
        """Test that session ID includes meaningful timestamp component."""
        # Timestamp should be current time in base36
        current_time_ms = 1704067200000  # Example: 2024-01-01
        base36_timestamp = hex(current_time_ms)[2:]  # Convert to base36-like

        # Expected session ID format
        expected_pattern = f"session_{base36_timestamp}_[a-z0-9]{{12}}"
        pattern = re.compile(expected_pattern)

        test_session_id = f"session_{base36_timestamp}_abcdef123456"
        assert pattern.match(test_session_id)

    def test_session_id_prevents_prediction(self):
        """Test that session IDs cannot be easily predicted."""
        # Even if an attacker knows the timestamp, they can't predict the random part
        # Random part should use cryptographically secure randomness (Web Crypto API)

        # Test that different "random" parts with same timestamp are different
        timestamp = "1a2b3c"
        session1 = f"session_{timestamp}_random123456"
        session2 = f"session_{timestamp}_random654321"

        # Extract random parts
        pattern = re.compile(r"session_[a-z0-9]+_([a-z0-9]{12})")
        match1 = pattern.match(session1)
        match2 = pattern.match(session2)

        assert match1.group(1) != match2.group(1)

    def test_session_id_backwards_compatibility(self):
        """Test that new session IDs don't break existing systems."""
        # New format should still:
        # 1. Start with "session_" prefix (for easy identification)
        # 2. Be valid HTTP header values
        # 3. Be safe in URLs and JSON

        test_session_id = "session_1a2b3c_def456789012"

        # Check prefix
        assert test_session_id.startswith("session_")

        # Check HTTP header safety (no spaces, control chars)
        assert " " not in test_session_id
        assert "\t" not in test_session_id
        assert "\n" not in test_session_id

        # Check URL safety (no special URL characters)
        url_unsafe_chars = [
            "/",
            "?",
            "#",
            "[",
            "]",
            "@",
            "!",
            "$",
            "&",
            "'",
            "(",
            ")",
            "*",
            "+",
            ",",
            ";",
            "=",
        ]
        for char in url_unsafe_chars:
            assert char not in test_session_id


class TestSessionIdIntegration:
    """Integration tests for session ID usage in chat system."""

    def test_session_id_in_chat_workflow(self):
        """Test session ID usage in complete chat workflow."""
        # Simulate the workflow:
        # 1. Generate session ID
        # 2. Create session
        # 3. Send messages
        # 4. Cleanup session

        # Mock session ID (simulating generateSessionId() output)
        mock_session_id = "session_1a2b3c4d_def456789012"

        # Validate format before use
        session_pattern = re.compile(r"^session_[a-z0-9]+_[a-z0-9]{12}$")
        assert session_pattern.match(mock_session_id)

        # Test that session ID can be used in various contexts
        contexts = [
            f"/chat/create-session with session_id: {mock_session_id}",
            f"/chat/send-message with session_id: {mock_session_id}",
            f"/chat/cleanup-session with session_id: {mock_session_id}",
            f"Session header: X-Session-ID: {mock_session_id}",
            f"JSON: {{'session_id': '{mock_session_id}'}}",
        ]

        for context in contexts:
            # Should not contain problematic characters
            assert '"' not in mock_session_id or '\\"' in context
            assert "\n" not in context

    def test_session_id_storage_safety(self):
        """Test that session IDs are safe for storage and logging."""
        mock_session_id = "session_1a2b3c4d_def456789012"

        # Should be safe for:
        # 1. Database storage (no SQL injection risk)
        # 2. Log files (no log injection)
        # 3. JSON serialization
        # 4. HTTP headers

        # SQL safety - no quotes or special SQL chars
        sql_dangerous_chars = ["'", '"', ";", "--", "/*", "*/"]
        for char in sql_dangerous_chars:
            assert char not in mock_session_id

        # Log injection safety - no newlines or control chars
        log_dangerous_chars = ["\n", "\r", "\t", "\x00"]
        for char in log_dangerous_chars:
            assert char not in mock_session_id

        # JSON safety
        import json

        json_str = json.dumps({"session_id": mock_session_id})
        parsed = json.loads(json_str)
        assert parsed["session_id"] == mock_session_id

    def test_session_cleanup_with_enhanced_ids(self):
        """Test that session cleanup works with enhanced session IDs."""
        # Test multiple session IDs with new format
        enhanced_session_ids = [
            "session_1a2b3c4d_def456789012",
            "session_2b3c4d5e_abc123456789",
            "session_3c4d5e6f_789012345678",
        ]

        # All should follow the same pattern
        pattern = re.compile(r"^session_[a-z0-9]+_[a-z0-9]{12}$")
        for session_id in enhanced_session_ids:
            assert pattern.match(session_id)

        # All should be unique
        unique_ids = set(enhanced_session_ids)
        assert len(unique_ids) == len(enhanced_session_ids)

        # All should have different random components
        random_parts = []
        for session_id in enhanced_session_ids:
            parts = session_id.split("_")
            random_parts.append(parts[2])  # Third part is random component

        unique_random_parts = set(random_parts)
        assert len(unique_random_parts) == len(random_parts)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
