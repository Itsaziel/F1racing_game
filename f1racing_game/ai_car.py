import pygame
import math
import random
from car import Car

class AICar(Car):
    """
    Enhanced AI car with racing line following behavior.
    """
    def __init__(self, x, y, car_type="ai", assets=None):
        super().__init__(x, y, car_type, assets)
        self.racing_line = None
        self.target_waypoint = None
        self.next_waypoints = []
        self.lap_completed = False
        self.current_lap = 1
        self.total_laps = 5
        self.race_complete = False
        
        # AI-specific properties
        self.steering_adjustment = 0
        self.speed_adjustment = 0
        self.recovery_timer = 0
        self.stuck_timer = 0
        self.last_position = (x, y)
        self.last_position_time = 0
        self.avoiding_player = False
        self.blocking_player = False
        
        # For debugging
        self.debug_mode = False
        
        # Keys simulation for AI
        self.simulated_keys = {
            pygame.K_UP: False,
            pygame.K_DOWN: False,
            pygame.K_LEFT: False,
            pygame.K_RIGHT: False,
            pygame.K_SPACE: False
        }
    
    def set_racing_line(self, racing_line):
        """Set the racing line for this AI car to follow"""
        self.racing_line = racing_line
        self.update_target_waypoints()
        print("Racing line set for AI car with", len(racing_line.waypoints), "waypoints")
    
    def update_target_waypoints(self):
        """Update the target waypoint and next waypoints"""
        if not self.racing_line:
            return
            
        self.target_waypoint = self.racing_line.get_current_waypoint()
        self.next_waypoints = self.racing_line.get_next_waypoints(5)  # Look ahead 5 waypoints
    
    def update(self, keys=None, track=None):
        """Update AI car position and state by simulating key presses"""
        if not self.racing_line or self.race_complete:
            return
        
        # Reset simulated keys
        for key in self.simulated_keys:
            self.simulated_keys[key] = False
        
        # Update target waypoints
        self.update_target_waypoints()
        
        if not self.target_waypoint:
            return
        
        # Calculate distance to waypoint
        target_x, target_y = self.target_waypoint["x"], self.target_waypoint["y"]
        dx = target_x - self.x
        dy = target_y - self.y
        distance = math.hypot(dx, dy)
        
        # Check if we've reached the waypoint
        waypoint_radius = 25  # Smaller radius for more precise following
        if distance < waypoint_radius:
            # Move to next waypoint
            lap_completed = self.racing_line.advance_waypoint()
            if lap_completed:
                self.lap_completed = True
                self.current_lap += 1
                print(f"AI completed lap {self.current_lap-1}")
                if self.current_lap > self.total_laps:
                    self.race_complete = True
            
            # Update target waypoints
            self.update_target_waypoints()
            if not self.target_waypoint:
                return
            
            target_x, target_y = self.target_waypoint["x"], self.target_waypoint["y"]
            dx = target_x - self.x
            dy = target_y - self.y
            distance = math.hypot(dx, dy)
        
        # Calculate angle to waypoint
        target_angle = math.degrees(math.atan2(dy, dx))
        # Convert to pygame angle (0 is up, clockwise)
        target_angle = (90 - target_angle) % 360
        
        # Calculate angle difference
        angle_diff = (target_angle - self.angle) % 360
        if angle_diff > 180:
            angle_diff -= 360
        
        # Look ahead to next waypoints for smoother cornering
        look_ahead_angle = angle_diff
        if self.next_waypoints:
            # Calculate weighted average angle to next few waypoints
            total_weight = 0
            weighted_angle = 0
            
            for i, waypoint in enumerate(self.next_waypoints):
                weight = 1.0 / (i + 1)  # Higher weight for closer waypoints
                wp_dx = waypoint["x"] - self.x
                wp_dy = waypoint["y"] - self.y
                wp_angle = math.degrees(math.atan2(wp_dy, wp_dx))
                wp_angle = (90 - wp_angle) % 360
                
                wp_angle_diff = (wp_angle - self.angle) % 360
                if wp_angle_diff > 180:
                    wp_angle_diff -= 360
                
                weighted_angle += wp_angle_diff * weight
                total_weight += weight
            
            if total_weight > 0:
                look_ahead_angle = weighted_angle / total_weight
        
        # Determine if we're approaching a corner
        is_cornering = abs(look_ahead_angle) > 30
        
        # Determine target speed based on situation
        base_speed = 8.0  # Base speed
        
        # Slow down for corners based on sharpness
        if is_cornering:
            corner_factor = min(1.0, abs(look_ahead_angle) / 90.0)  # How sharp is the corner
            target_speed = base_speed * (1.0 - corner_factor * 0.7)  # Reduce speed by up to 70% for sharp corners
            
            # Slow down more for very sharp corners
            if abs(look_ahead_angle) > 60:
                target_speed *= 0.7
        else:
            target_speed = base_speed
        
        # Adjust speed based on distance to waypoint
        if distance < 50:
            # Look ahead to see if next waypoint requires a sharp turn
            if self.next_waypoints and len(self.next_waypoints) > 0:
                next_wp = self.next_waypoints[0]
                next_dx = next_wp["x"] - target_x
                next_dy = next_wp["y"] - target_y
                next_angle = math.degrees(math.atan2(next_dy, next_dx))
                next_angle = (90 - next_angle) % 360
                
                # Calculate angle difference between current and next waypoint
                next_angle_diff = (next_angle - target_angle) % 360
                if next_angle_diff > 180:
                    next_angle_diff -= 360
                
                # If next turn is sharp, slow down more
                if abs(next_angle_diff) > 45:
                    target_speed *= 0.8
        
        # Check if we're stuck
        current_time = pygame.time.get_ticks() / 1000.0  # Current time in seconds
        if current_time - self.last_position_time > 0.5:  # Check every half second
            current_pos = (self.x, self.y)
            dx = current_pos[0] - self.last_position[0]
            dy = current_pos[1] - self.last_position[1]
            movement = math.hypot(dx, dy)
            
            if movement < 5:  # If we've moved less than 5 pixels
                self.stuck_timer += 0.5
            else:
                self.stuck_timer = 0
                
            self.last_position = current_pos
            self.last_position_time = current_time
        
        # If stuck for more than 1.5 seconds, try to recover
        if self.stuck_timer > 1.5:
            print("AI car is stuck, trying to recover")
            # Reverse for a bit
            self.simulated_keys[pygame.K_DOWN] = True
            self.simulated_keys[pygame.K_UP] = False
            
            # Turn sharply away from obstacle
            if random.random() < 0.5:
                self.simulated_keys[pygame.K_LEFT] = True
            else:
                self.simulated_keys[pygame.K_RIGHT] = True
                
            # Reset stuck timer after a while
            if self.stuck_timer > 3.0:
                self.stuck_timer = 0
                
            # Skip the rest of the update
            super().update(self.simulated_keys, track)
            return
        
        # Simulate key presses based on AI decisions
        
        # Acceleration/Braking - more nuanced control
        if self.speed < target_speed - 0.5:
            # Need to accelerate
            self.simulated_keys[pygame.K_UP] = True
            self.simulated_keys[pygame.K_DOWN] = False
        elif self.speed > target_speed + 0.5:
            # Need to brake
            if self.speed > target_speed + 2.0:
                # Hard braking
                self.simulated_keys[pygame.K_DOWN] = True
                self.simulated_keys[pygame.K_UP] = False
            else:
                # Soft braking - just release accelerator
                self.simulated_keys[pygame.K_UP] = False
                self.simulated_keys[pygame.K_DOWN] = False
        else:
            # Maintain speed
            self.simulated_keys[pygame.K_UP] = True
            self.simulated_keys[pygame.K_DOWN] = False
        
        # Steering - more precise with proportional control
        steering_intensity = min(1.0, abs(look_ahead_angle) / 45.0)
        
        # Apply steering based on angle difference
        if abs(look_ahead_angle) > 1:  # Very small dead zone for precise following
            if look_ahead_angle > 0:
                # Need to turn left
                self.simulated_keys[pygame.K_LEFT] = True
                self.simulated_keys[pygame.K_RIGHT] = False
                
                # Pulse the steering for more natural control on gentle curves
                if steering_intensity < 0.2 and random.random() < 0.2:
                    self.simulated_keys[pygame.K_LEFT] = False
            else:
                # Need to turn right
                self.simulated_keys[pygame.K_LEFT] = False
                self.simulated_keys[pygame.K_RIGHT] = True
                
                # Pulse the steering for more natural control on gentle curves
                if steering_intensity < 0.2 and random.random() < 0.2:
                    self.simulated_keys[pygame.K_RIGHT] = False
        else:
            # Go straight
            self.simulated_keys[pygame.K_LEFT] = False
            self.simulated_keys[pygame.K_RIGHT] = False
        
        # Call the parent class update method with our simulated keys
        super().update(self.simulated_keys, track)
    
    def render(self, surface, offset_x=0, offset_y=0):
        """Render the AI car and debug information if enabled"""
        # Call the parent class render method
        super().render(surface, offset_x, offset_y)
        
        # Draw debug information if enabled
        if self.debug_mode and self.racing_line:
            # Draw line to target waypoint
            if self.target_waypoint:
                target_x = self.target_waypoint["x"] + offset_x
                target_y = self.target_waypoint["y"] + offset_y
                pygame.draw.line(surface, (255, 0, 0), 
                                (self.x + offset_x, self.y + offset_y), 
                                (target_x, target_y), 2)
                
                # Draw circle around target waypoint
                pygame.draw.circle(surface, (255, 0, 0), 
                                  (int(target_x), int(target_y)), 10, 2)
            
            # Draw lines to next waypoints
            for i, waypoint in enumerate(self.next_waypoints):
                wp_x = waypoint["x"] + offset_x
                wp_y = waypoint["y"] + offset_y
                
                # Different color for each waypoint
                color = (255, 255 - i * 40, 0)
                
                pygame.draw.circle(surface, color, 
                                  (int(wp_x), int(wp_y)), 5, 1)
    
    def handle_collision(self):
        """Handle collision with track boundaries"""
        # Reduce speed
        self.speed *= 0.5
        
        # Increment stuck timer to trigger recovery behavior
        self.stuck_timer += 0.5
        
        # Call parent method
        super().handle_collision()
    
    def respawn(self, x, y, angle):
        """Respawn the AI car at the specified position and angle"""
        self.x = x
        self.y = y
        self.angle = angle
        self.speed = 0
        self.velocity_x = 0
        self.velocity_y = 0
        self.stuck_timer = 0
        self.last_position = (x, y)
        self.last_position_time = pygame.time.get_ticks() / 1000.0