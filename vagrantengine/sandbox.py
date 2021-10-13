import logging
import os

import pygame
import pygame.display
import pygame.event

print('__file__={0:<35} | __name__={1:<20} | __package__={2:<20}'.format(__file__,__name__,str(__package__)))

# from .vagrantengine.game import Stage, load_scene
import game
from eventhandler import register_game, register_key_bindings
from rendering import Renderer, DebugRenderer
from driver import game_start
from map_loader import MapLoader

# TODO: Environment Variables
ASSET_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), "assets")
SCENES = os.path.join(ASSET_PATH, "scenes")
MAPS = os.path.join(ASSET_PATH, "maps")

IMAGES = os.path.join(ASSET_PATH, "images")

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

MENU_WIDTH = 100
MENU_HEIGHT = 600
MENU_LEFT = 50

HUD_HEIGHT = 100

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    pygame.init()

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

    # Debug Surface/HUD
    debug_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT)).convert_alpha()

    # Game State Initialization
    stage = game.Stage()

    # Initial Scene Load
    # game.load_scene(SCENES, IMAGES, MAPS, 1, stage)
    loader = MapLoader(ASSET_PATH)
    loader.load_map("sandbox_3.json", stage)

    # Event Handler config
    register_game(stage)
    # Limit allowed Pygame events (performance)
    pygame.event.set_blocked([
        pygame.MOUSEMOTION
    ])
    key_bindings = {
        pygame.K_UP: "player_character_up",
        pygame.K_DOWN: "player_character_down",
        pygame.K_LEFT: "player_character_left",
        pygame.K_RIGHT: "player_character_right"
    }
    register_key_bindings(key_bindings)

    # Renderer Setup
    renderer = Renderer(stage
        # , overworld_menu=overworld_menu
        # , battle_hud=battle_hud
        )
    debug_renderer = DebugRenderer(stage, debug_surface)

    # TODO: Stage Stack

    # Render pipeline defines surface rendering order and functions to use
    renderer.add_pipeline_step(debug_surface, debug_renderer.draw_debug)

    # Game Loop Start
    game_start(stage, renderer)