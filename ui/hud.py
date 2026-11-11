import math
import pygame

from assets.party_members import party_members, HERO_PORTRAIT_SIZE
from assets.spells import SPELLS
from ui.common import VIRTUAL_HEIGHT, get_fonts


# ==========================================
# PARTY UI RENDER (Seamless Bottom Bar)
# ==========================================
def draw_party_ui(surface, current_actor=None, targeting_active=False):
    font_med, font_large, _ = get_fonts()
    w = surface.get_width()
    ui_top = 546
    ui_height = VIRTUAL_HEIGHT - ui_top  # 194px seamlessly fills the bottom
    bar_rect = pygame.Rect(0, ui_top, w, ui_height)
    pygame.draw.rect(surface, (20, 20, 25), bar_rect)
    pygame.draw.line(surface, (50, 50, 60), (0, ui_top), (w, ui_top), 2)

    spacing = 160
    start_x = (w - (len(party_members) * spacing)) / 2

    total_content_height = HERO_PORTRAIT_SIZE + 6 + 16 + 6 + 5 + 4 + 5
    start_y = ui_top + (ui_height - total_content_height) // 2 + 6
    portrait_offset = (spacing - HERO_PORTRAIT_SIZE) // 2

    for i, hero in enumerate(party_members):
        slot_x = start_x + i * spacing
        cx = slot_x + portrait_offset

        surface.blit(hero["avatar"], (cx, start_y))

        # Healing flash effect
        if hero.get("heal_flash", 0) > 0:
            flash_surf = pygame.Surface((HERO_PORTRAIT_SIZE, HERO_PORTRAIT_SIZE), pygame.SRCALPHA)
            alpha = int(140 * (hero["heal_flash"] / 30))
            flash_surf.fill((60, 255, 120, alpha))
            surface.blit(flash_surf, (cx, start_y))
            pygame.draw.rect(surface, (100, 255, 150), (cx, start_y, HERO_PORTRAIT_SIZE, HERO_PORTRAIT_SIZE), 3)

        # Targeting mode highlight (bright pulsing border & number badge)
        if targeting_active:
            pulse = int(abs(math.sin(pygame.time.get_ticks() * 0.01)) * 100) + 155
            pygame.draw.rect(surface, (pulse, 255, pulse),
                             (cx - 4, start_y - 4, HERO_PORTRAIT_SIZE + 8, HERO_PORTRAIT_SIZE + 8), 4)

            # Badge overlay
            badge_rect = pygame.Rect(cx + HERO_PORTRAIT_SIZE - 28, start_y + 4, 24, 24)
            pygame.draw.rect(surface, (20, 160, 60), badge_rect)
            pygame.draw.rect(surface, (255, 255, 255), badge_rect, 2)
            badge_txt = font_large.render(str(i + 1), True, (255, 255, 255))
            surface.blit(badge_txt, badge_txt.get_rect(center=badge_rect.center))
        elif current_actor == hero:
            pygame.draw.rect(
                surface, (255, 215, 0), (cx - 3, start_y - 3, HERO_PORTRAIT_SIZE + 6, HERO_PORTRAIT_SIZE + 6), 3
            )

        name_y = start_y + HERO_PORTRAIT_SIZE + 6
        name_txt = font_med.render(
            f"[{i + 1}] {hero['name']}",
            True,
            (230, 230, 230) if hero["hp"] > 0 else (120, 120, 120),
        )
        name_rect = name_txt.get_rect(midtop=(slot_x + spacing / 2, name_y))
        surface.blit(name_txt, name_rect)

        hp_bar_width = HERO_PORTRAIT_SIZE - 10
        hp_bar_height = 5
        hp_bar_x = cx + 5
        hp_bar_y = name_y + 16 + 6

        bg_bar_rect = pygame.Rect(hp_bar_x, hp_bar_y, hp_bar_width, hp_bar_height)
        pygame.draw.rect(surface, (60, 30, 30), bg_bar_rect)

        hp_ratio = max(0.0, min(1.0, hero["hp"] / max(1, hero["max_hp"])))
        fill_width = int(hp_bar_width * hp_ratio)
        if fill_width > 0:
            fill_bar_rect = pygame.Rect(hp_bar_x, hp_bar_y, fill_width, hp_bar_height)
            bar_color = (50, 205, 50) if hero["hp"] > 0 else (150, 150, 150)
            pygame.draw.rect(surface, bar_color, fill_bar_rect)
        pygame.draw.rect(surface, (100, 100, 100), bg_bar_rect, 1)

        # MP Bar
        if hero.get("max_mp", 0) > 0:
            mp_bar_y = hp_bar_y + hp_bar_height + 4
            bg_mp_rect = pygame.Rect(hp_bar_x, mp_bar_y, hp_bar_width, hp_bar_height)
            pygame.draw.rect(surface, (30, 30, 60), bg_mp_rect)
            mp_ratio = max(0.0, min(1.0, hero["mp"] / max(1, hero["max_mp"])))
            mp_fill_width = int(hp_bar_width * mp_ratio)
            if mp_fill_width > 0:
                mp_fill_rect = pygame.Rect(hp_bar_x, mp_bar_y, mp_fill_width, hp_bar_height)
                pygame.draw.rect(surface, (70, 150, 255), mp_fill_rect)
            pygame.draw.rect(surface, (80, 80, 120), bg_mp_rect, 1)


# ==========================================
# SPELL BOOK SUBSCREEN RENDER
# ==========================================
def draw_spell_book(surface, hero):
    font_med, font_large, _ = get_fonts()
    w = surface.get_width()
    bg_rect = pygame.Rect(0, 0, w, 580)
    pygame.draw.rect(surface, (20, 20, 35), bg_rect)
    pygame.draw.rect(surface, (100, 140, 220), bg_rect, 3)

    title_txt = font_large.render(
        f"Spell Book: {hero['name']} ({hero['class']}) — Mana: {hero['mp']} / {hero['max_mp']}",
        True,
        (160, 210, 255),
    )
    surface.blit(title_txt, (bg_rect.x + 20, bg_rect.y + 15))
    pygame.draw.line(
        surface,
        (60, 80, 120),
        (bg_rect.x + 20, bg_rect.y + 45),
        (bg_rect.right - 20, bg_rect.y + 45),
        1,
    )

    spells = hero.get("spells", [])
    if not spells:
        no_spell_txt = font_large.render("No spells learned.", True, (170, 170, 170))
        surface.blit(no_spell_txt, (bg_rect.x + 25, bg_rect.y + 75))
    else:
        for i, s_name in enumerate(spells):
            spell = SPELLS[s_name]
            sy = bg_rect.y + 75 + i * 85

            spell_box = pygame.Rect(bg_rect.x + 25, sy, bg_rect.width - 50, 70)
            pygame.draw.rect(surface, (30, 30, 48), spell_box)
            pygame.draw.rect(surface, (80, 120, 180), spell_box, 2)

            icon_rect = pygame.Rect(spell_box.x + 12, spell_box.y + 12, 46, 46)
            pygame.draw.rect(surface, (40, 70, 130), icon_rect)
            if s_name == "Magic Arrow":
                pygame.draw.line(surface, (200, 240, 255), (icon_rect.left + 10, icon_rect.centery),
                                 (icon_rect.right - 10, icon_rect.centery), 3)
                pygame.draw.line(surface, (200, 240, 255), (icon_rect.right - 16, icon_rect.centery - 8),
                                 (icon_rect.right - 10, icon_rect.centery), 3)
                pygame.draw.line(surface, (200, 240, 255), (icon_rect.right - 16, icon_rect.centery + 8),
                                 (icon_rect.right - 10, icon_rect.centery), 3)
            elif s_name == "Heal":
                # Draw clear red medical/pharmacy cross for Heal spell
                pygame.draw.rect(surface, (40, 70, 130), icon_rect)

                center_x = icon_rect.centerx
                center_y = icon_rect.centery

                # A subtle glow effect
                pygame.draw.line(surface, (255, 180, 180),
                                 (center_x - 15, center_y + 1),
                                 (center_x + 17, center_y + 1), width=2)
                pygame.draw.line(surface, (255, 180, 180),
                                 (center_x + 1, center_y - 15),
                                 (center_x + 1, center_y + 17), width=3)
                # Vertical bar - extends up/down from center
                pygame.draw.line(surface, (255, 80, 80),
                                 (center_x, center_y - 16),
                                 (center_x, center_y + 16), width=3)
                # Horizontal bar - extends left/right from center
                pygame.draw.line(surface, (255, 80, 80),
                                 (center_x - 16, center_y),
                                 (center_x + 16, center_y), width=3)

            name_txt = font_large.render(f"[{i + 1}] {spell['name']}", True, (255, 255, 255))
            cost_txt = font_med.render(f"Cost: {spell['cost']} MP", True, (120, 180, 255))

            if "damage" in spell:
                stat_str = f"Damage: {spell['damage']}"
            elif "healing" in spell:
                stat_str = f"Heal: {spell['healing']}"
            else:
                stat_str = ""

            dmg_txt = font_med.render(stat_str, True, (255, 120, 120))
            desc_txt = font_med.render(spell['desc'], True, (180, 180, 190))

            surface.blit(name_txt, (spell_box.x + 75, spell_box.y + 12))
            surface.blit(cost_txt, (spell_box.x + 280, spell_box.y + 14))
            surface.blit(dmg_txt, (spell_box.x + 400, spell_box.y + 14))
            surface.blit(desc_txt, (spell_box.x + 75, spell_box.y + 38))

    footer_txt = font_med.render(
        "Press [1-2] to Select Spell  |  [ESC] Return", True, (170, 170, 170)
    )
    surface.blit(footer_txt, footer_txt.get_rect(center=(bg_rect.centerx, 520)))


# ==========================================
# CHARACTER SUBSCREEN RENDER
# ==========================================
def draw_character_subscreen(surface, hero):
    font_med, font_large, _ = get_fonts()
    w = surface.get_width()
    bg_rect = pygame.Rect(0, 0, w, 580)
    pygame.draw.rect(surface, (22, 22, 28), bg_rect)
    pygame.draw.rect(surface, (160, 140, 90), bg_rect, 3)

    title_txt = font_large.render(
        f"Character Sheet: {hero['name']} ({hero['class']})",
        True,
        (240, 220, 150),
    )
    surface.blit(title_txt, (bg_rect.x + 20, bg_rect.y + 15))
    pygame.draw.line(
        surface,
        (90, 80, 55),
        (bg_rect.x + 20, bg_rect.y + 45),
        (bg_rect.right - 20, bg_rect.y + 45),
        1,
    )

    avatar_x = bg_rect.x + 25
    avatar_y = bg_rect.y + 60
    surface.blit(hero["avatar"], (avatar_x, avatar_y))

    stats_x = avatar_x + 110
    stats_y = avatar_y + 5
    name_txt = font_large.render(hero["name"], True, (255, 255, 255))
    class_txt = font_med.render(f"Class: {hero['class']}", True, (180, 180, 190))

    # Level & Total Experience display
    lvl = hero.get("level", 1)
    exp = hero.get("exp", 0)
    level_txt = font_med.render(f"Level: {lvl}", True, (220, 200, 100))
    exp_txt = font_med.render(f"Experience: {exp}", True, (220, 200, 100))

    hp_txt = font_med.render(
        f"Hit Points: {hero['hp']} / {hero['max_hp']}", True, (120, 220, 120)
    )
    mp_txt = font_med.render(
        f"Mana: {hero['mp']} / {hero['max_mp']}", True, (120, 180, 255)
    )

    if hero["weapon"] is not None:
        atk_str = f"Attack: {hero['weapon']['min_atk']}-{hero['weapon']['max_atk']}"
    else:
        atk_str = "Attack: 0"
    atk_txt = font_med.render(atk_str, True, (220, 120, 120))

    if hero.get("armor") is not None:
        def_str = f"Defense: {hero['armor']['min_def']}-{hero['armor']['max_def']}"
    else:
        def_str = "Defense: 0"
    def_txt = font_med.render(def_str, True, (120, 160, 220))

    # Render top info (Name, Class, Level, Experience)
    surface.blit(name_txt, (stats_x, stats_y))
    surface.blit(class_txt, (stats_x, stats_y + 20))
    surface.blit(level_txt, (stats_x, stats_y + 42))
    surface.blit(exp_txt, (stats_x, stats_y + 62))

    # Divider line separating progression stats from combat stats
    pygame.draw.line(
        surface,
        (70, 70, 85),
        (stats_x, stats_y + 86),
        (stats_x + 220, stats_y + 86),
        1
    )

    # Render combat stats below the divider
    surface.blit(hp_txt, (stats_x, stats_y + 96))
    surface.blit(mp_txt, (stats_x, stats_y + 116))
    surface.blit(atk_txt, (stats_x, stats_y + 136))
    surface.blit(def_txt, (stats_x, stats_y + 156))

    sil_center_x = bg_rect.centerx
    sil_center_y = bg_rect.centery + 30
    sil_color = (55, 55, 70)

    pygame.draw.circle(surface, sil_color, (sil_center_x, sil_center_y - 80), 20)
    torso_rect = pygame.Rect(sil_center_x - 28, sil_center_y - 55, 56, 85)
    pygame.draw.rect(surface, sil_color, torso_rect, border_radius=6)
    pygame.draw.rect(
        surface,
        sil_color,
        (sil_center_x - 46, sil_center_y - 50, 14, 75),
        border_radius=4,
    )
    pygame.draw.rect(
        surface,
        sil_color,
        (sil_center_x + 32, sil_center_y - 50, 14, 75),
        border_radius=4,
    )

    # Armor slot & icon
    armor_slot_rect = pygame.Rect(sil_center_x - 20, sil_center_y - 40, 40, 40)
    pygame.draw.rect(surface, (30, 30, 38), armor_slot_rect)
    pygame.draw.rect(surface, (110, 100, 70), armor_slot_rect, 2)
    if hero.get("armor") is not None and "icon" in hero["armor"]:
        armor_icon_rect = hero["armor"]["icon"].get_rect(center=armor_slot_rect.center)
        surface.blit(hero["armor"]["icon"], armor_icon_rect)

    # Weapon slot & icon
    weapon_slot_rect = pygame.Rect(sil_center_x - 80, sil_center_y - 20, 40, 40)
    pygame.draw.rect(surface, (30, 30, 38), weapon_slot_rect)
    pygame.draw.rect(surface, (110, 100, 70), weapon_slot_rect, 2)
    if hero["weapon"] is not None and "icon" in hero["weapon"]:
        icon_rect = hero["weapon"]["icon"].get_rect(center=weapon_slot_rect.center)
        surface.blit(hero["weapon"]["icon"], icon_rect)

    footer_txt = font_med.render(
        "Press [ESC] to return to Dungeon", True, (170, 170, 170)
    )
    surface.blit(footer_txt, footer_txt.get_rect(center=(bg_rect.centerx, 410)))
