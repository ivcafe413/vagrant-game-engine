import logging
import os
import json

from abc import ABC
from itertools import chain

import pygame
import pygame.image
import pygame.transform
from pygame.sprite import GroupSingle, Group, LayeredDirty
from pyqtree import Index

# from constants import ROOT_PATH
from .sprites import ActorSprite, GameSprite, MoveableSprite

# SCENES = os.path.join(ROOT_PATH, "scenes")
# MAPS = os.path.join(ROOT_PATH, "maps")

# Type Alias for game object collection
# ActorSet = set[Actor]

# Stage class
class Stage(ABC):
    """Stage class. Full game can involved multiple stages in a stack.
    Stage should wrap common elements for any stage.
    Should extend Stage, add registered components for different game types"""
    def __init__(self):
        # Concrete Groups
        self.sprite_layers = LayeredDirty() # TODO: Extend class to account for MySprite type?
        self.actors = Group()
        self.tilemap = GroupSingle()
        self.props = Group()
        # self.player = GroupSingle()
        self.player = None # type: ActorSprite
        # TODO: Make boundary a rect?
        self.boundary = None # type: tuple
        self.collision_index = None # type: Index

        # Command Pattern?
        self.actions = {
            "player_up": lambda d: self.player_move(0, -1, d, "walking_up"),
            "player_down": lambda d: self.player_move(0, 1, d, "walking_down"),
            "player_left": lambda d: self.player_move(-1, 0, d, "walking_left"),
            "player_right": lambda d: self.player_move(1, 0, d, "walking_right")
        }

    @property
    def focus_point(self) -> tuple:
        """Where the game is currently focused.
        This is separate from how the Renderer chooses its viewport,
        which is agnostic from the game focus/boundaries."""
        if self.player is not None:
            return (self.player.x, self.player.y)
        else:
            return (self.boundary[0] / 2, self.boundary[1] / 2)

    def player_move(self, x, y, ev: pygame.KEYDOWN | pygame.KEYUP, action: str):
        """Apply Movement Vector to player character."""
        if self.player is not None:
            if ev == pygame.KEYUP:
                # Key Up, reverse the vector
                x = -x
                y = -y
                # And stop the animation
                self.player.animator.stop(action)
            else:
                # Key Down, start animation loop
                self.player.animator.start(action)
                
            self.player.apply_movement_vector(x, y)

    def update(self):
        """Called to trigger update of game state.
        Should be called once per frame, or more if playing catch-up.
        Extend this in an inherited class, if necessary"""
                
        self.tilemap.update()
        self.actors.update()
        self.props.update()
        # TODO: Does LayeredDirty update layer by layer?

        # Recalculate Index
        moved_actors = (s for s in self.actors.sprites() if s.is_moving)
        moved_props = (s for s in self.props.sprites() if s.is_moving)
        moved_sprites = chain(moved_actors, moved_props)
        # logging.info(moved_sprites)
        for s in moved_sprites:
            # logging.info(f"{s.name} moving from {s.last_rect} to {s.rect}")
            # TODO: Extend/write my own pyqtree?
            # if s.last_rect is not None: 
            self.collision_index.remove(s, s.last_bbox)
            self.collision_index.insert(s, s.bbox)
            s.resolve_collisions(self.collision_index)

            # Check boundaries
            if self.player is not None:
                temp = self.player.bbox # Immutable value
                changed = False

                if self.player.left < 0:
                    self.player.rect.left = 0
                    changed = True
                elif self.player.right > self.boundary[0]:
                    self.player.rect.right = self.boundary[0]
                    changed = True

                if self.player.top < 0:
                    self.player.rect.top = 0
                    changed = True
                elif self.player.bottom > self.boundary[1]:
                    self.player.rect.bottom = self.boundary[1]
                    changed = True

                if changed:
                    self.collision_index.remove(s, temp)
                    self.collision_index.insert(s, s.bbox)

# def construct_actor(images_path: str, **kwargs) -> Actor:
#     """Instantiate an Actor object based on dictionary/json values"""
#     # Pass the rest of the dict as keyword-arguments. Let the actor handle itself
#     # actor = _class(**a) # type: Actor
#     # logging.info(f"kwargs: {kwargs}")
#     actor = Actor(images_path, **kwargs)

#     logging.info(f"New Actor Constructed: {actor.name}")
#     return actor
