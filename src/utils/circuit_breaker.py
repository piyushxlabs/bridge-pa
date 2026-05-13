import time
from collections import deque

class CircuitBreaker:
    def __init__(self, time_window_seconds=300, threshold=3):
        self.time_window_seconds = time_window_seconds
        self.threshold = threshold
        self.events = deque()

    def record_emergency_stop(self, case_id: str):
        self.events.append((time.time(), case_id))

    def is_circuit_open(self) -> bool:
        current_time = time.time()
        # Remove events outside the time window
        while self.events and current_time - self.events[0][0] > self.time_window_seconds:
            self.events.popleft()
        
        # Count unique case IDs
        unique_cases = set()
        for t, cid in self.events:
            unique_cases.add(cid)
            
        return len(unique_cases) >= self.threshold

# Module-level singleton
circuit_breaker = CircuitBreaker()
