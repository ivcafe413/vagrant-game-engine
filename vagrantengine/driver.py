import logging

import pygame
import pygame.display
import pygame.time

from vagrantengine.game import Stage
from vagrantengine import eventhandler
from vagrantengine.rendering import Renderer

FRAME_RATE = 60
MS_PER_FRAME = (1 / FRAME_RATE) * 1000
GAME_CLOCK = pygame.time.Clock()

_GAME = None # type: Stage

def game_start(game: Stage, renderer: Renderer):
    """Setup the game to run, and then run!"""
    global _GAME
    _GAME = game

    GAME_CLOCK.tick(FRAME_RATE) # Setup initial frame
    game_loop(renderer)

def game_loop(renderer: Renderer):
    time_buffer = 0 # How many MS have passed since last frame

    while True:
        time_buffer += GAME_CLOCK.get_time()
        # If enough time has passed for at least one frame
        while time_buffer >= MS_PER_FRAME:
            eventhandler.handle_events()
            _GAME.update()
            time_buffer -= MS_PER_FRAME

        # Render the game after catching-up on updates
        renderer.render()

        pygame.display.set_caption(f"FPS: {GAME_CLOCK.get_fps():2f}")

        # Tick to the next frame
        GAME_CLOCK.tick(FRAME_RATE)