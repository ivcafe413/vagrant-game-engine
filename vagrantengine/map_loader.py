import logging
import os
import json

import pygame
import pygame.image
from pygame.sprite import Sprite
from pyqtree import Index

from game import Stage
from sprites import Tile

class MapLoader:
    def __init__(self, assets_path: str):
        self.assets_path = assets_path
        self.maps_path = os.path.join(assets_path, "maps")
        self.images_path = os.path.join(assets_path, "images")
        self.tilesets_path = os.path.join(assets_path, "tilesets")
        # self.tilesets = tilesets
        self.global_tileset = dict[int, pygame.Surface]

    def load_tileset(self, tileset_file: str, first_gid: int):
        """Load tiles as pygame Surfaces into a data structure for easy lookup.
        Since Tile Ids are global, consolidate all tiles into a single lookup."""
        with open(tileset_file) as f:
            tileset = json.load(f)
            
        # Load the full reference image into memory
        tileset_image = pygame.image.load(os.path.join(self.images_path, tileset["image"])).convert_alpha()

        tilecount = 256 # Number of distinct tiles in the tileset

    def load_map(self, map_file: str, stage: Stage):
        """Load a Tiled Map Edtior JSON Map"""
        # Clear the scene (kill & gc the sprites for memory)
        sprites = stage.sprites.sprites() # type: list[Sprite]
        # Remove each sprite from all group membership
        for s in sprites:
            s.kill()
        sprites.clear() # TODO: Need to test if this is clearing memory correctly

        # Open the map file
        with open(os.path.join(self.maps_path, map_file)) as f:
            tilemap = json.load(f)

        # Load in tileset information
        raw_tilesets = tilemap["tilesets"] # type: list[dict]
        tilesets = dict()
        for t in raw_tilesets:
            with open(os.path.join(self.tilesets_path, t["source"])) as tf:
                tilesets[t["firstgid"]] = json.load(tf)
        single_tileset = tilesets[1]
        tileset_image = pygame.image.load(os.path.join(self.images_path, single_tileset["image"])).convert_alpha()

        tile_width = tilemap["tilewidth"]
        logging.info(f"Tile Width: {tile_width}")
        # tile_height = tilemap["tileheight"]
        
        # Load in the first layer
        layers = tilemap["layers"]
        tilelayer = layers[0]
        tilemap_surface = pygame.Surface((tilemap["tilewidth"] * tilemap["width"], tilemap["tileheight"] * tilemap["height"]))
        map_x = 0
        map_y = 0
        for d in tilelayer["data"]:
            d_width = (d-1) % single_tileset["columns"]
            d_height = (d-1) // single_tileset["columns"]
            tilemap_surface.blit(
                tileset_image,
                (tilemap["tilewidth"] * map_x, tilemap["tileheight"] * map_y),
                pygame.Rect
                (
                    tilemap["tilewidth"] * d_width,
                    tilemap["tileheight"] * d_height,
                    tilemap["tilewidth"], tilemap["tileheight"]
                )
            )
            map_x += tilemap["tilewidth"]
            if map_x >= single_tileset["imagewidth"]:
                map_x = 0
                map_y += single_tileset["tileheight"]

        tilemap_sprite = Tile(image=tilemap_surface)
        stage.tilemap.add(tilemap_sprite)
        stage.boundary = (tilemap_surface.get_width(), tilemap_surface.get_height())
        # Scaffold Collision QuadTree
        stage.collision_index = Index(bbox=(0, 0, tilemap_surface.get_width(), tilemap_surface.get_height()))

        stage.sprites.add(tilemap_sprite, layer=0)
