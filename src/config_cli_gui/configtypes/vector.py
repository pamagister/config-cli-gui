class Vector:
    """Class that represents a vector or point in 2D or 3D"""

    def __init__(self, x: int | float = 0, y: int | float = 0, z: int | float | None = None):
        self.x = x
        self.y = y
        self.z = z

    def to_list(self) -> list[int | float]:
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
        return cls.from_list([c for c in coordinate.strip().strip("()[]").split(",") if c.strip()])

    def to_str(self) -> str:
        return f"({self.x}, {self.y}, {self.z})" if self.z is not None else f"({self.x}, {self.y})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Vector):
            return NotImplemented
        return self.to_list() == other.to_list()

    def __hash__(self) -> int:
        return hash(tuple(self.to_list()))

    def __str__(self):
        return self.to_str()

    def __repr__(self):
        return f"Vector{str(self)}"
