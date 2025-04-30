import pygame
import math
import random
import neat
import os
import pickle
from car import Car

class NeatAICar(Car):
    """
    AI car controlled by a NEAT neural network.
    """
    def __init__(self, x, y, car_type="ai", assets=None, genome=None, config=None):
        super().__init__(x, y, car_type, assets)
        
        # NEAT neural network
        self.genome = genome
        self.config = config
        
        if genome and config:
            self.neural_network = neat.nn.FeedForwardNetwork.create(genome, config)
        else:
            self.neural_network = None
        
        # Sensors for detecting track boundaries
        self.sensor_count = 8
        self.sensor_length = 200
        self.sensor_angles = [i * (360 / self.sensor_count) for i in range(self.sensor_count)]
        self.sensor_readings = [0] * self.sensor_count
        
        # Performance metrics
        self.distance_traveled = 0
        self.last_position = (x, y)
        self.checkpoint_count = 0
        self.last_checkpoint_time = pygame.time.get_ticks()
        self.collision_count = 0
        self.fitness = 0
        self.time_alive = 0
        self.start_time = pygame.time.get_ticks()
        
        # Keys simulation for AI
        self.simulated_keys = {
            pygame.K_UP: False,
            pygame.K_DOWN: False,
            pygame.K_LEFT: False,
            pygame.K_RIGHT: False,
            pygame.K_SPACE: False
        }
    
    def update_sensors(self, track):
        """Update sensor readings based on track boundaries"""
        for i, angle in enumerate(self.sensor_angles):
            # Calculate sensor direction
            sensor_angle = (self.angle + angle) % 360
            rad_angle = math.radians(sensor_angle)
            
            # Calculate sensor endpoint
            end_x = self.x + math.sin(rad_angle) * self.sensor_length
            end_y = self.y - math.cos(rad_angle) * self.sensor_length
            
            # Check for intersection with track boundaries
            min_distance = self.sensor_length
            
            # Check all track segments
            for segment in track.boundaries:
                # Check intersection with track segment
                intersection = self.line_intersection(
                    (self.x, self.y), (end_x, end_y),
                    segment[0], segment[1]
                )
                
                if intersection:
                    # Calculate distance to intersection
                    dx = intersection[0] - self.x
                    dy = intersection[1] - self.y
                    distance = math.sqrt(dx*dx + dy*dy)
                    
                    if distance < min_distance:
                        min_distance = distance
            
            # Normalize reading (0 = no obstacle, 1 = obstacle very close)
            self.sensor_readings[i] = 1.0 - (min_distance / self.sensor_length)
    
    def line_intersection(self, line1_start, line1_end, line2_start, line2_end):
        """Calculate intersection point of two line segments"""
        x1, y1 = line1_start
        x2, y2 = line1_end
        x3, y3 = line2_start
        x4, y4 = line2_end
        
        # Calculate determinants
        den = (y4 - y3) * (x2 - x1) - (x4 - x3) * (y2 - y1)
        
        # Lines are parallel
        if den == 0:
            return None
        
        ua = ((x4 - x3) * (y1 - y3) - (y4 - y3) * (x1 - x3)) / den
        ub = ((x2 - x1) * (y1 - y3) - (y2 - y1) * (x1 - x3)) / den
        
        # Check if intersection is within both line segments
        if 0 <= ua <= 1 and 0 <= ub <= 1:
            x = x1 + ua * (x2 - x1)
            y = y1 + ua * (y2 - y1)
            return (x, y)
        
        return None
    
    def update(self, keys=None, track=None):
        """Update AI car position and state using neural network"""
        if not self.neural_network or not track:
            return
        
        # Update sensors
        self.update_sensors(track)
        
        # Prepare neural network inputs
        inputs = self.sensor_readings.copy()
        
        # Add current speed as input (normalized)
        inputs.append(self.speed / 10.0)  # Assuming max speed is around 10
        
        # Get neural network output
        outputs = self.neural_network.activate(inputs)
        
        # Reset simulated keys
        for key in self.simulated_keys:
            self.simulated_keys[key] = False
        
        # Interpret neural network outputs
        # Output 0: Accelerate (forward/backward)
        if outputs[0] > 0.5:
            self.simulated_keys[pygame.K_UP] = True
        elif outputs[0] < -0.5:
            self.simulated_keys[pygame.K_DOWN] = True
            
        # Output 1: Steering (left/right)
        if outputs[1] > 0.5:
            self.simulated_keys[pygame.K_RIGHT] = True
        elif outputs[1] < -0.5:
            self.simulated_keys[pygame.K_LEFT] = True
        
        # Update performance metrics
        current_pos = (self.x, self.y)
        dx = current_pos[0] - self.last_position[0]
        dy = current_pos[1] - self.last_position[1]
        distance = math.sqrt(dx*dx + dy*dy)
        
        # Only count forward movement
        if self.speed > 0:
            self.distance_traveled += distance
        
        self.last_position = current_pos
        self.time_alive = (pygame.time.get_ticks() - self.start_time) / 1000.0
        
        # Call the parent class update method with our simulated keys
        super().update(self.simulated_keys, track)
    
    def handle_collision(self):
        """Handle collision with track boundaries"""
        self.collision_count += 1
        super().handle_collision()
    
    def calculate_fitness(self):
        """Calculate fitness score for this AI car"""
        # Base fitness on distance traveled
        fitness = self.distance_traveled
        
        # Bonus for staying alive longer
        fitness += self.time_alive * 10
        
        # Bonus for checkpoints reached
        fitness += self.checkpoint_count * 500
        
        # Penalty for collisions
        fitness -= self.collision_count * 100
        
        # Penalty for standing still
        if self.distance_traveled < 100 and self.time_alive > 5:
            fitness -= 500
        
        self.fitness = max(0, fitness)
        return self.fitness
    
    def render(self, surface, offset_x=0, offset_y=0):
        """Render the AI car and sensors"""
        # Call the parent class render method
        super().render(surface, offset_x, offset_y)
        
        # Draw sensors
        for i, angle in enumerate(self.sensor_angles):
            # Calculate sensor direction
            sensor_angle = (self.angle + angle) % 360
            rad_angle = math.radians(sensor_angle)
            
            # Calculate sensor endpoint
            length = self.sensor_length * (1 - self.sensor_readings[i])
            end_x = self.x + math.sin(rad_angle) * length
            end_y = self.y - math.cos(rad_angle) * length
            
            # Draw sensor line
            pygame.draw.line(
                surface,
                (255, 0, 0) if self.sensor_readings[i] > 0.5 else (0, 255, 0),
                (self.x + offset_x, self.y + offset_y),
                (end_x + offset_x, end_y + offset_y),
                1
            )