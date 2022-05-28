import dataclasses
import math


@dataclasses.dataclass
class Position2D:
    """
    A position in 2D space
    """

    x: float  # pylint: disable=invalid-name
    y: float  # pylint: disable=invalid-name


    def __hash__(self):
        return hash((self.x, self.y))

    def __sub__(self, other: "Position2D") -> "Position2D":
        """
        Subtracts the other vector from this one and returns the result
        :param other: The other position
        :return: A new vector of z where z = this-other
        >>> Position2D(x=10, y=5) - Position2D(x=3, y=2)
        Position2D(x=7, y=3)
        """
        return Position2D(x=self.x - other.x, y=self.y - other.y)

    def __add__(self, other: "Position2D") -> "Position2D":
        """
        Adds this vector to the other vector
        :param other: The other vector to add to
        :return: A new vector of the two combined
        """
        return Position2D(x=self.x + other.x, y=self.y + other.y)

    def __mul__(self, other: float) -> "Position2D":
        return Position2D(x=self.x * other, y=self.y * other)

    def __truediv__(self, other: float) -> "Position2D":
        """
        Gets this vector divided by a scalar value
        :param other: The scalar value to divide by
        :return: A new vector.
        """
        return Position2D(x=self.x / other, y=self.y / other)

    def dot_product(self, other: "Position2D") -> float:
        """
        Gets the dot product of this vector to the other vector
        :param other: The other vector
        :return: The dot product of the two vectors
        """
        return self.x * other.x + self.y * other.y

    def cross_product_scalar(self, other: "Position2D") -> float:
        """

        :param other:
        :return:
        >>> Position2D(x=5, y=0).cross_product_scalar(Position2D(x=0, y=4))
        1.0
        >>> Position2D(x=0, y=3).cross_product_scalar(Position2D(x=4, y=0))
        -1.0
        """
        return (self.x * other.y - self.y * other.x) / (
            self.magnitude() * other.magnitude()
        )

    def magnitude(self) -> float:
        """
        Gets the magnitude of this vector
        :return: The magnitude of this vector
        """
        return math.sqrt(self.x ** 2 + self.y ** 2)

    def unit(self) -> "Position2D":
        return self / self.magnitude()

    def angle_between(self, other: "Position2D") -> float:
        """
        Gets the angle between this vector and the other vector
        :param other: The other vector to get the angle between
        :return:
        >>> Position2D(x=0.5, y=0.5).angle_between(Position2D(x=0, y=1))
        0.7853981633974484
        """
        total_magnitude = self.magnitude() * other.magnitude()
        if total_magnitude == 0:
            return 0
        try:
            return math.acos(self.dot_product(other) / total_magnitude)
        except ValueError:
            return 0
