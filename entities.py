"""
entities.py

Defines the core game entities, including celestial bodies, the player ship,
projectiles, missiles, and enemy ships. Handles their physics, behavior,
and rendering.
"""
import pygame
from vector import Vec2D # Assuming vector.py is in the same directory
import math

class PhysicsObject:
    """
    Base class for all objects in the game that are affected by physics (gravity, forces).
    Handles position, velocity, acceleration, mass, and basic physics updates.
    Also includes collision detection.
    """
    def __init__(self, mass, position_vec, velocity_vec=None, acceleration_vec=None, color=(255, 255, 255), radius=2):
        """
        Initializes a PhysicsObject.

        Args:
            mass (float): Mass of the object. Must be > 0.
            position_vec (Vec2D): Initial position vector.
            velocity_vec (Vec2D, optional): Initial velocity vector. Defaults to Vec2D(0,0).
            acceleration_vec (Vec2D, optional): Initial non-gravitational acceleration. Defaults to Vec2D(0,0).
            color (tuple, optional): RGB color tuple. Defaults to (255, 255, 255) (White).
            radius (int, optional): Radius in pixels for drawing and collision. Defaults to 2.
        """
        if mass <= 0:
            # Avoid division by zero in physics calculations if mass is zero or negative.
            # Using a very small positive mass instead.
            self.mass = 1e-6 
        else:
            self.mass = mass
        self.position_vec = position_vec
        self.velocity_vec = velocity_vec if velocity_vec is not None else Vec2D(0, 0)
        # Stores non-gravitational acceleration (e.g., from thrusters). Reset each frame after use.
        self.acceleration_vec = acceleration_vec if acceleration_vec is not None else Vec2D(0, 0) 
        self.color = color
        self.radius = radius

    def apply_force(self, force_vec):
        """
        Applies a force to the object, contributing to its non-gravitational acceleration
        for the current physics update cycle.
        F = m*a => a = F/m.

        Args:
            force_vec (Vec2D): The force vector to apply.
        """
        if self.mass == 0: return # Should be prevented by __init__ mass check
        self.acceleration_vec += force_vec / self.mass

    def update_physics(self, delta_time, list_of_celestial_bodies, G_constant):
        """
        Updates the object's velocity and position based on gravitational forces
        and any other applied forces (stored in self.acceleration_vec).
        Resets non-gravitational acceleration after applying it.

        Args:
            delta_time (float): Time elapsed since the last frame.
            list_of_celestial_bodies (list): List of CelestialBody objects to calculate gravity from.
            G_constant (float): The gravitational constant.
        """
        # 1. Calculate total gravitational force and resulting acceleration
        total_gravity_force = Vec2D(0, 0)
        for body in list_of_celestial_bodies:
            force_by_body = body.get_gravity_force_on(self.position_vec, self.mass, G_constant)
            total_gravity_force += force_by_body
        
        gravitational_acceleration = total_gravity_force / self.mass

        # 2. Total acceleration = non-gravitational (e.g., thrust) + gravitational
        total_acceleration = self.acceleration_vec + gravitational_acceleration

        # 3. Update velocity and position using total acceleration
        self.velocity_vec += total_acceleration * delta_time
        self.position_vec += self.velocity_vec * delta_time

        # 4. Reset non-gravitational acceleration for the next frame.
        # Forces like thrust must be applied each frame they are active.
        self.acceleration_vec = Vec2D(0, 0)

    def check_collision(self, other_object):
        """
        Checks for a circular collision with another object.

        Args:
            other_object (PhysicsObject or CelestialBody): The other object to check collision against.
                                                           Must have `position_vec` and `radius` attributes.

        Returns:
            bool: True if a collision is detected, False otherwise.
        """
        # Ensure the other object has the necessary attributes for collision detection.
        if not hasattr(other_object, 'position_vec') or not hasattr(other_object, 'radius'):
            # Log an error or warning, or handle as appropriate for your game.
            # print(f"Collision check failed: other_object missing attributes: {other_object}")
            return False 

        distance = self.position_vec.distance_to(other_object.position_vec)
        return distance < (self.radius + other_object.radius)

    def draw(self, screen, camera_offset_x=0, camera_offset_y=0):
        """
        Draws the physics object as a simple circle.
        Subclasses may override this for more specific drawing.

        Args:
            screen (pygame.Surface): The Pygame surface to draw on.
            camera_offset_x (float, optional): X offset for camera view. Defaults to 0.
            camera_offset_y (float, optional): Y offset for camera view. Defaults to 0.
        """
        on_screen_x = int(self.position_vec.x + camera_offset_x)
        on_screen_y = int(self.position_vec.y + camera_offset_y)
        pygame.draw.circle(screen, self.color, (on_screen_x, on_screen_y), self.radius)


class CelestialBody:
    """
    Represents a large celestial body like a planet or moon.
    Exerts gravitational force on PhysicsObjects.
    Is not a PhysicsObject itself; its position is fixed or pre-determined.
    """
    def __init__(self, mass, radius, position_vec, color, name="CelestialBody"):
        """
        Initializes a CelestialBody.

        Args:
            mass (float): Mass of the celestial body.
            radius (int): Radius in pixels.
            position_vec (Vec2D): Position vector (center of the body).
            color (tuple): RGB color tuple.
            name (str, optional): Name of the celestial body (e.g., "Planet", "Moon"). Defaults to "CelestialBody".
        """
        self.mass = mass
        self.radius = radius
        self.position_vec = position_vec
        self.color = color
        self.name = name
        # Initialize font for rendering the name (can be None if pygame.font is not initialized)
        try:
            self.font = pygame.font.SysFont(None, 24) 
        except Exception: # Broad exception if font system fails
            self.font = None


    def draw(self, screen, camera_offset_x=0, camera_offset_y=0):
        """
        Draws the celestial body and its name.

        Args:
            screen (pygame.Surface): The Pygame surface to draw on.
            camera_offset_x (float, optional): X offset for camera view. Defaults to 0.
            camera_offset_y (float, optional): Y offset for camera view. Defaults to 0.
        """
        on_screen_x = int(self.position_vec.x + camera_offset_x)
        on_screen_y = int(self.position_vec.y + camera_offset_y)

        pygame.draw.circle(screen, self.color, (on_screen_x, on_screen_y), self.radius)

        if self.font: # Only render text if font was successfully loaded
            name_surface = self.font.render(self.name, True, (255, 255, 255)) # White text
            name_rect = name_surface.get_rect(center=(on_screen_x, on_screen_y - self.radius - 10)) # Position above body
            screen.blit(name_surface, name_rect)

    def get_gravity_force_on(self, other_object_position_vec, other_object_mass, G_constant):
        """
        Calculates the gravitational force exerted by this celestial body on another object.

        Args:
            other_object_position_vec (Vec2D): Position vector of the other object.
            other_object_mass (float): Mass of the other object.
            G_constant (float): The gravitational constant.

        Returns:
            Vec2D: The gravitational force vector acting on the other object (directed towards this body).
        """
        # Vector from the other object to this celestial body (force direction)
        direction_vec = self.position_vec - other_object_position_vec

        distance_sq = direction_vec.x**2 + direction_vec.y**2

        # Prevent division by zero or instability at very small distances.
        # A minimum distance squared threshold helps avoid extremely large forces.
        min_distance_sq = max(1e-6, (self.radius * 0.1)**2) # Avoid issues if objects are too close or inside
        if distance_sq < min_distance_sq:
            # If objects are extremely close (e.g., inside each other),
            # the gravitational model might break down.
            # Returning zero force is a simple way to prevent instability.
            # More complex models might cap the force or handle surface interactions.
            return Vec2D(0, 0)

        force_magnitude = (G_constant * self.mass * other_object_mass) / distance_sq
        
        # Normalize the direction vector to get a unit vector
        # Check distance_sq again to be safe, though min_distance_sq should prevent it being zero.
        if distance_sq == 0: # Should ideally not happen due to min_distance_sq
            normalized_direction_vec = Vec2D(0,0)
        else:
            distance = math.sqrt(distance_sq)
            normalized_direction_vec = direction_vec / distance

class Projectile(PhysicsObject):
    """
    Represents a basic projectile fired by a weapon.
    Inherits from PhysicsObject for physics simulation.
    Has a limited lifespan.
    """
    def __init__(self, mass, position_vec, velocity_vec, color=(255, 200, 0), radius=2, lifespan=3.0):
        """
        Initializes a Projectile.

        Args:
            mass (float): Mass of the projectile.
            position_vec (Vec2D): Initial position vector.
            velocity_vec (Vec2D): Initial velocity vector.
            color (tuple, optional): RGB color tuple. Defaults to (255, 200, 0) (Orange).
            radius (int, optional): Radius in pixels. Defaults to 2.
            lifespan (float, optional): Time in seconds before the projectile disappears. Defaults to 3.0.
        """
        super().__init__(mass, position_vec, velocity_vec, color=color, radius=radius)
        self.lifespan = lifespan

    def update(self, delta_time):
        """
        Updates the projectile's state, primarily its lifespan.

        Args:
            delta_time (float): Time elapsed since the last frame in seconds.

        Returns:
            bool: True if the projectile is still active, False if its lifespan has expired.
        """
        self.lifespan -= delta_time
        return self.lifespan > 0

class PlayerShip(PhysicsObject):
    """
    Represents the player-controlled ship.
    Handles player input for movement (rotation, thrust) and firing weapons.
    Includes an orbit predictor and weapon cooldowns.
    """
    def __init__(self, mass, position_vec, velocity_vec=None, color=(0, 255, 0), thrust_strength=10000.0, rotation_speed=5.0):
        """
        Initializes the PlayerShip.

        Args:
            mass (float): Mass of the ship.
            position_vec (Vec2D): Initial position vector.
            velocity_vec (Vec2D, optional): Initial velocity vector. Defaults to Vec2D(0,0).
            color (tuple, optional): RGB color tuple. Defaults to (0, 255, 0) (Green).
            thrust_strength (float, optional): Force applied by the thruster. Defaults to 10000.0.
            rotation_speed (float, optional): Speed of rotation in degrees per second. Defaults to 5.0.
        """
        super().__init__(mass, position_vec, velocity_vec, color=color, radius=8) # Default radius 8
        self.thrust_strength = thrust_strength
        self.rotation_speed = rotation_speed  # Degrees per second
        self.angle = 0.0  # Degrees, 0 pointing right
        self.thruster_on = False
        self.projectiles_to_add = [] # Will store both Projectiles and HomingMissiles
        self.railgun_projectile_speed = 150.0
        self.railgun_recoil_strength = 150000.0
        self.railgun_projectile_mass = 2.0
        self.railgun_projectile_lifespan = 3.0

        # Orbit Predictor attributes
        self.orbit_prediction_points = []
        self.prediction_steps = 100 # Number of steps to predict
        self.prediction_delta_time = 0.15 # Time step for each prediction segment (reduced from 0.5)
        self.show_orbit_predictor = True

        # Weapon Cooldown attributes
        self.railgun_cooldown_time = 0.25 # seconds
        self.missile_cooldown_time = 1.0 # seconds
        self.last_railgun_fire_time = 0.0 # Time in seconds
        self.last_missile_fire_time = 0.0 # Time in seconds

        # Homing Missile attributes
        self.missile_fuel = 7.0
        self.missile_thrust = 75000.0
        self.missile_turn_rate = 120.0 # degrees/sec
        self.missile_lifespan = 15.0
        self.missile_mass = 15.0

    def fire_railgun(self):
        """
        Fires a railgun projectile if not on cooldown.
        Applies recoil to the ship.
        Adds the new projectile to `self.projectiles_to_add` for processing by the main game loop.
        """
        current_time_seconds = pygame.time.get_ticks() / 1000.0
        if current_time_seconds - self.last_railgun_fire_time < self.railgun_cooldown_time:
            return # Cooldown active
        self.last_railgun_fire_time = current_time_seconds
        
        rad = math.radians(self.angle)
        projectile_direction = Vec2D(math.cos(rad), math.sin(rad))

        # Projectile initial position: slightly ahead of the ship's nose
        nose_offset = self.radius + 3 # projectile radius is 2, ship radius is 8. (8 + 2 + buffer) -> 13
        projectile_start_pos = self.position_vec + projectile_direction * nose_offset 

        # Projectile initial velocity: ship's velocity + projectile's velocity relative to ship
        projectile_velocity = self.velocity_vec + projectile_direction * self.railgun_projectile_speed

        new_projectile = Projectile(
            mass=self.railgun_projectile_mass,
            position_vec=projectile_start_pos,
            velocity_vec=projectile_velocity,
            lifespan=self.railgun_projectile_lifespan,
            color=(255, 255, 0) # Bright yellow
        )
        self.projectiles_to_add.append(new_projectile)

        # Apply recoil to the ship
        # Recoil force should be opposite to projectile_direction
        recoil_force = projectile_direction * (-1 * self.railgun_recoil_strength) 
        self.apply_force(recoil_force)

    def fire_missile(self, target_obj):
        """
        Fires a homing missile if not on cooldown and a target is provided.
        Adds the new missile to `self.projectiles_to_add`.

        Args:
            target_obj (PhysicsObject or CelestialBody): The target for the missile.
        """
        current_time_seconds = pygame.time.get_ticks() / 1000.0
        if current_time_seconds - self.last_missile_fire_time < self.missile_cooldown_time:
            return # Cooldown active
        self.last_missile_fire_time = current_time_seconds

        if not target_obj: 
            return # Need a target

        rad = math.radians(self.angle)
        missile_direction = Vec2D(math.cos(rad), math.sin(rad))

        # Missile initial position: slightly ahead of the ship's nose
        missile_start_pos = self.position_vec + missile_direction * (self.radius + 5) # missile radius is 4, ship is 8. (8+4+buffer) -> ~17

        # Missile initial velocity: ship's velocity + a small forward push
        initial_missile_push_speed = 20.0 
        missile_velocity = self.velocity_vec + missile_direction * initial_missile_push_speed

        new_missile = HomingMissile(
            mass=self.missile_mass,
            position_vec=missile_start_pos,
            velocity_vec=missile_velocity,
            target=target_obj,
            lifespan=self.missile_lifespan,
            turn_rate_degrees_sec=self.missile_turn_rate,
            thrust_force=self.missile_thrust,
            fuel=self.missile_fuel,
            color=(0,200,255) # Cyan
        )
        self.projectiles_to_add.append(new_missile)

    def get_altitude(self, planet_obj):
        """
        Calculates the ship's altitude relative to the surface of a given celestial body.

        Args:
            planet_obj (CelestialBody): The celestial body to measure altitude from.

        Returns:
            float: The altitude in game units.
        """
        # Assumes planet_obj is a CelestialBody
        distance_to_center = (self.position_vec - planet_obj.position_vec).magnitude()
        altitude = distance_to_center - planet_obj.radius
        return altitude

    def get_speed(self):
        """
        Calculates the current speed (magnitude of velocity) of the ship.

        Returns:
            float: The ship's speed in game units per second.
        """
        return self.velocity_vec.magnitude()

    def predict_orbit(self, celestial_bodies_list, G_constant):
        """
        Simulates and predicts the ship's orbital path based on current velocity
        and gravitational forces from celestial bodies.
        The predicted path is stored in `self.orbit_prediction_points`.

        Args:
            celestial_bodies_list (list): A list of CelestialBody objects that exert gravity.
            G_constant (float): The gravitational constant used for the simulation.
        """
        if not self.show_orbit_predictor:
            self.orbit_prediction_points = []
            return

        sim_pos = self.position_vec.copy()
        sim_vel = self.velocity_vec.copy()
        
        predicted_path = []
        for _ in range(self.prediction_steps):
            sim_grav_accel = Vec2D(0, 0)
            for body in celestial_bodies_list:
                force = body.get_gravity_force_on(sim_pos, self.mass, G_constant)
                sim_grav_accel += force / self.mass # self.mass is ship's mass
            
            sim_vel += sim_grav_accel * self.prediction_delta_time
            sim_pos += sim_vel * self.prediction_delta_time
            predicted_path.append(sim_pos.copy())

        self.orbit_prediction_points = predicted_path

    def rotate(self, direction, delta_time):
        """
        Rotates the ship.

        Args:
            direction (int): -1 for left (counter-clockwise), 1 for right (clockwise).
            delta_time (float): Time elapsed since the last frame.
        """
        self.angle += direction * self.rotation_speed * delta_time
        self.angle %= 360  # Keep angle in 0-360 range

    def apply_ship_thrust(self):
        """
        Applies thrust force in the direction the ship is currently pointing.
        Sets `self.thruster_on` to True for drawing purposes.
        """
        rad = math.radians(self.angle)
        force_x = math.cos(rad) * self.thrust_strength
        force_y = math.sin(rad) * self.thrust_strength # Pygame y-axis is downwards
        
        force_vec = Vec2D(force_x, force_y)
        self.apply_force(force_vec) 
        self.thruster_on = True

    def draw(self, screen, camera_offset_x=0, camera_offset_y=0):
        """
        Draws the player ship as a triangle, its thruster flame if active,
        and its predicted orbit path.

        Args:
            screen (pygame.Surface): The Pygame surface to draw on.
            camera_offset_x (float, optional): X offset for camera view. Defaults to 0.
            camera_offset_y (float, optional): Y offset for camera view. Defaults to 0.
        """
        screen_pos_x = self.position_vec.x + camera_offset_x
        screen_pos_y = self.position_vec.y + camera_offset_y

        rad = math.radians(self.angle)
        
        # Nose point
        nose_len = self.radius + 5
        nose = (screen_pos_x + math.cos(rad) * nose_len, 
                screen_pos_y + math.sin(rad) * nose_len)
        
        # Rear points (forming the base of the triangle)
        # Angle for rear points is relative to the ship's angle
        rear_angle_offset = 140 # degrees
        
        rear_left_rad = math.radians(self.angle + rear_angle_offset)
        rear_left = (screen_pos_x + math.cos(rear_left_rad) * self.radius, 
                     screen_pos_y + math.sin(rear_left_rad) * self.radius)
        
        rear_right_rad = math.radians(self.angle - rear_angle_offset)
        rear_right = (screen_pos_x + math.cos(rear_right_rad) * self.radius, 
                      screen_pos_y + math.sin(rear_right_rad) * self.radius)
        
        pygame.draw.polygon(screen, self.color, [nose, rear_left, rear_right])

        if self.thruster_on:
            # Draw a small flame at the "center" of the rear
            # Calculate a point slightly behind the center of the ship
            flame_length = self.radius + 2 # How far back the flame center is
            flame_center_x = screen_pos_x - math.cos(rad) * flame_length 
            flame_center_y = screen_pos_y - math.sin(rad) * flame_length
            
            # Simple flame: a small yellow circle
            pygame.draw.circle(screen, (255, 255, 0), (int(flame_center_x), int(flame_center_y)), self.radius // 2)
            
        self.thruster_on = False # Reset for the next frame

        # Draw orbit prediction
        if self.show_orbit_predictor and len(self.orbit_prediction_points) > 1:
            path_tuples = [(int(p.x + camera_offset_x), int(p.y + camera_offset_y)) for p in self.orbit_prediction_points]
            pygame.draw.lines(screen, (100, 100, 100), False, path_tuples, 1)

class EnemyShip(PhysicsObject):
    def __init__(self, mass, position_vec, velocity_vec=None, color=(255, 0, 0), radius=10, health=100, target_for_missiles=None):
        super().__init__(mass, position_vec, velocity_vec, color=color, radius=radius)
        self.health = health
        # If target_for_missiles is not provided, it can default to self, 
        # so missiles fired AT this enemy can use its own position_vec.
        self.target_for_missiles = target_for_missiles if target_for_missiles is not None else self

    def take_damage(self, amount):
        """
        Applies damage to the enemy ship and checks if it's destroyed.

        Args:
            amount (float): The amount of damage to inflict.

        Returns:
            bool: True if the ship's health is depleted (destroyed), False otherwise.
        """
        self.health -= amount
        print(f"Enemy ({id(self)}) took {amount} damage, health is now {self.health}") # Debug
        return self.health <= 0

    def update_ai(self, delta_time, player_ship_obj, celestial_bodies_list, G_constant):
        """
        Updates the AI logic for the enemy ship.
        (Currently a placeholder - passive behavior).

        Args:
            delta_time (float): Time elapsed since the last frame.
            player_ship_obj (PlayerShip): The player ship object, for targeting or behavior.
            celestial_bodies_list (list): List of celestial bodies for context.
            G_constant (float): Gravitational constant.
        """
        # Passive behavior: only affected by gravity via PhysicsObject.update_physics()
        pass

    def draw(self, screen, camera_offset_x=0, camera_offset_y=0):
        """
        Draws the enemy ship.

        Args:
            screen (pygame.Surface): The Pygame surface to draw on.
            camera_offset_x (float, optional): X offset for camera view. Defaults to 0.
            camera_offset_y (float, optional): Y offset for camera view. Defaults to 0.
        """
        # Uses the parent's draw method (draws a circle).
        super().draw(screen, camera_offset_x, camera_offset_y)
        # TODO: Optionally, draw a health bar or a more distinct shape for enemies.


class HomingMissile(Projectile):
    """
    Represents a homing missile that tracks a target.
    Inherits from Projectile and adds guidance logic, fuel, and thrust.
    """
    def __init__(self, mass, position_vec, velocity_vec, target=None, color=(0, 255, 255), radius=4, lifespan=10.0, turn_rate_degrees_sec=90.0, thrust_force=50000.0, fuel=10.0):
        """
        Initializes a HomingMissile.

        Args:
            mass (float): Mass of the missile.
            position_vec (Vec2D): Initial position vector.
            velocity_vec (Vec2D): Initial velocity vector.
            target (PhysicsObject, optional): The object the missile will home towards. Defaults to None.
            color (tuple, optional): RGB color tuple. Defaults to (0, 255, 255) (Cyan).
            radius (int, optional): Radius in pixels. Defaults to 4.
            lifespan (float, optional): Max time in seconds before the missile self-destructs. Defaults to 10.0.
            turn_rate_degrees_sec (float, optional): Max turn rate in degrees per second. Defaults to 90.0.
            thrust_force (float, optional): Force applied by the missile's thruster. Defaults to 50000.0.
            fuel (float, optional): Amount of fuel in seconds of thrust. Defaults to 10.0.
        """
        super().__init__(mass, position_vec, velocity_vec, color=color, radius=radius, lifespan=lifespan)
        self.target = target
        self.turn_rate_rad_sec = math.radians(turn_rate_degrees_sec)
        self.thrust_force = thrust_force
        self.fuel = fuel
        self.current_thrust_on = False # For drawing thruster flame

    def update_guidance_and_thrust(self, delta_time):
        """
        Updates missile guidance towards the target and applies thrust if fuel is available.
        Modifies acceleration directly via `self.apply_force()`.

        Args:
            delta_time (float): Time elapsed since the last frame.
        """
        self.current_thrust_on = False
        if self.target is None or self.fuel <= 0:
            return # No guidance or thrust if no target or out of fuel

        # Check if target is "destroyed" (e.g., an EnemyShip with no health)
        # This requires target to have a 'health' attribute if it's damageable.
        # A more generic solution would be an 'is_active' or 'is_destroyed' flag in PhysicsObject.
        if hasattr(self.target, 'health') and self.target.health <= 0:
            self.target = None # Stop targeting a dead enemy
            # Missile continues straight without thrust as per requirement
            return 
        
        self.fuel -= delta_time # Consume fuel
        if self.fuel <=0: # Check again after consumption
            self.fuel = 0
            return 
        self.current_thrust_on = True

        # --- Guidance Logic ---
        direction_to_target = (self.target.position_vec - self.position_vec).normalize()
        
        # Use missile's current velocity vector for its orientation.
        # If velocity is near zero, it might not accurately reflect orientation.
        # A more robust solution might involve storing an explicit orientation angle for the missile.
        if self.velocity_vec.magnitude() < 1e-6: # If velocity is practically zero
             # If missile is not moving, attempt to thrust directly towards the target.
             # This can be problematic if the missile is at the target's exact location.
             if self.position_vec.distance_to(self.target.position_vec) < 1e-3: # Practically at target
                 self.current_thrust_on = False # Stop thrust if on top of target
                 return
             current_direction = direction_to_target 
        else:
            current_direction = self.velocity_vec.normalize()

        # Calculate desired angle and current angle
        desired_angle_rad = math.atan2(direction_to_target.y, direction_to_target.x)
        current_angle_rad = math.atan2(current_direction.y, current_direction.x)

        # Determine the shortest angle to turn
        angle_diff = desired_angle_rad - current_angle_rad
        # Normalize angle_diff to be between -pi and pi
        while angle_diff > math.pi: angle_diff -= 2 * math.pi
        while angle_diff < -math.pi: angle_diff += 2 * math.pi

        # Limit turn rate
        max_turn_this_frame = self.turn_rate_rad_sec * delta_time
        turn_amount_rad = max(min(angle_diff, max_turn_this_frame), -max_turn_this_frame)
        
        # New direction after turning
        new_angle_rad = current_angle_rad + turn_amount_rad
        new_direction = Vec2D(math.cos(new_angle_rad), math.sin(new_angle_rad))

        # Apply thrust in the new direction
        thrust_vec = new_direction * self.thrust_force
        self.apply_force(thrust_vec)

    def draw(self, screen, camera_offset_x=0, camera_offset_y=0):
        """
        Draws the homing missile and its thruster flame if active.

        Args:
            screen (pygame.Surface): The Pygame surface to draw on.
            camera_offset_x (float, optional): X offset for camera view. Defaults to 0.
            camera_offset_y (float, optional): Y offset for camera view. Defaults to 0.
        """
        super().draw(screen, camera_offset_x, camera_offset_y) # Draw missile body (circle)
        if self.current_thrust_on:
            # Draw flame opposite to the missile's current direction of travel (velocity)
            if self.velocity_vec.magnitude() > 1e-6: # Only draw if moving
                flame_direction = self.velocity_vec.normalize() * -1
                flame_length = self.radius + 2 # Position flame slightly behind missile
                flame_pos = self.position_vec + flame_direction * flame_length
                
                screen_flame_pos_x = int(flame_pos.x + camera_offset_x)
                screen_flame_pos_y = int(flame_pos.y + camera_offset_y)
                
                flame_radius = self.radius // 2 + 1
                pygame.draw.circle(screen, (255,165,0), (screen_flame_pos_x, screen_flame_pos_y), flame_radius) # Orange flame
        return normalized_direction_vec * force_magnitude
