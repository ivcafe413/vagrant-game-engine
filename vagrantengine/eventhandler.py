import logging
import sys

import pygame
import pygame.event
from pygame.event import Event

from vagrantengine.game import Stage

_GAME = None # type: Stage
_BINDINGS = None # type: dict[int, str]

def register_game(game: Stage):
    global _GAME
    _GAME = game

def register_key_bindings(bindings):
    """Pass a dictionary to assign keys to in-game functions.
    Game exposes list of possible actions/functions,
    and Driver/entrypoint binds keys by function name"""
    global _BINDINGS
    _BINDINGS = bindings

def handle_event(event: Event):
    # event_type = event.type
    
    if event.type == pygame.QUIT:
        pygame.quit()
        sys.exit(0)
    elif event.type == pygame.KEYDOWN:
        action = _BINDINGS.get(event.key)
        if action is not None: _GAME.actions[action](pygame.KEYDOWN)
    elif event.type == pygame.KEYUP:
        action = _BINDINGS.get(event.key)
        if action is not None: _GAME.actions[action](pygame.KEYUP)

def handle_events():
    for event in pygame.event.get():
        handle_event(event)
