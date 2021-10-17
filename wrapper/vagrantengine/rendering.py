import logging

from collections import OrderedDict

import pygame
import pygame.display
import pygame.draw
import pygame.font

from .game import Stage

COLOR_BLACK = (0, 0, 0)
COLOR_WHITE = (255, 255, 255)
COLOR_TRANSPARENT = (0, 0, 0, 0)

# Persisting a lot of data for Renderer, classing out
class Renderer:
    def __init__(self, game: Stage,
        **kwargs: pygame.Surface):
        self._game = game

        self._game_area = pygame.Surface(game.boundary).convert_alpha()
        self._destination_x = 0
        self._destination_y = 0
        self._viewport = pygame.display.get_surface().get_rect() # init to 0,0
        
        if self._viewport.w > self._game.boundary[0]: # Viewport wider than scene
            # Set destination left
            self._destination_x = self._viewport.centerx - (self._game.boundary[0] / 2)
            # Shrink viewport width
            self._viewport.w = self._game.boundary[0]
        if self._viewport.h > self._game.boundary[1]: # Viewport taller than scene
            # Set destination top
            self._destination_y = self._viewport.centery - (self._game.boundary[1] / 2)
            # Shrink viewport height
            self._viewport.h = self._game.boundary[1]

        self._surfaces = kwargs # Non-display and wrapper surfaces
        self._pipeline = OrderedDict()

        # We always render the game first (?)
        self.add_pipeline_step(self._game_area, self.draw_game)

    @property
    def viewport(self) -> pygame.Rect:
        """Calculate and return the Renderer's current viewport
        based on viewport size and current stage's focus point & boundary"""
        # TODO: Give Focus Point a dirty flag and only re-calc on dirty        

        # logging.info(f"Focus: {self._game.focus_point}")
        _viewport = pygame.Rect(
            self._game.focus_point[0] - (self._viewport.w / 2), # left
            self._game.focus_point[1] - (self._viewport.h / 2), # top
            self._viewport.w, self._viewport.h # width, height
        )

        # Too far left or right?
        if _viewport.left < 0: _viewport.left = 0
        if _viewport.right > self._game.boundary[0]:
            _viewport.right = self._game.boundary[0]
        # Too far up or down?
        if _viewport.top < 0: _viewport.top = 0
        if _viewport.bottom > self._game.boundary[1]:
            _viewport.bottom = self._game.boundary[1]
        
        self._viewport = _viewport
        return _viewport

    def add_pipeline_step(self, surface: pygame.Surface, step):
        current_steps = self._pipeline.get(surface, None)
        if current_steps is None:
            self._pipeline[surface] = step
        elif isinstance(current_steps, list):
            current_steps.append(step)
            self._pipeline[surface] = current_steps
        else:
            new_steps = [current_steps, step]
            self._pipeline[surface] = new_steps

    def draw_game(self) -> list[pygame.Rect]:
        """"""
        changes = self._game.sprites.draw(self._game_area)
        # Blit and flip viewport -> display
        pygame.display.get_surface().blit(self._game_area,
            (self._destination_x, self._destination_y),
            self.viewport
        )

        return changes

    def render(self):
        """Run through the entire rendering pipeline, in order"""
        pygame.display.get_surface().fill(COLOR_BLACK)

        updates = []
        for _, steps in self._pipeline.items():
            if isinstance(steps, list):
                for step in steps:
                    updates.extend(step())
            else: # Single
                updates.extend(steps())
        # logging.info(f"Updates: {updates}")

        pygame.display.flip()
        # if(len(updates) > 0):
        # pygame.display.update(self.viewport)

class DebugRenderer:
    def __init__(self, game: Stage, surface: pygame.Surface):
        self._game = game
        self._surface = surface

        self.debug_font = pygame.font.Font(None, 24)

    def draw_debug(self):
        """Draw debug stats over game for dev/test"""
        changes = []

        self._surface.fill(COLOR_TRANSPARENT)
        
        if self._game.player_character is not None:
            debug_dict = {
                "Animation Frame": self._game.player_character.animator.frame_count,
                "Frame Threshold": self._game.player_character.animator.threshold,
                "Current Animation": self._game.player_character.animator.current_animation,
                "Current Index": self._game.player_character.animator.current_index,
                "Current Slice": self._game.player_character.animator.current_slice,
                "Stack Count": len(self._game.player_character.animator.stack),
                "Is Current ?": (self._game.player_character.animator.current is not None),
                "Player Position": self._game.player_character.bbox,
                "Table Position": self._game.props.sprites()[0].bbox,
                "Sprites Moving": len(list(s for s in self._game.sprites.sprites() if s.is_moving))
            }
            current_height = 10
            for k, v in debug_dict.items():
                to_render = "{0}: {1}".format(k, v)
                font_width, font_height = self.debug_font.size(to_render)
                draw_text(self._surface, to_render, 10, current_height, self.debug_font)

                changes.append(pygame.Rect(10, current_height, font_width, font_height))
                current_height += font_height

        pygame.display.get_surface().blit(self._surface, (0, 0))

        return changes

def draw_text(surface: pygame.Surface, string: str, x: int, y: int, font: pygame.font.Font):
    text_surface = font.render(string, True, COLOR_WHITE)
    surface.blit(text_surface, (x, y))