class Vector:
    """Class that represents a vector or point in 2D or 3D"""

    def __init__(self, x: int | float, y: int | float, z: int | float | None = None):
        self.x = x
        self.y = y
        self.z = z

    def to_list(self) -> list[int]:
        return [self.x, self.y, self.z] if self.z is not None else [self.x, self.y]

    @classmethod
    def from_list(cls, coordinate: list[int | str | float]) -> "Vector":
        if len(coordinate) == 2:
            return cls(float(coordinate[0]), float(coordinate[1]))
        if len(coordinate) >= 3:
            return cls(float(coordinate[0]), float(coordinate[1]), float(coordinate[2]))
        return cls()

    @classmethod
    def from_str(cls, coordinate: str) -> "Vector":
        return cls.from_list(coordinate.strip("()[]").split(","))

    def to_str(self) -> str:
        return f"({self.x}, {self.y}, {self.z})" if self.z is not None else f"({self.x}, {self.y})"  # type: ignore

    def __str__(self):
        return self.to_str()

    def __repr__(self):
        return f"Vector{str(self)}"
