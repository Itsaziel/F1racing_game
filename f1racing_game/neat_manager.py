import os
import neat
import pickle
import pygame
import random
from neat_ai_car import NeatAICar

class NeatManager:
    """
    Manages a population of NEAT AI cars.
    """
    def __init__(self, track, assets, population_size=20):
        self.track = track
        self.assets = assets
        self.population_size = population_size
        self.generation = 0
        self.best_fitness = 0
        self.best_genome = None
        
        # Load configuration
        self.config_path = os.path.join(os.path.dirname(__file__), "neat_config.txt")
        if not os.path.exists(self.config_path):
            self.create_default_config()
        
        self.config = neat.Config(
            neat.DefaultGenome,
            neat.DefaultReproduction,
            neat.DefaultSpeciesSet,
            neat.DefaultStagnation,
            self.config_path
        )
        
        # Create population
        self.population = neat.Population(self.config)
        
        # Add reporters
        self.population.add_reporter(neat.StdOutReporter(True))
        self.population.add_reporter(neat.StatisticsReporter())
        
        # Current cars
        self.cars = []
        self.active_cars = 0
        
        # Simulation state
        self.simulation_running = False
        self.max_simulation_time = 60  # seconds
        self.simulation_start_time = 0
    
    def create_default_config(self):
        """Create a default NEAT configuration file"""
        config_text = """[NEAT]
fitness_criterion     = max
fitness_threshold     = 10000
pop_size              = 20
reset_on_extinction   = True

[DefaultGenome]
# node activation options
activation_default      = sigmoid
activation_mutate_rate  = 0.1
activation_options      = sigmoid tanh relu

# node aggregation options
aggregation_default     = sum
aggregation_mutate_rate = 0.0
aggregation_options     = sum

# node bias options
bias_init_mean          = 0.0
bias_init_stdev         = 1.0
bias_max_value          = 30.0
bias_min_value          = -30.0
bias_mutate_power       = 0.5
bias_mutate_rate        = 0.7
bias_replace_rate       = 0.1

# genome compatibility options
compatibility_disjoint_coefficient = 1.0
compatibility_weight_coefficient   = 0.5

# connection add/remove rates
conn_add_prob           = 0.5
conn_delete_prob        = 0.5

# connection enable options
enabled_default         = True
enabled_mutate_rate     = 0.01

feed_forward            = True
initial_connection      = full_direct

# node add/remove rates
node_add_prob           = 0.2
node_delete_prob        = 0.2

# network parameters
num_hidden              = 4
num_inputs              = 9
num_outputs             = 2

# node response options
response_init_mean      = 1.0
response_init_stdev     = 0.0
response_max_value      = 30.0
response_min_value      = -30.0
response_mutate_power   = 0.0
response_mutate_rate    = 0.0
response_replace_rate   = 0.0

# connection weight options
weight_init_mean        = 0.0
weight_init_stdev       = 1.0
weight_max_value        = 30
weight_min_value        = -30
weight_mutate_power     = 0.5
weight_mutate_rate      = 0.8
weight_replace_rate     = 0.1

[DefaultSpeciesSet]
compatibility_threshold = 3.0

[DefaultStagnation]
species_fitness_func = max
max_stagnation       = 15
species_elitism      = 2

[DefaultReproduction]
elitism            = 2
survival_threshold = 0.2
"""
        with open(self.config_path, "w") as f:
            f.write(config_text)
    
    def start_simulation(self):
        """Start a new simulation with the current population"""
        self.simulation_running = True
        self.simulation_start_time = pygame.time.get_ticks() / 1000.0
        
        # Create cars for each genome
        self.cars = []
        genomes = list(self.population.population.items())
        
        # Randomize starting positions slightly
        start_x, start_y = self.track.start_line[0]
        start_angle = 90  # Facing right
        
        for genome_id, genome in genomes:
            # Create a car with this genome
            x = start_x + random.randint(-10, 10)
            y = start_y + random.randint(-10, 10)
            
            car = NeatAICar(x, y, "ai", self.assets, genome, self.config)
            car.angle = start_angle
            
            self.cars.append(car)
        
        self.active_cars = len(self.cars)
        print(f"Starting generation {self.generation} with {self.active_cars} cars")
    
    def update(self):
        """Update all active cars and check for simulation end"""
        if not self.simulation_running:
            return
        
        # Check if simulation time limit is reached
        current_time = pygame.time.get_ticks() / 1000.0
        elapsed_time = current_time - self.simulation_start_time
        
        if elapsed_time > self.max_simulation_time:
            print(f"Simulation time limit reached ({self.max_simulation_time} seconds)")
            self.end_simulation()
            return
        
        # Update all active cars
        for car in self.cars:
            if car.active:
                car.update(None, self.track)
                
                # Check for collisions
                if self.track.check_collision(car):
                    car.handle_collision()
                
                # Check for checkpoint crossing
                if self.track.check_checkpoint(car):
                    car.checkpoint_count += 1
                    car.last_checkpoint_time = pygame.time.get_ticks()
                
                # Check for lap completion
                if self.track.check_lap_completion(car):
                    car.checkpoint_count += 10  # Bonus for completing a lap
                
                # Check for timeout (no progress)
                if pygame.time.get_ticks() - car.last_checkpoint_time > 10000:  # 10 seconds
                    car.active = False
                    self.active_cars -= 1
        
        # Check if all cars are inactive
        if self.active_cars == 0:
            self.end_simulation()
    
    def end_simulation(self):
        """End the current simulation and prepare for the next generation"""
        self.simulation_running = False
        
        # Calculate fitness for each car
        for car in self.cars:
            genome = car.genome
            genome.fitness = car.calculate_fitness()
            
            # Track best fitness
            if genome.fitness > self.best_fitness:
                self.best_fitness = genome.fitness
                self.best_genome = genome
                
                # Save best genome
                self.save_best_genome()
        
        # Create next generation
        self.generation += 1
        self.population.population = self.population.reproduction.reproduce(
            self.population.config, 
            self.population.species, 
            self.population.config.pop_size, 
            self.population.generation
        )
        
        # Print generation stats
        print(f"Generation {self.generation-1} complete")
        print(f"Best fitness: {self.best_fitness}")
        
        # Start next generation
        self.start_simulation()
    
    def render(self, surface, offset_x=0, offset_y=0):
        """Render all active cars"""
        for car in self.cars:
            if car.active:
                car.render(surface, offset_x, offset_y)
    
    def save_best_genome(self):
        """Save the best genome to a file"""
        save_dir = os.path.join(os.path.dirname(__file__), "data")
        os.makedirs(save_dir, exist_ok=True)
        
        with open(os.path.join(save_dir, "best_genome.pkl"), "wb") as f:
            pickle.dump(self.best_genome, f)
        
        print(f"Saved best genome with fitness {self.best_fitness}")
    
    def load_best_genome(self):
        """Load the best genome from a file"""
        genome_path = os.path.join(os.path.dirname(__file__), "data", "best_genome.pkl")
        
        if os.path.exists(genome_path):
            with open(genome_path, "rb") as f:
                self.best_genome = pickle.load(f)
            
            print(f"Loaded best genome from file")
            return self.best_genome
        
        return None
    
    def create_car_from_best_genome(self, x, y):
        """Create a car using the best genome"""
        if not self.best_genome:
            self.load_best_genome()
            
        if self.best_genome:
            car = NeatAICar(x, y, "ai", self.assets, self.best_genome, self.config)
            return car
        
        return None