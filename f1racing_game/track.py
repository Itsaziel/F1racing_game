import pygame
import math
import random
import time  # For skid mark timestamps

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (100, 100, 100)
GREEN = (20, 120, 20)

class Track:
    def __init__(self, assets=None):
        self.width = 1200
        self.height = 900
        self.assets = assets
        self.total_laps = 15
        
        self.outer_boundary = self._create_rounded_track(
            [(150, 150), (1050, 150), (1050, 750), (150, 750)], corner_radius=100
        )
        self.inner_boundary = self._create_rounded_track(
            [(350, 300), (850, 300), (850, 600), (350, 600)], corner_radius=70
        )
        
        self.start_line = [(600, 150), (600, 300)]
        self.checkpoints = [
            [(1050, 450), (850, 450)],
            [(600, 750), (600, 600)],
            [(150, 450), (350, 450)],
            [(450, 150), (450, 300)],
        ]
        self.checkpoint_status = [False] * len(self.checkpoints)

        self.track_surface = None
        self.create_track_surface()
        self.decorations = []
        self.create_decorations()

        self.skid_marks = []

    def _create_rounded_track(self, corners, corner_radius):
        points = []
        num_corners = len(corners)
        for i in range(num_corners):
            current = corners[i]
            next_corner = corners[(i + 1) % num_corners]
            prev_corner = corners[(i - 1) % num_corners]
            to_next = (next_corner[0] - current[0], next_corner[1] - current[1])
            from_prev = (current[0] - prev_corner[0], current[1] - prev_corner[1])
            to_next_len = math.hypot(*to_next)
            from_prev_len = math.hypot(*from_prev)
            if to_next_len == 0 or from_prev_len == 0:
                points.append(current)
                continue
            to_next = (to_next[0]/to_next_len, to_next[1]/to_next_len)
            from_prev = (from_prev[0]/from_prev_len, from_prev[1]/from_prev_len)
            radius = min(corner_radius, to_next_len/2, from_prev_len/2)
            curve_start = (current[0] - from_prev[0] * radius, current[1] - from_prev[1] * radius)
            curve_end = (current[0] + to_next[0] * radius, current[1] + to_next[1] * radius)
            points.append(curve_start)
            for step in range(1, 10):
                t = step / 10
                point = (
                    curve_start[0] * (1-t) + curve_end[0] * t,
                    curve_start[1] * (1-t) + curve_end[1] * t
                )
                points.append(point)
            points.append(curve_end)
        return points

    def create_track_surface(self):
        self.track_surface = pygame.Surface((self.width, self.height))
        self.track_surface.fill(GREEN)
        track_polygon = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        pygame.draw.polygon(track_polygon, (255, 255, 255, 255), self.outer_boundary)
        pygame.draw.polygon(track_polygon, (0, 0, 0, 0), self.inner_boundary)
        if self.assets and self.assets.get_image("track_asphalt"):
            asphalt = self.assets.get_image("track_asphalt")
            for x in range(0, self.width, asphalt.get_width()):
                for y in range(0, self.height, asphalt.get_height()):
                    self.track_surface.blit(asphalt, (x, y))
        else:
            self.track_surface.fill(GRAY)
        self.track_surface.blit(track_polygon, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        pygame.draw.lines(self.track_surface, WHITE, True, self.outer_boundary, 5)
        pygame.draw.lines(self.track_surface, WHITE, True, self.inner_boundary, 5)
        pygame.draw.line(self.track_surface, WHITE, self.start_line[0], self.start_line[1], 5)
        start_x, start_y = self.start_line[0]
        end_x, end_y = self.start_line[1]
        length = math.hypot(end_x - start_x, end_y - start_y)
        for i in range(int(length / 10)):
            if i % 2 == 0:
                t1 = i / (length / 10)
                t2 = (i + 1) / (length / 10)
                x1 = start_x + (end_x - start_x) * t1
                y1 = start_y + (end_y - start_y) * t1
                x2 = start_x + (end_x - start_x) * t2
                y2 = start_y + (end_y - start_y) * t2
                pygame.draw.line(self.track_surface, BLACK, (x1, y1), (x2, y2), 5)

    def create_decorations(self):
        for _ in range(40):
            x = random.randint(0, self.width)
            y = random.randint(0, self.height)
            if self._point_in_polygon((x, y), self.outer_boundary) and not self._point_in_polygon((x, y), self.inner_boundary):
                continue
            size = random.randint(10, 30)
            self.decorations.append(("tree", x, y, size))
        self.decorations += [
            ("stand", 100, 100, 150),
            ("stand", 1000, 100, 150),
            ("stand", 100, 750, 150),
            ("stand", 1000, 750, 150),
        ]

    def add_skid_mark(self, x, y, size=3):
        """Add a fading skid mark"""
        created_time = time.time()
        self.skid_marks.append((x, y, size, created_time))

    def render(self, surface):
        surface.blit(self.track_surface, (0, 0))

        # Draw fading skid marks
        now = time.time()
        fade_duration = 3.0  # seconds
        new_skids = []
        for x, y, size, created_at in self.skid_marks:
            age = now - created_at
            if age < fade_duration:
                opacity = max(0, 255 * (1 - age / fade_duration))
                mark = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                pygame.draw.circle(mark, (30, 30, 30, int(opacity)), (size, size), size)
                surface.blit(mark, (x - size, y - size))
                new_skids.append((x, y, size, created_at))
        self.skid_marks = new_skids

        # Draw decorations
        for kind, x, y, size in self.decorations:
            if kind == "tree":
                pygame.draw.rect(surface, (100, 50, 0), (x - size//4, y, size//2, size))
                pygame.draw.circle(surface, (0, 100, 0), (x, y - size//2), size)
            elif kind == "stand":
                pygame.draw.rect(surface, (150, 150, 150), (x, y, size, size//4))
                for i in range(10):
                    for j in range(3):
                        dot_x = x + 5 + (i * (size - 10)) // 10
                        dot_y = y + 5 + j * (size//4 - 10) // 3
                        color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
                        pygame.draw.circle(surface, color, (dot_x, dot_y), 2)

    def _point_in_polygon(self, point, polygon):
        x, y = point
        n = len(polygon)
        inside = False
        p1x, p1y = polygon[0]
        for i in range(1, n + 1):
            p2x, p2y = polygon[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        return inside

    def check_collision(self, car):
        pos = (car.x, car.y)
        if not self._point_in_polygon(pos, self.outer_boundary):
            return True
        if self._point_in_polygon(pos, self.inner_boundary):
            return True
        return False

    def check_lap_completion(self, car):
        if self._line_circle_intersection(self.start_line[0], self.start_line[1], (car.x, car.y), 10):
            if all(self.checkpoint_status):
                if self.assets:
                    self.assets.play_sound("checkpoint")
                self.checkpoint_status = [False] * len(self.checkpoints)
                return True
        for i, cp in enumerate(self.checkpoints):
            if self._line_circle_intersection(cp[0], cp[1], (car.x, car.y), 10):
                if not self.checkpoint_status[i]:
                    self.checkpoint_status[i] = True
                    if self.assets:
                        self.assets.play_sound("checkpoint")
        return False

    def _line_circle_intersection(self, a, b, c, r):
        ax, ay = a
        bx, by = b
        cx, cy = c
        lab = math.hypot(bx - ax, by - ay)
        dx, dy = (bx - ax) / lab, (by - ay) / lab
        t = dx * (cx - ax) + dy * (cy - ay)
        ex, ey = ax + dx * t, ay + dy * t
        dist = math.hypot(ex - cx, ey - cy)
        return dist <= r

    # Add these methods to your Track class if they don't exist:
    
    def check_checkpoint(self, car):
        """Check if car has crossed a checkpoint"""
        for checkpoint in self.checkpoints:
            # Check if car crosses the checkpoint line
            if self.line_intersection(
                (car.x, car.y),
                (car.x - car.velocity_x, car.y - car.velocity_y),
                checkpoint[0], checkpoint[1]
            ):
                return True
        return False
    
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
            return False
        
        ua = ((x4 - x3) * (y1 - y3) - (y4 - y3) * (x1 - x3)) / den
        ub = ((x2 - x1) * (y1 - y3) - (y2 - y1) * (x1 - x3)) / den
        
        # Check if intersection is within both line segments
        if 0 <= ua <= 1 and 0 <= ub <= 1:
            return True
        
        return False
