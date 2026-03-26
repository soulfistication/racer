#!/usr/bin/env python3
"""
Minimal 2D racer: black track on green grass, checkpoint + finish lap logic, 5 laps to win.
Run: python main.py  (after: pip install -r requirements.txt)
"""

from __future__ import annotations

import math
import sys

import pygame


# --- Display ---
W, H = 960, 640
FPS = 60

GRASS = (34, 139, 34)
BLACK = (0, 0, 0)
WHITE = (240, 240, 240)
CAR_COLOR = (220, 60, 60)
CHECK_COLOR = (255, 220, 0)


def build_track_surface() -> pygame.Surface:
    s = pygame.Surface((W, H))
    s.fill(GRASS)
    cx, cy = W // 2, H // 2
    rx_o, ry_o = 340, 220
    rx_i, ry_i = 190, 120
    outer = pygame.Rect(cx - rx_o, cy - ry_o, 2 * rx_o, 2 * ry_o)
    inner = pygame.Rect(cx - rx_i, cy - ry_i, 2 * rx_i, 2 * ry_i)
    pygame.draw.ellipse(s, BLACK, outer)
    pygame.draw.ellipse(s, GRASS, inner)
    return s


def is_on_track(track: pygame.Surface, x: float, y: float) -> bool:
    ix, iy = int(x), int(y)
    if not (0 <= ix < W and 0 <= iy < H):
        return False
    r, g, b, *_ = track.get_at((ix, iy))
    # Treat near-black as track (antialiasing / edges)
    return r + g + b < 80


def main() -> None:
    pygame.init()
    pygame.display.set_caption("Racer — 5 laps to win")
    screen = pygame.display.set_mode((W, H))
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 36)
    big_font = pygame.font.Font(None, 64)

    track = build_track_surface()
    cx, cy = W // 2, H // 2
    rx_o, ry_o = 340, 220

    # Hit zones at top (checkpoint) and bottom (finish): works when the car runs
    # horizontally across those parts of the oval.
    check_zone = pygame.Rect(cx - 55, cy - ry_o + 4, 110, 40)
    finish_zone = pygame.Rect(cx - 55, cy + ry_o - 44, 110, 40)
    y_checkpoint = check_zone.centery
    y_finish = finish_zone.centery

    # Car state
    x, y = float(cx), float(y_finish + 40)
    angle = -math.pi / 2  # facing up along bottom straight
    speed = 0.0
    max_speed = 7.5
    accel = 0.18
    friction = 0.02
    grass_drag = 0.14
    turn_rate = 0.055

    laps = 0
    checkpoint_ok = False
    finished = False
    was_in_check = False
    was_in_finish = False

    def reset_run() -> None:
        nonlocal x, y, angle, speed, laps, checkpoint_ok, finished
        nonlocal was_in_check, was_in_finish
        x, y = float(cx), float(y_finish + 40)
        angle = -math.pi / 2
        speed = 0.0
        laps = 0
        checkpoint_ok = False
        finished = False
        was_in_check = False
        was_in_finish = False

    running = True
    while running:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_r and finished:
                    reset_run()

        if not finished:
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                angle -= turn_rate * (0.5 + min(abs(speed) / max_speed, 1.0))
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                angle += turn_rate * (0.5 + min(abs(speed) / max_speed, 1.0))
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                speed += accel
            if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                speed -= accel * 1.1

            speed = max(-max_speed * 0.45, min(max_speed, speed))

            on = is_on_track(track, x, y)
            if on:
                if abs(speed) > 0.01:
                    speed -= math.copysign(friction, speed)
            else:
                speed *= 1.0 - grass_drag
                speed -= math.copysign(friction * 2, speed) if speed != 0 else 0

            x += math.cos(angle) * speed
            y += math.sin(angle) * speed

            # Lap: enter checkpoint zone, then finish zone (stops finish-spam / short cuts).
            in_check = check_zone.collidepoint(x, y)
            in_finish = finish_zone.collidepoint(x, y)
            if in_check and not was_in_check:
                checkpoint_ok = True
            if in_finish and not was_in_finish and checkpoint_ok:
                laps += 1
                checkpoint_ok = False
                if laps >= 5:
                    finished = True
            was_in_check = in_check
            was_in_finish = in_finish

        screen.blit(track, (0, 0))

        # Finish line (white) and checkpoint strip (yellow) across the track width
        x_left_o = cx - int(math.sqrt(max(rx_o * rx_o - (y_finish - cy) ** 2, 0)))
        x_right_o = cx + int(math.sqrt(max(rx_o * rx_o - (y_finish - cy) ** 2, 0)))
        pygame.draw.line(screen, WHITE, (x_left_o, y_finish), (x_right_o, y_finish), 3)

        x_left_c = cx - int(math.sqrt(max(rx_o * rx_o - (y_checkpoint - cy) ** 2, 0)))
        x_right_c = cx + int(math.sqrt(max(rx_o * rx_o - (y_checkpoint - cy) ** 2, 0)))
        pygame.draw.line(screen, CHECK_COLOR, (x_left_c, y_checkpoint), (x_right_c, y_checkpoint), 3)

        # Car (triangle pointing forward)
        car_len = 22
        car_wid = 12
        cos_a, sin_a = math.cos(angle), math.sin(angle)
        tip = (x + cos_a * car_len, y + sin_a * car_len)
        left = (
            x + math.cos(angle + 2.4) * car_wid,
            y + math.sin(angle + 2.4) * car_wid,
        )
        right = (
            x + math.cos(angle - 2.4) * car_wid,
            y + math.sin(angle - 2.4) * car_wid,
        )
        pygame.draw.polygon(screen, CAR_COLOR, [tip, left, right])
        pygame.draw.polygon(screen, (40, 40, 40), [tip, left, right], 2)

        hud = font.render(f"Lap {laps} / 5", True, WHITE)
        screen.blit(hud, (16, 12))
        hint = font.render("Arrows / WASD — drive   Esc quit   R restart after win", True, WHITE)
        screen.blit(hint, (16, H - 40))

        if finished:
            overlay = pygame.Surface((W, H), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            screen.blit(overlay, (0, 0))
            t1 = big_font.render("Level complete!", True, WHITE)
            t2 = font.render("5 laps finished. Press R to race again.", True, WHITE)
            screen.blit(t1, t1.get_rect(center=(W // 2, H // 2 - 30)))
            screen.blit(t2, t2.get_rect(center=(W // 2, H // 2 + 30)))

        pygame.display.flip()

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
