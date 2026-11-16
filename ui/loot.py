import pygame
from assets.items import get_item_icon
from assets.party_members import get_class_abbrev_str
from ui.common import VIRTUAL_WIDTH, VIRTUAL_HEIGHT, get_fonts, get_virtual_mouse_pos_from_raw

_loot_dragged_item = None
_loot_drag_source = None  # ("loot", idx) or ("inventory", hero, slot_idx)
_prev_mouse_pressed = False

loot_panel_rect = pygame.Rect(40, 60, 360, 460)
player_panel_rect = pygame.Rect(440, 60, 360, 460)
loot_grid_rects = []
player_inv_rects = []
hero_tab_rects = []


def handle_loot_key(event, party_members, selected_hero_index, loot_items):
    """
    Handles keyboard input while the loot dialog is open.
    Returns (close_loot: bool, updated_hero_idx: int, status_msg: str | None)
    """
    global _loot_dragged_item, _loot_drag_source

    # Switch active character with keys 1-4
    key_map = {pygame.K_1: 0, pygame.K_2: 1, pygame.K_3: 2, pygame.K_4: 3}
    if event.key in key_map:
        idx = key_map[event.key]
        if idx < len(party_members):
            return False, idx, None

    if event.key in (pygame.K_ESCAPE, pygame.K_SPACE):
        # Return any mid-drag item before closing
        if _loot_dragged_item is not None and _loot_drag_source is not None:
            _return_loot_item(loot_items, _loot_dragged_item, _loot_drag_source)
            _loot_dragged_item = None
            _loot_drag_source = None
        return True, selected_hero_index, "Finished looting."

    return False, selected_hero_index, None


def draw_loot_dialog(surface, party_members, selected_hero_index, loot_items, enemy_name="Enemy"):
    """
    Renders the post-combat loot screen with drag-and-drop into party inventories
    and character switching tabs.
    Returns (updated_hero_idx: int, status_msg: str | None)
    """
    global _loot_dragged_item, _loot_drag_source, _prev_mouse_pressed
    global loot_grid_rects, player_inv_rects, hero_tab_rects

    font_med, font_large, _ = get_fonts()
    status_msg = None
    hero = party_members[selected_hero_index]

    # Semi-transparent backdrop
    overlay = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT), pygame.SRCALPHA)
    overlay.fill((10, 10, 15, 230))
    surface.blit(overlay, (0, 0))

    # --- LEFT PANEL: ENEMY SPOILS ---
    pygame.draw.rect(surface, (25, 25, 35), loot_panel_rect)
    pygame.draw.rect(surface, (180, 140, 70), loot_panel_rect, 3)

    title_loot = font_large.render(f"{enemy_name} Spoils", True, (240, 200, 100))
    surface.blit(title_loot, (loot_panel_rect.x + 20, loot_panel_rect.y + 15))
    pygame.draw.line(
        surface, (90, 80, 60),
        (loot_panel_rect.x + 20, loot_panel_rect.y + 45),
        (loot_panel_rect.right - 20, loot_panel_rect.y + 45), 1,
    )

    loot_grid_rects = []
    slot_size = 44
    cols = 5
    start_x = loot_panel_rect.x + 25
    start_y = loot_panel_rect.y + 65

    if not loot_items and _loot_dragged_item is None:
        empty_loot_surf = font_med.render("All items collected!", True, (140, 200, 140))
        surface.blit(empty_loot_surf, (start_x, start_y))

    for idx, item in enumerate(loot_items):
        r = idx // cols
        c = idx % cols
        cell_x = start_x + c * (slot_size + 10)
        cell_y = start_y + r * (slot_size + 10)
        cell_rect = pygame.Rect(cell_x, cell_y, slot_size, slot_size)
        loot_grid_rects.append((cell_rect, idx))

        pygame.draw.rect(surface, (35, 35, 48), cell_rect)
        pygame.draw.rect(surface, (140, 115, 70), cell_rect, 2)

        icon = get_item_icon(item)
        surface.blit(icon, icon.get_rect(center=cell_rect.center))

    # --- RIGHT PANEL: CHARACTER SWITCHER & INVENTORY ---
    pygame.draw.rect(surface, (25, 25, 35), player_panel_rect)
    pygame.draw.rect(surface, (140, 140, 160), player_panel_rect, 3)

    # Character Switcher Tabs
    hero_tab_rects = []
    tab_count = len(party_members)
    tab_gap = 6
    total_tab_w = player_panel_rect.width - 40
    tab_w = (total_tab_w - tab_gap * (tab_count - 1)) // tab_count
    tab_h = 28
    tab_y = player_panel_rect.y + 12

    for idx, member in enumerate(party_members):
        tx = player_panel_rect.x + 20 + idx * (tab_w + tab_gap)
        t_rect = pygame.Rect(tx, tab_y, tab_w, tab_h)
        hero_tab_rects.append((t_rect, idx))

        is_selected = idx == selected_hero_index
        bg_col = (55, 70, 105) if is_selected else (32, 32, 44)
        border_col = (140, 195, 255) if is_selected else (80, 80, 100)
        pygame.draw.rect(surface, bg_col, t_rect)
        pygame.draw.rect(surface, border_col, t_rect, 2 if is_selected else 1)

        short_name = member["name"][:7]
        lbl = font_med.render(f"[{idx + 1}] {short_name}", True, (245, 245, 255) if is_selected else (170, 170, 185))
        surface.blit(lbl, lbl.get_rect(center=t_rect.center))

    # Active Hero Header
    title_player = font_large.render(f"{hero['name']} ({hero['class']})", True, (220, 220, 240))
    surface.blit(title_player, (player_panel_rect.x + 20, player_panel_rect.y + 48))
    pygame.draw.line(
        surface, (70, 70, 90),
        (player_panel_rect.x + 20, player_panel_rect.y + 76),
        (player_panel_rect.right - 20, player_panel_rect.y + 76), 1,
    )

    # Player Inventory Slots (10 slots)
    player_inv_rects = []
    inv_start_x = player_panel_rect.x + 20
    inv_start_y = player_panel_rect.y + 88
    inv_slot_w = 320
    inv_slot_h = 32
    inv_slot_spacing = 4

    for i in range(10):
        sy = inv_start_y + i * (inv_slot_h + inv_slot_spacing)
        s_rect = pygame.Rect(inv_start_x, sy, inv_slot_w, inv_slot_h)
        player_inv_rects.append(s_rect)

        pygame.draw.rect(surface, (30, 30, 40), s_rect)
        pygame.draw.rect(surface, (80, 80, 100), s_rect, 1)

        item = hero["inventory"][i]
        if item is not None:
            icon_box = pygame.Rect(s_rect.x + 3, s_rect.y + 3, 26, 26)
            pygame.draw.rect(surface, (45, 45, 60), icon_box)
            i_icon = get_item_icon(item)
            surface.blit(pygame.transform.scale(i_icon, (26, 26)), icon_box)

            name_surf = font_med.render(item.get("name", "Item"), True, (240, 240, 240))
            surface.blit(name_surf, (s_rect.x + 36, s_rect.y + 8))
        else:
            empty_surf = font_med.render(f"Empty Slot {i + 1}", True, (90, 90, 105))
            surface.blit(empty_surf, (s_rect.x + 12, s_rect.y + 8))

    footer_txt = font_med.render(
        "Drag item to inventory | [1-4] or Click Tab to Switch Hero | [ESC / SPACE] Done",
        True, (170, 170, 170)
    )
    surface.blit(footer_txt, footer_txt.get_rect(center=(VIRTUAL_WIDTH // 2, 545)))

    # ==========================================
    # MOUSE INPUT HANDLING
    # ==========================================
    window_size = pygame.display.get_surface().get_size()
    mouse_pos = get_virtual_mouse_pos_from_raw(pygame.mouse.get_pos(), window_size)
    mouse_buttons = pygame.mouse.get_pressed()
    left_clicked = mouse_buttons[0] and not _prev_mouse_pressed
    left_released = not mouse_buttons[0] and _prev_mouse_pressed

    # 1. Pick Up Item or Click Character Tab
    if left_clicked:
        # Check character switcher tabs first
        for tab_rect, idx in hero_tab_rects:
            if tab_rect.collidepoint(mouse_pos):
                selected_hero_index = idx
                hero = party_members[selected_hero_index]
                break

        # Pick up from loot panel
        if loot_panel_rect.collidepoint(mouse_pos):
            for rect, idx in loot_grid_rects:
                if rect.collidepoint(mouse_pos):
                    _loot_dragged_item = loot_items.pop(idx)
                    _loot_drag_source = ("loot", idx)
                    break
        # Pick up from active hero's inventory (allows rearranging or moving back to loot pile)
        else:
            for i, rect in enumerate(player_inv_rects):
                if rect.collidepoint(mouse_pos) and hero["inventory"][i] is not None:
                    _loot_dragged_item = hero["inventory"][i]
                    _loot_drag_source = ("inventory", hero, i)
                    hero["inventory"][i] = None
                    break

    # 2. Drop Item
    elif left_released and _loot_dragged_item is not None:
        handled = False

        # Dropped onto Player Inventory Panel
        if player_panel_rect.collidepoint(mouse_pos):
            target_slot = None
            for i, rect in enumerate(player_inv_rects):
                if rect.collidepoint(mouse_pos):
                    target_slot = i
                    break

            # If dropped in panel generally (not on a specific slot), use first empty slot
            if target_slot is None:
                for i in range(10):
                    if hero["inventory"][i] is None:
                        target_slot = i
                        break

            if target_slot is not None:
                old_item = hero["inventory"][target_slot]
                hero["inventory"][target_slot] = _loot_dragged_item
                if old_item is not None:
                    _return_loot_item(loot_items, old_item, _loot_drag_source)
                if _loot_drag_source[0] == "loot":
                    status_msg = f"{hero['name']} took {_loot_dragged_item['name']}!"
                handled = True
            else:
                status_msg = f"{hero['name']}'s inventory is full!"

        # Dropped back onto Loot Panel
        elif loot_panel_rect.collidepoint(mouse_pos):
            loot_items.append(_loot_dragged_item)
            handled = True

        if not handled:
            _return_loot_item(loot_items, _loot_dragged_item, _loot_drag_source)

        _loot_dragged_item = None
        _loot_drag_source = None

    _prev_mouse_pressed = mouse_buttons[0]

    # Hover Tooltip on Loot Items
    hovered_item = None
    if _loot_dragged_item is None:
        for rect, idx in loot_grid_rects:
            if rect.collidepoint(mouse_pos) and idx < len(loot_items):
                hovered_item = loot_items[idx]
                break

    if hovered_item and _loot_dragged_item is None:
        tip_title = font_med.render(hovered_item["name"], True, (255, 255, 150))
        allowed_str = get_class_abbrev_str(hovered_item.get("allowed_classes", []))
        tip_cls = font_med.render(f"Classes: {allowed_str}", True, (150, 200, 255))

        stat_line = ""
        if "min_atk" in hovered_item:
            stat_line = f"ATK: {hovered_item['min_atk']}-{hovered_item['max_atk']}"
        elif "min_def" in hovered_item:
            stat_line = f"DEF: {hovered_item['min_def']}-{hovered_item['max_def']}"
        tip_stat = font_med.render(stat_line, True, (200, 235, 200)) if stat_line else None

        box_h = 64 if tip_stat else 46
        max_w = max(tip_title.get_width(), tip_cls.get_width(), tip_stat.get_width() if tip_stat else 0)
        tip_rect = pygame.Rect(mouse_pos[0] + 12, mouse_pos[1] - 40, max_w + 16, box_h)

        pygame.draw.rect(surface, (15, 15, 25), tip_rect)
        pygame.draw.rect(surface, (200, 180, 100), tip_rect, 1)
        surface.blit(tip_title, (tip_rect.x + 8, tip_rect.y + 4))
        surface.blit(tip_cls, (tip_rect.x + 8, tip_rect.y + 22))
        if tip_stat:
            surface.blit(tip_stat, (tip_rect.x + 8, tip_rect.y + 40))

    # Draw dragged icon at cursor
    if _loot_dragged_item is not None:
        surface.blit(get_item_icon(_loot_dragged_item), (mouse_pos[0] - 16, mouse_pos[1] - 16))

    return selected_hero_index, status_msg


def _return_loot_item(loot_items, item, source):
    if source is None:
        loot_items.append(item)
        return
    stype = source[0]
    if stype == "loot":
        loot_items.append(item)
    elif stype == "inventory":
        _, hero, idx = source
        if hero["inventory"][idx] is None:
            hero["inventory"][idx] = item
        else:
            for i in range(10):
                if hero["inventory"][i] is None:
                    hero["inventory"][i] = item
                    return
            loot_items.append(item)
