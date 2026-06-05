from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class Vec3:
    x: float
    y: float
    z: float

    def __add__(self, other: Vec3) -> Vec3:
        return Vec3(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other: Vec3) -> Vec3:
        return Vec3(self.x - other.x, self.y - other.y, self.z - other.z)

    def scale(self, factor: float) -> Vec3:
        return Vec3(self.x * factor, self.y * factor, self.z * factor)

    def dot(self, other: Vec3) -> float:
        return self.x * other.x + self.y * other.y + self.z * other.z

    def cross(self, other: Vec3) -> Vec3:
        return Vec3(
            self.y * other.z - self.z * other.y,
            self.z * other.x - self.x * other.z,
            self.x * other.y - self.y * other.x,
        )

    def length(self) -> float:
        return math.sqrt(self.dot(self))

    def normalized(self) -> Vec3:
        length = self.length()
        if length == 0:
            raise ValueError("No se puede normalizar un vector nulo.")
        return self.scale(1 / length)

    def as_tuple(self) -> tuple[float, float, float]:
        return (self.x, self.y, self.z)
