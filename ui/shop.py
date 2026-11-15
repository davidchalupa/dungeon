import pygame
from assets.items import ITEMS, get_item, get_item_icon
from assets.party_members import get_class_abbrev_str
from ui.common import VIRTUAL_WIDTH, VIRTUAL_HEIGHT, get_fonts, get_virtual_mouse_pos_from_raw

# Drag-and-drop trackers for shop interactions
_shop_dragged_item = None
_shop_drag_source = None  # ("shop", item_id) or ("inventory", hero, slot_idx) or ("weapon", hero) or ("armor", hero)
_prev_mouse_pressed = False

# Unified pending transaction state:
# None or {"type": "buy"|"sell", "hero": hero, "item": item, "source": source, "target_slot": int|None, "price": int}
_pending_transaction = None

# Layout rects
shop_panel_rect = pygame.Rect(40, 60, 360, 460)
player_panel_rect = pygame.Rect(440, 60, 360, 460)
shop_grid_rects = []
player_inv_rects = []
shop_weapon_slot_rect = pygame.Rect(0, 0, 0, 0)
shop_armor_slot_rect = pygame.Rect(0, 0, 0, 0)

# Confirmation modal button rects
confirm_yes_rect = pygame.Rect(0, 0, 0, 0)
confirm_no_rect = pygame.Rect(0, 0, 0, 0)


def handle_shop_key(event, player_gold):
    """
    Handles keyboard shortcuts while the shop is open.
    Returns (close_shop: bool, updated_gold: int, status_msg: str | None)
    """
    global _pending_transaction, _shop_dragged_item, _shop_drag_source

    if _pending_transaction is not None:
        tx_type = _pending_transaction["type"]
        item = _pending_transaction["item"]
        item_name = item.get("name", "Item")
        price = _pending_transaction["price"]

        if event.key == pygame.K_y:
            if tx_type == "sell":
                _pending_transaction = None
                return False, player_gold + price, f"Sold {item_name} for {price}g!"
            elif tx_type == "buy":
                hero = _pending_transaction["hero"]
                slot = _pending_transaction["target_slot"]
                if player_gold >= price and hero["inventory"][slot] is None:
                    hero["inventory"][slot] = item
                    _pending_transaction = None
                    return False, player_gold - price, f"Bought {item_name} for {price}g!"
                _pending_transaction = None
                return False, player_gold, "Could not complete purchase."

        elif event.key in (pygame.K_n, pygame.K_ESCAPE):
            if tx_type == "sell":
                _return_shop_item(_pending_transaction["hero"], item, _pending_transaction["source"])
                _pending_transaction = None
                return False, player_gold, f"Cancelled selling {item_name}."
            elif tx_type == "buy":
                _pending_transaction = None
                return False, player_gold, f"Cancelled buying {item_name}."

        return False, player_gold, None

    if event.key == pygame.K_ESCAPE:
        if _shop_dragged_item is not None and _shop_drag_source is not None:
            _return_shop_item(
                _shop_drag_source[1] if _shop_drag_source[0] != "shop" else None,
                _shop_dragged_item,
                _shop_drag_source,
            )
            _shop_dragged_item = None
            _shop_drag_source = None
        return True, player_gold, "Left the Blacksmith Shop."

    return False, player_gold, None


def draw_shop_dialog(surface, hero, player_gold):
    """
    Draws the Blacksmith shop interface, handles drag-and-drop buying/selling,
    and renders the confirmation popup for both buying and selling.
    Returns (updated_gold, status_message_or_None).
    """
    global _shop_dragged_item, _shop_drag_source, _prev_mouse_pressed, _pending_transaction
    global shop_grid_rects, player_inv_rects, shop_weapon_slot_rect, shop_armor_slot_rect
    global confirm_yes_rect, confirm_no_rect

    font_med, font_large, _ = get_fonts()
    status_msg = None

    # Semi-transparent backdrop
    overlay = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT), pygame.SRCALPHA)
    overlay.fill((10, 10, 15, 230))
    surface.blit(overlay, (0, 0))

    # --- LEFT PANEL: MERCHANT SHOP (Grid Matrix) ---
    pygame.draw.rect(surface, (25, 25, 35), shop_panel_rect)
    pygame.draw.rect(surface, (180, 140, 70), shop_panel_rect, 3)

    title_shop = font_large.render("Blacksmith Shop", True, (240, 200, 100))
    surface.blit(title_shop, (shop_panel_rect.x + 20, shop_panel_rect.y + 15))

    gold_surf = font_med.render(f"Party Gold: {player_gold}g", True, (255, 215, 0))
    surface.blit(gold_surf, (shop_panel_rect.right - gold_surf.get_width() - 20, shop_panel_rect.y + 18))
    pygame.draw.line(surface, (90, 80, 60), (shop_panel_rect.x + 20, shop_panel_rect.y + 45), (shop_panel_rect.right - 20, shop_panel_rect.y + 45), 1)

    # Render Shop Matrix (40x40 slots)
    shop_grid_rects = []
    slot_size = 40
    cols = 6
    start_x = shop_panel_rect.x + 25
    start_y = shop_panel_rect.y + 65

    shop_item_ids = list(ITEMS.keys())

    for idx, item_id in enumerate(shop_item_ids):
        r = idx // cols
        c = idx % cols
        cell_x = start_x + c * (slot_size + 8)
        cell_y = start_y + r * (slot_size + 8)
        cell_rect = pygame.Rect(cell_x, cell_y, slot_size, slot_size)
        shop_grid_rects.append((cell_rect, item_id))

        pygame.draw.rect(surface, (35, 35, 48), cell_rect)
        pygame.draw.rect(surface, (110, 90, 60), cell_rect, 1)

        temp_item = get_item(item_id)
        icon = get_item_icon(temp_item)
        icon_rect = icon.get_rect(center=cell_rect.center)
        surface.blit(icon, icon_rect)

    # --- RIGHT PANEL: PLAYER INVENTORY & EQUIPMENT ---
    pygame.draw.rect(surface, (25, 25, 35), player_panel_rect)
    pygame.draw.rect(surface, (140, 140, 160), player_panel_rect, 3)

    title_player = font_large.render(f"Customer: {hero['name']} ({hero['class']})", True, (220, 220, 240))
    surface.blit(title_player, (player_panel_rect.x + 20, player_panel_rect.y + 15))
    pygame.draw.line(surface, (70, 70, 90), (player_panel_rect.x + 20, player_panel_rect.y + 45), (player_panel_rect.right - 20, player_panel_rect.y + 45), 1)

    # Mini Equipment Slots
    shop_weapon_slot_rect = pygame.Rect(player_panel_rect.x + 20, player_panel_rect.y + 55, 36, 36)
    shop_armor_slot_rect = pygame.Rect(player_panel_rect.x + 64, player_panel_rect.y + 55, 36, 36)

    pygame.draw.rect(surface, (30, 30, 40), shop_weapon_slot_rect)
    pygame.draw.rect(surface, (110, 100, 70), shop_weapon_slot_rect, 2)
    if hero.get("weapon"):
        w_icon = get_item_icon(hero["weapon"])
        surface.blit(w_icon, w_icon.get_rect(center=shop_weapon_slot_rect.center))

    pygame.draw.rect(surface, (30, 30, 40), shop_armor_slot_rect)
    pygame.draw.rect(surface, (110, 100, 70), shop_armor_slot_rect, 2)
    if hero.get("armor"):
        a_icon = get_item_icon(hero["armor"])
        surface.blit(a_icon, a_icon.get_rect(center=shop_armor_slot_rect.center))

    # Player Inventory Slots (10 slots)
    player_inv_rects = []
    inv_start_x = player_panel_rect.x + 20
    inv_start_y = player_panel_rect.y + 105
    inv_slot_w = 320
    inv_slot_h = 32
    inv_slot_spacing = 5

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

    footer_txt = font_med.render("Drag from shop to buy | Drag to shop to sell (50% price) | [ESC] Close", True, (170, 170, 170))
    surface.blit(footer_txt, footer_txt.get_rect(center=(VIRTUAL_WIDTH // 2, 545)))

    # ==========================================
    # MOUSE INPUT HANDLING
    # ==========================================
    window_size = pygame.display.get_surface().get_size()
    mouse_pos = get_virtual_mouse_pos_from_raw(pygame.mouse.get_pos(), window_size)
    mouse_buttons = pygame.mouse.get_pressed()
    left_clicked = mouse_buttons[0] and not _prev_mouse_pressed
    left_released = not mouse_buttons[0] and _prev_mouse_pressed

    # If Confirmation Popup is open, block background drag/drop and handle popup buttons
    if _pending_transaction is not None:
        _draw_transaction_confirmation(surface, mouse_pos, font_med, font_large)

        if left_clicked:
            tx_type = _pending_transaction["type"]
            item = _pending_transaction["item"]
            item_name = item.get("name", "Item")
            price = _pending_transaction["price"]

            if confirm_yes_rect.collidepoint(mouse_pos):
                if tx_type == "sell":
                    player_gold += price
                    status_msg = f"Sold {item_name} for {price}g!"
                elif tx_type == "buy":
                    tx_hero = _pending_transaction["hero"]
                    slot = _pending_transaction["target_slot"]
                    if player_gold >= price and tx_hero["inventory"][slot] is None:
                        tx_hero["inventory"][slot] = item
                        player_gold -= price
                        status_msg = f"Bought {item_name} for {price}g!"
                _pending_transaction = None

            elif confirm_no_rect.collidepoint(mouse_pos):
                if tx_type == "sell":
                    _return_shop_item(_pending_transaction["hero"], item, _pending_transaction["source"])
                    status_msg = f"Cancelled selling {item_name}."
                elif tx_type == "buy":
                    status_msg = f"Cancelled buying {item_name}."
                _pending_transaction = None

        _prev_mouse_pressed = mouse_buttons[0]
        return player_gold, status_msg

    # 1. Pick Up Item
    if left_clicked:
        if shop_panel_rect.collidepoint(mouse_pos):
            for rect, item_id in shop_grid_rects:
                if rect.collidepoint(mouse_pos):
                    _shop_dragged_item = get_item(item_id)
                    _shop_drag_source = ("shop", item_id)
                    break
        elif shop_weapon_slot_rect.collidepoint(mouse_pos) and hero["weapon"]:
            _shop_dragged_item = hero["weapon"]
            _shop_drag_source = ("weapon", hero)
            hero["weapon"] = None
        elif shop_armor_slot_rect.collidepoint(mouse_pos) and hero.get("armor"):
            _shop_dragged_item = hero["armor"]
            _shop_drag_source = ("armor", hero)
            hero["armor"] = None
        else:
            for i, rect in enumerate(player_inv_rects):
                if rect.collidepoint(mouse_pos) and hero["inventory"][i]:
                    _shop_dragged_item = hero["inventory"][i]
                    _shop_drag_source = ("inventory", hero, i)
                    hero["inventory"][i] = None
                    break

    # 2. Drop Item (Open Buy/Sell Confirmation, or Reorganize)
    elif left_released and _shop_dragged_item is not None:
        handled = False

        # Dropped into Shop Area -> OPEN SALE CONFIRMATION POPUP
        if shop_panel_rect.collidepoint(mouse_pos):
            if _shop_drag_source[0] != "shop":
                offer_price = max(1, _shop_dragged_item.get("price", 20) // 2)
                _pending_transaction = {
                    "type": "sell",
                    "hero": hero,
                    "item": _shop_dragged_item,
                    "source": _shop_drag_source,
                    "target_slot": None,
                    "price": offer_price,
                }
            handled = True

        # Dropped into Player Area -> OPEN BUY CONFIRMATION POPUP or Reorganize
        elif player_panel_rect.collidepoint(mouse_pos):
            if _shop_drag_source[0] == "shop":
                item_price = _shop_dragged_item.get("price", 50)
                if player_gold >= item_price:
                    # Find target slot or first empty slot
                    target_slot = None
                    for i, rect in enumerate(player_inv_rects):
                        if rect.collidepoint(mouse_pos) and hero["inventory"][i] is None:
                            target_slot = i
                            break
                    if target_slot is None:
                        for i in range(10):
                            if hero["inventory"][i] is None:
                                target_slot = i
                                break

                    if target_slot is not None:
                        _pending_transaction = {
                            "type": "buy",
                            "hero": hero,
                            "item": _shop_dragged_item,
                            "source": _shop_drag_source,
                            "target_slot": target_slot,
                            "price": item_price,
                        }
                    else:
                        status_msg = f"{hero['name']}'s inventory is full!"
                else:
                    status_msg = f"Not enough gold! Need {item_price}g (have {player_gold}g)."
                handled = True
            else:
                # Re-placing player's own item within inventory
                for i, rect in enumerate(player_inv_rects):
                    if rect.collidepoint(mouse_pos):
                        old_item = hero["inventory"][i]
                        hero["inventory"][i] = _shop_dragged_item
                        if old_item:
                            _return_shop_item(hero, old_item, _shop_drag_source)
                        handled = True
                        break

        if not handled:
            _return_shop_item(hero, _shop_dragged_item, _shop_drag_source)

        _shop_dragged_item = None
        _shop_drag_source = None

    _prev_mouse_pressed = mouse_buttons[0]

    # Render Tooltip for hovered Shop Item
    hovered_shop_item = None
    for rect, item_id in shop_grid_rects:
        if rect.collidepoint(mouse_pos):
            hovered_shop_item = get_item(item_id)
            break

    if hovered_shop_item and _shop_dragged_item is None:
        tip_title = font_med.render(f"{hovered_shop_item['name']}", True, (255, 255, 150))
        tip_price = font_med.render(f"Price: {hovered_shop_item.get('price', 50)}g", True, (255, 215, 0))
        allowed_str = get_class_abbrev_str(hovered_shop_item.get("allowed_classes", []))
        tip_cls = font_med.render(f"Classes: {allowed_str}", True, (150, 200, 255))

        max_w = max(tip_title.get_width(), tip_price.get_width(), tip_cls.get_width())
        tip_rect = pygame.Rect(mouse_pos[0] + 12, mouse_pos[1] - 40, max_w + 16, 64)

        pygame.draw.rect(surface, (15, 15, 25), tip_rect)
        pygame.draw.rect(surface, (200, 180, 100), tip_rect, 1)
        surface.blit(tip_title, (tip_rect.x + 8, tip_rect.y + 4))
        surface.blit(tip_price, (tip_rect.x + 8, tip_rect.y + 22))
        surface.blit(tip_cls, (tip_rect.x + 8, tip_rect.y + 40))

    # Dragged icon following cursor
    if _shop_dragged_item is not None:
        surface.blit(get_item_icon(_shop_dragged_item), (mouse_pos[0] - 16, mouse_pos[1] - 16))

    return player_gold, status_msg


def _draw_transaction_confirmation(surface, mouse_pos, font_med, font_large):
    """Renders the centered modal dialog asking the player to confirm buying or selling an item."""
    global confirm_yes_rect, confirm_no_rect

    dim = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT), pygame.SRCALPHA)
    dim.fill((0, 0, 0, 140))
    surface.blit(dim, (0, 0))

    box_w, box_h = 410, 170
    box_rect = pygame.Rect((VIRTUAL_WIDTH - box_w) // 2, (VIRTUAL_HEIGHT - box_h) // 2 - 40, box_w, box_h)

    tx_type = _pending_transaction["type"]
    item = _pending_transaction["item"]
    price = _pending_transaction["price"]
    is_buy = tx_type == "buy"

    pygame.draw.rect(surface, (22, 24, 34), box_rect)
    pygame.draw.rect(surface, (100, 185, 240) if is_buy else (220, 175, 75), box_rect, 3)

    title_text = "BUY ITEM?" if is_buy else "SELL ITEM?"
    title_color = (140, 215, 255) if is_buy else (255, 215, 100)
    title_surf = font_large.render(title_text, True, title_color)
    surface.blit(title_surf, title_surf.get_rect(center=(box_rect.centerx, box_rect.y + 26)))

    # Item icon + description
    icon = get_item_icon(item)
    icon_rect = icon.get_rect(midleft=(box_rect.x + 35, box_rect.y + 68))
    surface.blit(icon, icon_rect)

    verb = "Buy" if is_buy else "Sell"
    desc_surf = font_med.render(f"{verb} {item.get('name', 'Item')} for {price} Gold?", True, (235, 235, 240))
    surface.blit(desc_surf, desc_surf.get_rect(midleft=(icon_rect.right + 14, box_rect.y + 68)))

    # Buttons
    btn_w, btn_h = 145, 36
    confirm_yes_rect = pygame.Rect(box_rect.centerx - btn_w - 15, box_rect.bottom - 52, btn_w, btn_h)
    confirm_no_rect = pygame.Rect(box_rect.centerx + 15, box_rect.bottom - 52, btn_w, btn_h)

    yes_hover = confirm_yes_rect.collidepoint(mouse_pos)
    no_hover = confirm_no_rect.collidepoint(mouse_pos)

    pygame.draw.rect(surface, (45, 120, 65) if yes_hover else (30, 90, 48), confirm_yes_rect)
    pygame.draw.rect(surface, (110, 220, 140), confirm_yes_rect, 2)
    yes_text = "[Y] Yes, Buy" if is_buy else "[Y] Yes, Sell"
    yes_lbl = font_med.render(yes_text, True, (240, 255, 240))
    surface.blit(yes_lbl, yes_lbl.get_rect(center=confirm_yes_rect.center))

    pygame.draw.rect(surface, (130, 50, 50) if no_hover else (95, 35, 35), confirm_no_rect)
    pygame.draw.rect(surface, (220, 110, 110), confirm_no_rect, 2)
    no_lbl = font_med.render("[N] Cancel", True, (255, 235, 235))
    surface.blit(no_lbl, no_lbl.get_rect(center=confirm_no_rect.center))


def _return_shop_item(hero, item, source):
    if source is None:
        return
    stype = source[0]
    if stype == "shop":
        return
    elif stype == "weapon":
        hero["weapon"] = item
    elif stype == "armor":
        hero["armor"] = item
    elif stype == "inventory":
        _, _, idx = source
        if hero["inventory"][idx] is None:
            hero["inventory"][idx] = item
        else:
            for i in range(10):
                if hero["inventory"][i] is None:
                    hero["inventory"][i] = item
                    break
