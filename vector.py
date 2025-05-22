"""
vector.py

Provides a 2D vector class `Vec2D` for physics calculations and positioning.
Supports basic vector operations such as addition, subtraction, scalar multiplication,
division, magnitude, normalization, dot product, copying, and distance calculation.
"""
import math

class Vec2D:
    """
    A 2-dimensional vector class with support for common vector operations.
    Used for representing positions, velocities, and forces in the game.
    """
    def __init__(self, x, y):
        """
        Initializes a Vec2D object.

        Args:
            x (float or int): The x-component of the vector.
            y (float or int): The y-component of the vector.
        """
        self.x = x
        self.y = y

    def __add__(self, other):
        """
        Adds another Vec2D to this vector.

        Args:
            other (Vec2D): The other vector to add.

        Returns:
            Vec2D: A new Vec2D object representing the sum.
        """
        return Vec2D(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        """
        Subtracts another Vec2D from this vector.

        Args:
            other (Vec2D): The other vector to subtract.

        Returns:
            Vec2D: A new Vec2D object representing the difference.
        """
        return Vec2D(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar):
        """
        Multiplies this vector by a scalar.

        Args:
            scalar (float or int): The scalar value to multiply by.

        Returns:
            Vec2D: A new Vec2D object representing the scaled vector.
        """
        return Vec2D(self.x * scalar, self.y * scalar)

    def __truediv__(self, scalar):
        """
        Divides this vector by a scalar.

        Args:
            scalar (float or int): The scalar value to divide by.

        Returns:
            Vec2D: A new Vec2D object representing the divided vector.
        
        Raises:
            ValueError: If scalar is zero.
        """
        if scalar == 0:
            raise ValueError("Cannot divide by zero")
        return Vec2D(self.x / scalar, self.y / scalar)

    def magnitude(self):
        """
        Calculates the magnitude (length) of the vector.

        Returns:
            float: The magnitude of the vector.
        """
        return math.sqrt(self.x**2 + self.y**2)

    def normalize(self):
        """
        Normalizes the vector (scales it to a magnitude of 1).
        If the magnitude is zero, returns a zero vector.

        Returns:
            Vec2D: A new Vec2D object representing the normalized vector.
        """
        mag = self.magnitude()
        if mag == 0:
            return Vec2D(0, 0) 
        return Vec2D(self.x / mag, self.y / mag)

    def dot(self, other):
        """
        Calculates the dot product of this vector with another Vec2D.

        Args:
            other (Vec2D): The other vector.

        Returns:
            float: The dot product of the two vectors.
        """
        return self.x * other.x + self.y * other.y

    def __str__(self):
        """
        Returns a string representation of the vector.

        Returns:
            str: The string representation (e.g., "Vec2D(10.0, 20.5)").
        """
        return f"Vec2D({self.x}, {self.y})"

    def copy(self):
        """
        Creates a copy of this vector.

        Returns:
            Vec2D: A new Vec2D object with the same x and y components.
        """
        return Vec2D(self.x, self.y)

    def distance_to(self, other_vec):
        """
        Calculates the distance between this vector and another Vec2D.

        Args:
            other_vec (Vec2D): The other vector.

        Returns:
            float: The Euclidean distance between the two vectors.
        """
        return (self - other_vec).magnitude()
# Removed the duplicate distance_to method
