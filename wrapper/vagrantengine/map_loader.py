import logging
import os
import pathlib
import json
from typing import Generator

import pygame
from pygame import sprite
import pygame.image
from pygame.sprite import Sprite
from pyqtree import Index

from wrapper.vagrantengine.animators import SpriteAnimator

from .game import Stage
from .sprites import ActorSprite, GameSprite, TilemapSprite
from .tiled import TiledObject, TiledType

class MapLoader:
    def __init__(self, assets_path: str):
        self.assets_path = assets_path
        self.maps_path = os.path.join(assets_path, "maps")
        self.images_path = os.path.join(assets_path, "images")
        self.tilesets_path = os.path.join(assets_path, "tilesets")
        self.actors_path = os.path.join(assets_path, "actors")
        # self.tilesets = tilesets
        self.global_tileset = dict() # type: dict[int, pygame.Surface]
        self.object_types = dict() # type: dict[str, TiledType]

    def load_tileset(self, ts: dict):
        """Load tiles as pygame Surfaces into a data structure for easy lookup.
        Since Tile Ids are global, consolidate all tiles into a single lookup."""
        tileset_path = ts["source"]
        tileset_file = os.path.join(self.tilesets_path, pathlib.PurePath(tileset_path).name)
        logging.info(f"Tileset File Path: {tileset_file}")
        with open(tileset_file) as f:
            tileset = json.load(f)

        # Tileset Image Load
        tileset_image_path = os.path.join(self.images_path, pathlib.PurePath(tileset["image"]).name)
        logging.info(f"Tileset Image Path: {tileset_image_path}")
        tileset_image = pygame.image.load(tileset_image_path).convert_alpha()
        
        # Iterate over Tileset Image, load into memory
        # columns = tileset["imagewidth"] // tileset["tilewidth"]
        # rows = tileset["imageheight"] // tileset["tileheight"]

        tile_gid = ts["firstgid"]
        for y in range(0, tileset["imageheight"], tileset["tileheight"]):
            for x in range(0, tileset["imagewidth"], tileset["tilewidth"]):
                tile = pygame.Surface((tileset["tilewidth"], tileset["tileheight"])).convert_alpha()
                tile.fill((0, 0, 0, 0)) # Default Transparency
                tile.blit(
                    tileset_image,
                    (0, 0),
                    pygame.Rect
                    (
                        x, y, tileset["tilewidth"], tileset["tileheight"]
                    )
                )
                self.global_tileset[tile_gid] = tile
                tile_gid += 1

    def load_tiled_types(self):
        types_file = os.path.join(self.assets_path, "objecttypes.json")
        with open(types_file) as f:
            object_types = json.load(f)

        for ot in object_types:
            name = ot.get("name")
            self.object_types[name] = TiledType(name, ot["properties"])

    def load_from_tilelayer(self, tilelayer: dict, tilewidth: int, tileheight: int) -> pygame.Surface:
        """Build the full map image/Surface from layer information"""
        map_columns = tilelayer["width"]
        map_rows = tilelayer["height"]

        # Pixel Conversion
        map_width = map_columns * tilewidth
        map_height = map_rows * tileheight

        # Suface Construct
        map_surface = pygame.Surface((map_width, map_height)).convert_alpha()

        # Data Iteration
        map_data = tilelayer["data"]
        
        column_index = 0 # Set up column/x counter
        row_index = 0 # Set up row/y counter

        for d in map_data:
            # logging.info(f"Map Datum: {d}")
            # try:
            d_tile = self.global_tileset[d]

            map_surface.blit(
                d_tile,
                (column_index * tilewidth, row_index * tileheight)
            )
            # Increment and move on
            column_index += 1
            if column_index >= map_columns:
                column_index = 0
                row_index += 1

        return map_surface

    def load_from_objectlayer(self, objectlayer: dict):
        """Generate List of Sprite Objects to return and add to game/stage."""
        object_list = objectlayer['objects'] # type: list[dict]
        # logging.info(f"Object Layer Objects: {object_list}")
        for o in object_list:
            # Load Object Type
            # object_type = o["type"]
            # game_object = GameSprite(name=o["name"], type=o["type"], **o)
            tiled_object = TiledObject(
                id = o.get("id"),
                name = o.get("name"),
                tiledtype = self.object_types[o.get("type")],
                x = o.get("x"),
                y = o.get("y"),
                width = o.get("width"),
                height = o.get("height"),
                gid = o.get("gid")
            )
            # object_type = next(t for t in object_types if t["name"] == o["type"])
            # For each prop in type, set attribute on object
            # for prop in object_type["properties"]:
            #     setattr(game_object, prop["name"], prop["value"])

            yield tiled_object

    def tiled_objects_processing(self, tiled_objects: list[TiledObject]):
        """Process objects on the layer into appropriate sprite objects"""
        # TODO: Pull in Mapping from Game, not Engine
        environment_types = ["Wall", "Solid", "Spawn Point"]
        
        for o in tiled_objects:
            object_sprite = None # type: GameSprite
            image = None # type: pygame.Surface

            if o.type.name in environment_types:
                if o.gid is not None:
                    logging.info(f"Tiled Object Global Id: {o.gid} for {o.name}")
                    image = self.global_tileset[o.gid]
                    # Accounting for weird Tiled coordniate bug
                    # TILED OBJECTS START COUNTING COORDINATES FROM BOTTOM-RIGHT!
                    object_sprite = GameSprite(o.rect.x, (o.rect.y - o.rect.h), o.rect.width, o.rect.height, image, name=o.name, type=o.type)
                else:
                    # Solid(collidable) normal Game Object
                    # object_sprite = GameSprite(o.rect.x, o.rect.y, o.rect.width, o.rect.height, image, name=o.name, type=o.type)
                    object_sprite = GameSprite(o.rect.x, o.rect.y, o.rect.width, o.rect.height, image, name=o.name, type=o.type)

                for prop in object_sprite.type.additional_properties:
                    setattr(object_sprite, prop, object_sprite.type.additional_properties[prop])

                yield object_sprite

    def load_actor_to_stage(self, actor_type: str, x, y, stage: Stage, layer: int):
        """Use type name for Actor custom json load"""
        actor_file = os.path.join(self.actors_path, f"{actor_type}.json")
        with open(actor_file) as af:
            actor = json.load(af)

        # Slice Spritesheet
        spritesheet = actor.get("spritesheet")
        if spritesheet is not None:
            images = slice_spritesheet(self.images_path, **spritesheet)
            initial_image = images[actor.get("initial_slice", 0)]

        animations = actor.get("animations")
        # if animations is not None:
        #     animator = SpriteAnimator(animations)

        zoom = spritesheet.get("zoom", 1)
        actor_sprite = ActorSprite(
            images=images,
            animations=animations,
            x=x,
            y=y,
            width=spritesheet["slice_specs"]["w"] * zoom,
            height=spritesheet["slice_specs"]["h"] * zoom,
            image=initial_image,
            name=actor["name"],
            type=self.object_types[actor_type]
        )
        for prop in actor_sprite.type.additional_properties:
            setattr(actor_sprite, prop, actor_sprite.type.additional_properties[prop])

        logging.info(f"Loading Actor {actor_sprite.name}")
        stage.actors.add(actor_sprite)
        stage.sprite_layers.add(actor_sprite, layer=layer)
        stage.collision_index.insert(actor_sprite, actor_sprite.bbox)

        if actor_type == "Player":
            stage.player = actor_sprite
        logging.info(f"Player: {stage.player}")

    def load_map_to_stage(self, map_file: str, stage: Stage):
        """Build a map image/Surface based on Tiled JSON Map format.
        Map image should be a single surface.
        Objects should be parsed and loaded into layer 2."""

        # Clear the scene (kill & gc the sprites for memory)
        sprites = stage.sprite_layers.sprites() # type: list[Sprite]
        # Remove each sprite from all group membership
        for s in sprites:
            s.kill() # Remove from all groups
        sprites.clear() # TODO: Need to test if this is clearing memory correctly

        map_file = os.path.join(self.maps_path, map_file)
        with open(map_file) as f:
            tilemap = json.load(f)

        # Load in Tilesets for the Map
        # logging.info(f"First Tileset Source: {tilemap['tilesets'][0]['source']}")
        for tileset in tilemap['tilesets']:
            self.load_tileset(tileset)

        # Load in Tiled Object Types for Sprite creation
        self.load_tiled_types()

        # Set Up Map Surface
        # map_columns = tilemap['width']
        # map_rows = tilemap['height']
        tile_width = tilemap['tilewidth'] # In Px
        tile_height = tilemap['tileheight'] # In Px

        # Iterate through the layers and build them out as appropriate
        map_layers = tilemap['layers'] # type: list
        for i, layer in enumerate(map_layers):
            if layer['type'] == "tilelayer":
                # Construct Surface
                map_surface = self.load_from_tilelayer(layer, tile_width, tile_height)
                # Construct Tilemap Sprite
                tilemap = TilemapSprite(map_surface)
                stage.tilemap.sprite = tilemap
                stage.sprite_layers.add(tilemap, layer = i) # Adding to layers in order
                # TODO: Move the boundary/index loading outside of map load?
                stage.boundary = (tilemap.rect.w, tilemap.rect.h)
                stage.collision_index = Index(bbox=(0, 0, tilemap.rect.w, tilemap.rect.h))
            elif layer['type'] == 'objectgroup':
                tiled_objects = list(self.load_from_objectlayer(layer))
                logging.info(f"Tiled Objects: {len(tiled_objects)}")
                game_objects = self.tiled_objects_processing(tiled_objects)

                # Post object load processing
                for go in game_objects:
                    logging.info(f"Loading Game Object {go.type.name}")
                    stage.props.add(go)
                    stage.sprite_layers.add(go, layer=i)
                    stage.collision_index.insert(go, go.bbox)

        # Tilemap and Objects are in, Finalize the Stage
        # TODO: On_Enter or On_Ready hooks
        # Find Spawn Point, load Player
        spawn_point = next(o for o in stage.props.sprites() if o.type.name == "Spawn Point")
        spawn_coordinates = (spawn_point.x, spawn_point.y)
        logging.info(f"Player Spawn Coodinates: {spawn_coordinates}")
        self.load_actor_to_stage("Player", spawn_point.x, spawn_point.y, stage, i+1)

def slice_spritesheet(images_path: str, file: str, slice_specs, slices: list, zoom=None) -> list[pygame.Surface]:
    """file, frame_size, frames"""
    images = [] # type: list[pygame.Surface]

    image = pygame.image.load(os.path.join(images_path, file)).convert_alpha()
    # pygame.image.save(image, os.path.join(SPRITESHEETS, "temp.png"))

    # Scale frame size to tile size (by width)
    # delta = size / slice_specs["w"]
    # scaled_height = round(slice_specs["h"] * delta)

    for y in range(slices[1]):
        for x in range(slices[0]):
            s = pygame.Surface((slice_specs["w"], slice_specs["h"])).convert_alpha()
            s.fill((0, 0, 0, 0)) # IMPORTANT: need to set default background to transparent
            s.blit(
                image, # source
                (0, 0), # dest
                pygame.Rect # area
                (
                    slice_specs["spacing"] + (2 * x * slice_specs["spacing"]) + (x * slice_specs["w"]),
                    slice_specs["spacing"] + (2 * y * slice_specs["spacing"]) + (y * slice_specs["h"]),
                    slice_specs["w"], slice_specs["h"]
                )
            )
            # pygame.image.save(frame, os.path.join(SPRITESHEETS, f"non_scaled_{x}_{y}.png"))
            if zoom is not None:
                s = pygame.transform.rotozoom(s, 0, zoom)
            images.append(s)
    return images