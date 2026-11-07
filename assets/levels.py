# ==========================================
# LEVEL & MAP CONFIGURATIONS
# ==========================================
LEVELS = {
    1: {
        "name": "Level 1: The Stone Keep",
        "texture_id": 1,
        "map": [
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 1, 1, 0, 1, 1, 0, 1, 1, 0, 1],
            [1, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 1],
            [1, 0, 1, 0, 1, 0, 1, 0, 1, 1, 0, 1],
            [1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1],
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        ],
        "opponents": [
            {
                "name": "Goblin Ghost",
                "x": 3.0,
                "y": 1.5,
                "hp": 25,
                "max_hp": 25,
                "min_atk": 2,
                "max_atk": 5,
                "alive": True,
            },
            {
                "name": "Goblin Ghost",
                "x": 9.5,
                "y": 1.5,
                "hp": 25,
                "max_hp": 25,
                "min_atk": 2,
                "max_atk": 5,
                "alive": True,
            },
        ],
    },
    2: {
        "name": "Level 2: The Deep Cavern",
        "texture_id": 2,
        "map": [
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            [1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1],
            [1, 0, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1],
            [1, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 1],
            [1, 0, 1, 1, 1, 1, 0, 1, 1, 1, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        ],
        "opponents": [
            {
                "name": "Goblin Ghost",
                "x": 6.5,
                "y": 3.5,
                "hp": 25,
                "max_hp": 25,
                "min_atk": 2,
                "max_atk": 5,
                "alive": True,
            }
        ],
    },
    3: {
        "name": "Level 3: The Sunlit Clearing",
        "texture_id": 2,  # organic rock walls (existing wall set)
        "floor_texture_id": 1,  # grass fills walkable (0) cells
        "sky": True,  # gradient sky instead of ceiling color
        "map": [
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 2, 2, 2, 0, 0, 0, 0, 1],
            [1, 0, 0, 2, 2, 2, 2, 2, 0, 0, 0, 1],
            [1, 0, 0, 0, 2, 2, 2, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        ],
        "opponents": [
            {
                "name": "Goblin Ghost",
                "x": 9.5,
                "y": 4.5,
                "hp": 25,
                "max_hp": 25,
                "min_atk": 2,
                "max_atk": 5,
                "alive": True,
            }
        ],
    },
}
