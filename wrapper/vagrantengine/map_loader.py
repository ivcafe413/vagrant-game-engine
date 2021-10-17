import logging
import os
import json

import pygame
import pygame.image
from pygame.sprite import Sprite
from pyqtree import Index

from .game import Stage
from .sprites import TilemapSprite

class MapLoader:
    def __init__(self, assets_path: str):
        self.assets_path = assets_path
        self.maps_path = os.path.join(assets_path, "maps")
        self.images_path = os.path.join(assets_path, "images")
        self.tilesets_path = os.path.join(assets_path, "tilesets")
        # self.tilesets = tilesets
        self.global_tileset = dict() # type: dict[int, pygame.Surface]

    def load_tileset(self, tileset_file: str, first_gid: int):
        """Load tiles as pygame Surfaces into a data structure for easy lookup.
        Since Tile Ids are global, consolidate all tiles into a single lookup."""
        
        with open(tileset_file) as f:
            tileset = json.load(f)
            
        # Load the full reference image into memory
        # tileset_image = pygame.image.load(os.path.join(self.images_path, tileset["image"])).convert_alpha()

        # tilecount = 256 # Number of distinct tiles in the tileset

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
            logging.info(f"Map Datum: {d}")
            try:
                d_tile = self.global_tileset[d]
            except KeyError:
                # Key Not Found. Load and try again
                # firstid = 0
                # # Identify the correct tileset to load
                # for ts in tilesets:
                #     firstid = ts["firstgid"]
                pass

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

        logging.info(f"First Tileset Source: {tilemap['tilesets'][0]['source']}")

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

    #     # Load in tileset information
    #     raw_tilesets = tilemap["tilesets"] # type: list[dict]
    #     tilesets = dict()
    #     for t in raw_tilesets:
    #         with open(os.path.join(self.tilesets_path, t["source"])) as tf:
    #             tilesets[t["firstgid"]] = json.load(tf)
    #     single_tileset = tilesets[1]
    #     tileset_image = pygame.image.load(os.path.join(self.images_path, single_tileset["image"])).convert_alpha()

    #     tilemap_sprite = Tile(image=tilemap_surface)
    #     stage.tilemap.add(tilemap_sprite)
    #     stage.boundary = (tilemap_surface.get_width(), tilemap_surface.get_height())
    #     # Scaffold Collision QuadTree
    #     stage.collision_index = Index(bbox=(0, 0, tilemap_surface.get_width(), tilemap_surface.get_height()))

    #     stage.sprites.add(tilemap_sprite, layer=0)
