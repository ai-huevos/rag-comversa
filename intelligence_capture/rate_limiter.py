"""
Shared rate limiter for parallel processing
Ensures all workers respect OpenAI rate limits
"""
import time
import threading
from collections import deque
from datetime import datetime, timedelta


class RateLimiter:
    """
    Thread-safe rate limiter for API calls
    Tracks calls across all workers and enforces limits
    """
    
    def __init__(self, max_calls_per_minute=50):
        """
        Initialize rate limiter
        
        Args:
            max_calls_per_minute: Maximum API calls per minute (default: 50)
                                 Set below OpenAI limit (60) for safety margin
        """
        self.max_calls = max_calls_per_minute
        self.calls = deque()  # Track timestamps of recent calls
        self.lock = threading.Lock()  # Thread-safe access
        
    def wait_if_needed(self):
        """
        Wait if rate limit would be exceeded
        Call this BEFORE making an API call
        """
        with self.lock:
            now = datetime.now()
            one_minute_ago = now - timedelta(minutes=1)
            
            # Remove calls older than 1 minute
            while self.calls and self.calls[0] < one_minute_ago:
                self.calls.popleft()
            
            # Check if we're at the limit
            if len(self.calls) >= self.max_calls:
                # Calculate how long to wait
                oldest_call = self.calls[0]
                wait_until = oldest_call + timedelta(minutes=1)
                wait_seconds = (wait_until - now).total_seconds()
                
                if wait_seconds > 0:
                    print(f"  ⏳ Rate limit: waiting {wait_seconds:.1f}s...")
                    time.sleep(wait_seconds + 0.1)  # Add small buffer
                    
                    # Clean up old calls after waiting
                    now = datetime.now()
                    one_minute_ago = now - timedelta(minutes=1)
                    while self.calls and self.calls[0] < one_minute_ago:
                        self.calls.popleft()
            
            # Record this call
            self.calls.append(now)
    
    def get_current_rate(self):
        """Get current calls per minute"""
        with self.lock:
            now = datetime.now()
            one_minute_ago = now - timedelta(minutes=1)
            
            # Count calls in last minute
            recent_calls = sum(1 for call_time in self.calls if call_time > one_minute_ago)
            return recent_calls


# Global rate limiter instances (keyed by model/provider)
_rate_limiters = {}


def get_rate_limiter(max_calls_per_minute=50, key: str = "default"):
    """Get or create a rate limiter keyed by model/provider."""
    limiter = _rate_limiters.get(key)
    if limiter is None:
        limiter = RateLimiter(max_calls_per_minute)
        _rate_limiters[key] = limiter
    return limiter
