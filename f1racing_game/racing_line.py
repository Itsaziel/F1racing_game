import pygame
import math
import json
import os

class RacingLine:
    """
    Represents a racing line that the AI car can follow.
    The racing line is a series of waypoints that define the optimal path around the track.
    """
    def __init__(self):
        self.waypoints = []
        self.current_waypoint_index = 0
        self.recording = False
        self.last_recorded_time = 0
        self.recording_interval = 0.1  # Record a point every 0.1 seconds
        
        # Colors
        self.line_color = (255, 165, 0)  # Orange
        self.waypoint_color = (255, 255, 0)  # Yellow
    
    def start_recording(self):
        """Start recording player positions to create a racing line"""
        self.waypoints = []
        self.current_waypoint_index = 0
        self.recording = True
        self.last_recorded_time = pygame.time.get_ticks() / 1000.0
        print("Started recording racing line")
    
    def stop_recording(self):
        """Stop recording player positions"""
        self.recording = False
        print(f"Stopped recording racing line with {len(self.waypoints)} waypoints")
    
    def record_player_position(self, player_car):
        """Record the player's position as a waypoint"""
        if not self.recording:
            return
        
        # Only record at specified intervals to avoid too many points
        current_time = pygame.time.get_ticks() / 1000.0
        if current_time - self.last_recorded_time < self.recording_interval:
            return
        
        # Record the position
        self.waypoints.append({
            "x": player_car.x,
            "y": player_car.y,
            "speed": player_car.speed,
            "angle": player_car.angle
        })
        
        self.last_recorded_time = current_time
    
    def get_current_waypoint(self):
        """Get the current waypoint the AI should target"""
        if not self.waypoints or self.current_waypoint_index >= len(self.waypoints):
            return None
        
        return self.waypoints[self.current_waypoint_index]
    
    def get_next_waypoints(self, count=3):
        """Get the next few waypoints for look-ahead behavior"""
        if not self.waypoints:
            return []
        
        next_waypoints = []
        for i in range(1, count + 1):
            index = (self.current_waypoint_index + i) % len(self.waypoints)
            next_waypoints.append(self.waypoints[index])
        
        return next_waypoints
    
    def advance_waypoint(self):
        """Move to the next waypoint and return True if a lap is completed"""
        if not self.waypoints:
            return False
        
        self.current_waypoint_index = (self.current_waypoint_index + 1) % len(self.waypoints)
        
        # Return True if we've completed a lap
        return self.current_waypoint_index == 0
    
    def render(self, surface, offset_x=0, offset_y=0):
        """Render the racing line on the screen"""
        if not self.waypoints:
            return
        
        # Draw lines connecting waypoints
        for i in range(len(self.waypoints)):
            start_point = self.waypoints[i]
            end_point = self.waypoints[(i + 1) % len(self.waypoints)]
            
            start_pos = (start_point["x"] + offset_x, start_point["y"] + offset_y)
            end_pos = (end_point["x"] + offset_x, end_point["y"] + offset_y)
            
            # Draw line with alpha for better visibility
            pygame.draw.line(surface, self.line_color, start_pos, end_pos, 2)
        
        # Highlight current waypoint
        if self.current_waypoint_index < len(self.waypoints):
            current = self.waypoints[self.current_waypoint_index]
            current_pos = (current["x"] + offset_x, current["y"] + offset_y)
            pygame.draw.circle(surface, self.waypoint_color, current_pos, 5)
    
    def save_to_file(self, filename="racing_line.json"):
        """Save the racing line to a file"""
        if not self.waypoints:
            print("No waypoints to save")
            return False
        
        # Create directory if it doesn't exist
        save_dir = os.path.join(os.path.dirname(__file__), "data")
        os.makedirs(save_dir, exist_ok=True)
        
        # Save to file
        save_path = os.path.join(save_dir, filename)
        try:
            with open(save_path, "w") as f:
                json.dump(self.waypoints, f)
            print(f"Racing line saved to {save_path}")
            return True
        except Exception as e:
            print(f"Error saving racing line: {e}")
            return False
    
    def load_from_file(self, filename="racing_line.json"):
        """Load a racing line from a file"""
        load_path = os.path.join(os.path.dirname(__file__), "data", filename)
        
        if not os.path.exists(load_path):
            print(f"Racing line file not found: {load_path}")
            return False
        
        try:
            with open(load_path, "r") as f:
                self.waypoints = json.load(f)
            
            self.current_waypoint_index = 0
            print(f"Racing line loaded from {load_path} with {len(self.waypoints)} waypoints")
            return True
        except Exception as e:
            print(f"Error loading racing line: {e}")
            return False