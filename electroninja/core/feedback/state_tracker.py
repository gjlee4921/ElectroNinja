# state_tracker.py

import logging
from copy import deepcopy

logger = logging.getLogger('electroninja')

class StateTracker:
    """Tracks the state of the feedback loop"""
    
    def __init__(self, request, max_iterations=5):
        self.state = {
            "request": request,
            "iteration": 0,
            "history": [],
            "max_iterations": max_iterations,
            "success": False
        }
        
    def get_state(self):
        """Get the current state"""
        return deepcopy(self.state)
        
    def increment_iteration(self):
        """Increment the iteration counter"""
        self.state["iteration"] += 1
        logger.info(f"Iteration incremented to {self.state['iteration']}")
        return self.state["iteration"]
        
    def add_asc_attempt(self, iteration, asc_code):
        """Add an ASC code attempt to history"""
        self.state["history"].append({
            "iteration": iteration,
            "asc_code": asc_code
        })
        logger.info(f"Added ASC attempt for iteration {iteration}")
        
    def add_vision_feedback(self, iteration, feedback):
        """Add vision feedback to history"""
        self.state["history"].append({
            "iteration": iteration,
            "vision_feedback": feedback
        })
        logger.info(f"Added vision feedback for iteration {iteration}")
        
    def set_success(self, success):
        """Set the success flag"""
        self.state["success"] = success
        logger.info(f"Set success flag to {success}")
        
    def is_max_iterations_reached(self):
        """Check if max iterations is reached"""
        return self.state["iteration"] >= self.state["max_iterations"]
        
    def get_iteration(self):
        """Get the current iteration"""
        return self.state["iteration"]
        
    def get_history(self):
        """Get the conversation history"""
        return deepcopy(self.state["history"])
        
    def get_request(self):
        """Get the original request"""
        return self.state["request"]