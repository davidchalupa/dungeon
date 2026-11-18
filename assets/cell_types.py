"""Cell type definitions for dungeon map tiles."""


class CellType(int):
    """Enum-like class representing dungeon cell types with numeric values."""

    EMPTY = 0  # Walkable floor/grass/water surface
    BRICK_WALL = 1  # Standard brick wall (town)
    STONE_WALL = 3  # Stone wall (caverns/keep)
    SHOP_WALL = 6  # Shop exterior wall

    WATER = 2  # Water - pass-through for raycasting, walkable in some contexts

    SHOP_DOOR = 4  # Shop door/front entrance
    TOWN_DOOR = 7  # Town building door
    TOWN_GATE = 8  # Large town gate structure


# Helper constants for common checks
WALL_TYPES = {CellType.BRICK_WALL, CellType.STONE_WALL, CellType.SHOP_WALL}
DOOR_TYPES = {CellType.SHOP_DOOR, CellType.TOWN_DOOR, CellType.TOWN_GATE}
SOLID_WALLS = WALL_TYPES | DOOR_TYPES  # Alias for consistency with existing code


def int_to_cell_type(value: int) -> CellType:
    """Convert a raw integer to its corresponding CellType enum."""
    return CellType(value) if isinstance(value, (int, CellType)) else None


def is_wall(cell_type: int) -> bool:
    """Check if a cell type represents a solid wall."""
    ct = int_to_cell_type(cell_type)
    return ct in SOLID_WALLS if ct else False


def is_water(cell_type: int) -> bool:
    """Check if a cell type represents water."""
    ct = int_to_cell_type(cell_type)
    return ct == CellType.WATER if ct else False

# Mapping for reverse lookup (value -> name)
CELL_TYPE_NAMES = {k.lower(): v for k, v in vars(CellType).items()
                   if not callable(v) and isinstance(v, int)}
