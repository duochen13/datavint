"""
Rate Limiter - Simple in-memory rate limiting

Tracks requests per IP address with a sliding window.
Shared across all endpoints that need rate limiting.
"""

import time
from collections import defaultdict
from typing import Dict, List


class RateLimiter:
    """
    Simple in-memory rate limiter.

    Tracks requests per IP address with a sliding window.
    Thread-safe for single-process applications.
    """

    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        """
        Initialize rate limiter.

        Args:
            max_requests: Maximum requests allowed per window
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, List[float]] = defaultdict(list)

    def is_allowed(self, client_ip: str) -> bool:
        """
        Check if request is allowed under rate limit.

        Args:
            client_ip: Client IP address

        Returns:
            bool: True if request is allowed, False if rate limit exceeded
        """
        now = time.time()

        # Clean old requests outside the window
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip]
            if now - req_time < self.window_seconds
        ]

        # Check if under limit
        if len(self.requests[client_ip]) >= self.max_requests:
            return False

        # Record this request
        self.requests[client_ip].append(now)
        return True

    def get_retry_after(self, client_ip: str) -> int:
        """
        Get seconds until rate limit resets.

        Args:
            client_ip: Client IP address

        Returns:
            int: Seconds until oldest request expires (rate limit resets)
        """
        if not self.requests[client_ip]:
            return 0

        oldest_request = min(self.requests[client_ip])
        return int(self.window_seconds - (time.time() - oldest_request)) + 1


# Global rate limiter instance (10 requests per minute per IP)
rate_limiter = RateLimiter(max_requests=10, window_seconds=60)
