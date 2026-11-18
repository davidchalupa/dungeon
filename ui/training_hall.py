import pygame
from ui.common import VIRTUAL_WIDTH, VIRTUAL_HEIGHT, get_fonts, get_virtual_mouse_pos_from_raw

_prev_mouse_pressed = False
train_btn_rect = pygame.Rect(0, 0, 0, 0)
hero_card_rects = []

def get_next_level_exp(level):
    return level * (level + 1) * 500

def handle_training_hall_key(event, party_members, selected_hero_index, player_gold):
    """
    Handles keyboard shortcuts while the training hall is open.
    Returns (close_hall: bool, updated_gold: int, updated_hero_index: int, status_msg: str | None)
    """
    if event.key == pygame.K_ESCAPE:
        return True, player_gold, selected_hero_index, "Left the Training Hall."
    elif event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4):
        idx = event.key - pygame.K_1
        if idx < len(party_members):
            return False, player_gold, idx, f"Selected {party_members[idx]['name']} for training."
    elif event.key == pygame.K_t:
        hero = party_members[selected_hero_index]
        target_level = hero["level"] + 1
        cost = 10 * target_level
        req_exp = get_next_level_exp(hero["level"])

        if hero["exp"] >= req_exp:
            if player_gold >= cost:
                player_gold -= cost
                hero["level"] += 1
                hero["max_hp"] = hero["level"] * hero["hp_per_level"]
                hero["max_mp"] = hero["level"] * hero["mp_per_level"]
                return False, player_gold, selected_hero_index, f"{hero['name']} trained to Level {hero['level']}!"
            else:
                return False, player_gold, selected_hero_index, f"Not enough gold! Need {cost}g (have {player_gold}g)."
        else:
            return False, player_gold, selected_hero_index, f"Not enough XP! Need {req_exp} XP (have {hero['exp']} XP)."

    return False, player_gold, selected_hero_index, None

def draw_training_hall_dialog(surface, party_members, selected_hero_index, player_gold):
    """
    Draws the Training Hall interface above the party HUD bar.
    Returns (updated_gold, updated_hero_index, status_message_or_None).
    """
    global _prev_mouse_pressed, train_btn_rect, hero_card_rects

    font_med, font_large, font_title = get_fonts()
    status_msg = None

    # Semi-transparent backdrop covering only the upper 3D viewport (leaves bottom party bar clickable & bright)
    overlay = pygame.Surface((VIRTUAL_WIDTH, 546), pygame.SRCALPHA)
    overlay.fill((10, 15, 25, 225))
    surface.blit(overlay, (0, 0))

    # Compact panel height so it doesn't overlap the party portraits at y >= 550
    panel_rect = pygame.Rect(60, 40, VIRTUAL_WIDTH - 120, 495)
    pygame.draw.rect(surface, (20, 25, 35), panel_rect)
    pygame.draw.rect(surface, (100, 180, 255), panel_rect, 3)

    # Title & Gold Header
    title_surf = font_title.render("TRAINING HALL", True, (150, 220, 255))
    surface.blit(title_surf, (panel_rect.x + 25, panel_rect.y + 18))

    gold_surf = font_large.render(f"Party Gold: {player_gold}g", True, (255, 215, 0))
    surface.blit(gold_surf, (panel_rect.right - gold_surf.get_width() - 25, panel_rect.y + 18))
    pygame.draw.line(surface, (70, 90, 120), (panel_rect.x + 25, panel_rect.y + 56), (panel_rect.right - 25, panel_rect.y + 56), 1)

    # Left side: Party Members Cards
    hero_card_rects = []
    list_y = panel_rect.y + 70
    card_w, card_h = 300, 76

    for i, hero in enumerate(party_members):
        card_rect = pygame.Rect(panel_rect.x + 25, list_y + i * (card_h + 10), card_w, card_h)
        hero_card_rects.append((card_rect, i))

        is_selected = (i == selected_hero_index)
        border_color = (100, 220, 140) if is_selected else (60, 80, 110)
        bg_color = (30, 45, 40) if is_selected else (25, 30, 42)

        pygame.draw.rect(surface, bg_color, card_rect)
        pygame.draw.rect(surface, border_color, card_rect, 2)

        name_color = (255, 255, 255) if hero["hp"] > 0 else (150, 150, 150)
        name_surf = font_large.render(f"{i+1}. {hero['name']} ({hero['class']})", True, name_color)
        lvl_surf = font_med.render(f"Level {hero['level']} | HP: {hero['hp']}/{hero['max_hp']}", True, (200, 200, 220))

        surface.blit(name_surf, (card_rect.x + 12, card_rect.y + 10))
        surface.blit(lvl_surf, (card_rect.x + 12, card_rect.y + 42))

    # Right side: Selected Hero Details & Training Action
    selected_hero = party_members[selected_hero_index]
    details_rect = pygame.Rect(panel_rect.x + 345, panel_rect.y + 70, panel_rect.width - 370, 334)

    pygame.draw.rect(surface, (28, 35, 50), details_rect)
    pygame.draw.rect(surface, (80, 120, 160), details_rect, 2)

    det_title = font_large.render(f"Training: {selected_hero['name']}", True, (220, 240, 255))
    surface.blit(det_title, (details_rect.x + 20, details_rect.y + 18))

    target_level = selected_hero["level"] + 1
    cost = 10 * target_level
    req_exp = get_next_level_exp(selected_hero["level"])
    current_exp = selected_hero.get("exp", 0)

    info_lines = [
        f"Current Level: {selected_hero['level']}  ->  Next Level: {target_level}",
        f"Current XP: {current_exp} / Required XP: {req_exp}",
        f"Training Cost: {cost} Gold (Available: {player_gold}g)",
        f"Stat Boosts on Training:",
        f"  • Max HP: +{selected_hero['hp_per_level']}",
        f"  • Max MP: +{selected_hero['mp_per_level']}",
    ]

    ly = details_rect.y + 60
    for line in info_lines:
        txt_surf = font_med.render(line, True, (220, 220, 230))
        surface.blit(txt_surf, (details_rect.x + 20, ly))
        ly += 27

    # Train Button
    train_btn_rect = pygame.Rect(details_rect.centerx - 120, details_rect.bottom - 56, 240, 40)
    can_train = current_exp >= req_exp and player_gold >= cost
    btn_bg = (40, 130, 70) if can_train else (60, 60, 70)
    btn_border = (100, 250, 140) if can_train else (100, 100, 100)

    window_size = pygame.display.get_surface().get_size()
    mouse_pos = get_virtual_mouse_pos_from_raw(pygame.mouse.get_pos(), window_size)
    mouse_buttons = pygame.mouse.get_pressed()
    left_clicked = mouse_buttons[0] and not _prev_mouse_pressed

    if train_btn_rect.collidepoint(mouse_pos) and can_train:
        btn_bg = (50, 160, 85)

    pygame.draw.rect(surface, btn_bg, train_btn_rect)
    pygame.draw.rect(surface, btn_border, train_btn_rect, 2)

    btn_txt = font_large.render("TRAIN LEVEL UP", True, (255, 255, 255) if can_train else (170, 170, 170))
    surface.blit(btn_txt, btn_txt.get_rect(center=train_btn_rect.center))

    # Footer instructions
    footer_surf = font_med.render("Click portrait or card [1-4] to switch | Press [T] or click [TRAIN] | [ESC] Close", True, (170, 170, 170))
    surface.blit(footer_surf, footer_surf.get_rect(center=(panel_rect.centerx, panel_rect.bottom - 20)))

    # Mouse Click Handling (Card selection & Train button)
    if left_clicked:
        for c_rect, idx in hero_card_rects:
            if c_rect.collidepoint(mouse_pos):
                selected_hero_index = idx
                status_msg = f"Selected {party_members[idx]['name']}."
                break

        if train_btn_rect.collidepoint(mouse_pos) and can_train:
            player_gold -= cost
            selected_hero["level"] += 1
            selected_hero["max_hp"] = selected_hero["level"] * selected_hero["hp_per_level"]
            selected_hero["max_mp"] = selected_hero["level"] * selected_hero["mp_per_level"]
            status_msg = f"{selected_hero['name']} successfully trained to Level {selected_hero['level']}!"

    _prev_mouse_pressed = mouse_buttons[0]
    return player_gold, selected_hero_index, status_msg
