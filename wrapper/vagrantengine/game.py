import logging
import os
import json

from abc import ABC

import pygame
import pygame.image
import pygame.transform
from pygame.sprite import GroupSingle, Sprite, Group, LayeredDirty
from pyqtree import Index

# from constants import ROOT_PATH
from .sprites import Actor, Tile, MySprite

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
        self.player = GroupSingle()
        # self.player_character = None # type: Actor
        # TODO: Make boundary a rect?
        self.boundary = None # type: tuple
        self.collision_index = None # type: Index

        # Command Pattern?
        self.actions = {
            "player_character_up": lambda d: self.player_move(0, -1, d, "walking_up"),
            "player_character_down": lambda d: self.player_move(0, 1, d, "walking_down"),
            "player_character_left": lambda d: self.player_move(-1, 0, d, "walking_left"),
            "player_character_right": lambda d: self.player_move(1, 0, d, "walking_right")
        }

    @property
    def focus_point(self) -> tuple:
        """Where the game is currently focused.
        This is separate from how the Renderer chooses its viewport,
        which is agnostic from the game focus/boundaries."""
        if self.player_character is not None:
            return (self.player_character.x, self.player_character.y)
        else:
            return (self.boundary[0] / 2, self.boundary[1] / 2)

    def player_move(self, x, y, ev: pygame.KEYDOWN | pygame.KEYUP, action: str):
        """Apply Movement Vector to player character."""
        if ev == pygame.KEYUP:
            # Key Up, reverse the vector
            x = -x
            y = -y
            # And stop the animation
            self.player_character.animator.stop(action)
        else:
            # Key Down, start animation loop
            self.player_character.animator.start(action)
            
        self.player_character.apply_movement_vector(x, y)

    # @abstractmethod
    def update(self):
        """Called to trigger update of game state.
        Should be called once per frame, or more if playing catch-up.
        Extend this in an inherited class, if necessary"""
                
        self.tilemap.update()
        self.actors.update()
        self.props.update()
        # TODO: Does LayeredDirty update layer by layer?

        # Recalculate Index
        moved_sprites = (s for s in self.sprites.sprites() if s.is_moving)
        # logging.info(moved_sprites)
        for s in moved_sprites:
            # logging.info(f"{s.name} moving from {s.last_rect} to {s.rect}")
            # TODO: Extend/write my own pyqtree?
            # if s.last_rect is not None: 
            self.collision_index.remove(s, s.last_bbox)
            self.collision_index.insert(s, s.bbox)
            s.resolve_collisions(self.collision_index)

        # Check boundaries
        if self.player_character is not None:
            temp = self.player_character.bbox # Immutable value
            changed = False

            if self.player_character.left < 0:
                self.player_character.rect.left = 0
                changed = True
            elif self.player_character.right > self.boundary[0]:
                self.player_character.rect.right = self.boundary[0]
                changed = True

            if self.player_character.top < 0:
                self.player_character.rect.top = 0
                changed = True
            elif self.player_character.bottom > self.boundary[1]:
                self.player_character.rect.bottom = self.boundary[1]
                changed = True

            if changed:
                self.collision_index.remove(s, temp)
                self.collision_index.insert(s, s.bbox)

def load_scene(scenes: str, images: str, maps: str, scene_id: int, stage: Stage):
    # # Clear the scene (kill & gc the sprites for memory)
    # sprites = stage.sprite_layers.sprites() # type: list[Sprite]
    # # Remove each sprite from all group membership
    # for s in sprites:
    #     s.kill()
    # sprites.clear() # TODO: Need to test if this is clearing memory correctly

    # Load in target scene
    # scene_file = os.path.join(scenes, str(scene_id) + ".json")
    # with open(scene_file) as f:
    #     scene = json.load(f)

    # Populate the set of actors for the scene (Sprites -> Group)
    actors = [construct_actor(images, **a) for a in scene["actors"]]

    # Construct the tilemap for the scene
    # tilemap = list(construct_tilemap(images, maps, **scene["tilemap"]))

    # Construct various screen objects/props
    props = [MySprite(images, **p) for p in scene["props"]]

    # Begin constructing scene
    # max_x = max(tile.right for tile in tilemap)
    # max_y = max(tile.bottom for tile in tilemap)
    # stage.boundary = (max_x, max_y)

    # # Scaffold Collision QuadTree
    # stage.collision_index = Index(bbox=(0, 0, max_x, max_y))

    # Add all the things to the groups
    # stage.tilemap.add(tilemap)
    stage.actors.add(actors)
    stage.props.add(props)

    stage.player_character = next((a for a in actors if a.is_player), None)

    # stage.sprite_layers.add(tilemap, layer=0)
    stage.sprite_layers.add(props, layer=1)
    # TODO: Split layers?
    stage.sprite_layers.add(actors, layer=1)

    for s in stage.sprite_layers.sprites():
        stage.collision_index.insert(s, s.bbox)

def construct_actor(images_path: str, **kwargs) -> Actor:
    """Instantiate an Actor object based on dictionary/json values"""
    # Pass the rest of the dict as keyword-arguments. Let the actor handle itself
    # actor = _class(**a) # type: Actor
    # logging.info(f"kwargs: {kwargs}")
    actor = Actor(images_path, **kwargs)

    logging.info(f"New Actor Constructed: {actor.name}")
    return actor

def construct_tilemap(images_path: str, maps_path: str, **kwargs):
    """Instantiate full Tilemap for a Scene"""
    # Load tiles (Dictionary Comprehension)
    size = kwargs.get("size")
    # tile_images = dict[str, pygame.Surface]()
    tile_images = dict[str, str]()
    # tile_images = {k:pygame.transform.scale(pygame.image.load(v).convert_alpha(), (tile_size, tile_size)) for (k,v) in tm["tiles"].items()}
    for k, tile in kwargs.get("tiles").items():
        # image = pygame.image.load(os.path.join(TILE_ATLAS, tile)).convert_alpha()
        # image = pygame.transform.scale(image, (size, size))
        tile_images[k] = tile

    # Load the map using tiles
    map_file = os.path.join(maps_path, kwargs.get("map") + ".txt")
    with open(map_file) as f:
        # Enumerating over map lines
        for y, map_line in enumerate(f):
            for x, map_tile in enumerate(map_line.strip()):
                yield Tile(
                    name=tile_images[map_tile],
                    size=size,
                    image=tile_images[map_tile],
                    x=(x*size),
                    y=(y*size),
                    images_path = images_path
                )