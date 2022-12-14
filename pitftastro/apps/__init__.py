import inspect
import logging
import os
import pathlib
import textwrap
import uuid
from pathlib import Path
from string import ascii_letters
from typing import Generator

import settings
from libs.framebuffer import Framebuffer
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger("pitftastro.apps")


class AbstractApp:
    """
    Abstract class for apps
    """

    framebuffer: Framebuffer = None
    image: Image = None
    reload_interval: int = 60
    reload_wait: int = 0

    def __init__(self, fb):
        """
        Default app constructor, sets the framebuffer
        :param fb: Framebuffer
        """
        self.framebuffer = fb
        self.blank()
        self.reload()

    def blank(self):
        """
        Reset the image back to the default
        :return: None
        """
        if settings.BACKGROUND:
            image: Image = Image.open(settings.BACKGROUND)
            self.image = image.resize(self.framebuffer.size)
        else:
            self.image = Image.new(
                "RGBA", self.framebuffer.size, settings.BACKGROUND_COLOR
            )

    def text(
        self,
        text,
        position=(5, 5),
        font_name=None,
        font_size=20,
        color=None,
        wrap=True,
        max_lines=None,
    ):
        """
        Draws text onto the app's image
        :param text: string to draw
        :param position: tuple representing where to draw the text
        :param font_name: filename of font to use, None for default
        :param font_size: integer font size to draw
        :param color: color of the text
        :param wrap: boolean whether to wrap the text
        :param max_lines: number of lines to draw maximum
        :return: integer number of lines drawn
        """
        if not font_name:
            font_name = settings.FONT
        if not color:
            color = settings.TEXT_COLOR
        if not self.image:
            raise ValueError("self.image is None")

        font: ImageFont = ImageFont.truetype(font_name, font_size)
        draw: ImageDraw = ImageDraw.Draw(self.image)
        number_of_lines: int = 0
        scaled_wrapped_text: str = ""

        if wrap:
            avg_char_width: int = sum(
                font.getsize(char)[0] for char in ascii_letters
            ) / len(ascii_letters)
            max_char_count: int = int(
                (self.image.size[0] * 0.95) / avg_char_width
            )

            for line in text.split("\n"):
                new_wrapped_text = textwrap.fill(
                    text=line, width=max_char_count
                )
                for wrapped_line in new_wrapped_text.split("\n"):
                    if not max_lines or number_of_lines < max_lines:
                        number_of_lines += 1
                        scaled_wrapped_text += wrapped_line + "\n"
        else:
            for line in text.split("\n"):
                if not max_lines or number_of_lines < max_lines:
                    number_of_lines += 1
                    scaled_wrapped_text += line + "\n"

        draw.text(position, scaled_wrapped_text, font=font, fill=color)

        return number_of_lines

    def wrapped_text(
        self, text, position=(5, 5), font_name=None, font_size=20, color=None
    ):
        """
        DEPRECATED - use text(wrap=True) instead
        Draws text onto the app's image, uses line wrapping
        :param text: string to draw
        :param position: tuple representing where to draw the text
        :param font_name: filename of font to use, None for default
        :param font_size: integer font size to draw
        :param color: color of the text
        :return: integer number of lines drawn
        """
        return self.text(
            text, position, font_name, font_size, color, wrap=True
        )

    def centered_text(
        self,
        text: str,
        color: any = "white",
        y: int = 0,
        font_size: int = 20,
        font_name: str = None,
        max_lines: int = -1,
    ):
        """
        Draws text centered horizontally
        :param text: str text to be displayed
        :param color: any color to use for text
        :param y: vertical starting position
        :param font_size: size of font
        :param font_name: name of font
        :param max_lines: maximum number of lines to show, -1 for no limit
        :return: None
        """
        if not font_name:
            font_name = settings.FONT
        font = ImageFont.truetype(font_name, font_size)
        avg_char_width: int = sum(
            font.getsize(char)[0] for char in ascii_letters
        ) / len(ascii_letters)
        number_of_lines = 0
        for line in text.split("\n"):
            if number_of_lines < max_lines or max_lines == -1:
                centered_position = (self.image.size[0] / 2) - (
                    avg_char_width * len(line) / 2
                )
                position = (
                    centered_position,
                    y + (number_of_lines * font_size),
                )
                self.text(
                    text,
                    color=color,
                    font_name=font_name,
                    font_size=font_size,
                    position=position,
                    wrap=False,
                )
                number_of_lines += 1

        return number_of_lines

    def line(self, position: tuple, fill: any = None, width: int = 5):
        """
        Draw a line onto the buffer
        :param position: tuple position to draw line
        :param fill: color to fill line with
        :param width: width of line
        :return: None
        """
        if not fill:
            fill = settings.TEXT_COLOR
        draw = ImageDraw.Draw(self.image)
        draw.line(position, fill, width)

    def rectangle(
        self,
        position: tuple,
        fill: any = None,
        outline: any = None,
        width: int = 0,
    ):
        if not fill:
            fill = settings.BACKGROUND_COLOR
        if not outline:
            outline = settings.TEXT_COLOR
        draw = ImageDraw.Draw(self.image)
        draw.rectangle(position, fill, outline, width)

    def draw_titlebar(
        self, text: str, color: any = None, fill: any = None, y: int = 0
    ):
        """
        Draws a titlebar
        :param text: str title to display
        :param color: any color to use for text
        :param fill: any color to use for background fill
        :param y: int position on the y axis
        """
        if not color:
            color = settings.TEXT_COLOR
        if not fill:
            fill = settings.BACKGROUND_COLOR
        self.rectangle(
            position=(0, 0, self.framebuffer.size[0], 25),
            fill=fill,
            outline=color,
            width=2,
        )
        self.centered_text(
            text, color=color, y=y, font_size=20, font_name=settings.BOLD_FONT
        )

    def paste_image(self, image, position=(5, 5)):
        """
        Draws an image onto the app's image
        :param image: Image to use
        :param position: tuple position to draw the image
        :return: None
        """
        if not self.image:
            logger.error(
                "App '{0}' called 'paste' without an image!".format(
                    self.__module__
                )
            )
            self.blank()
        self.image.paste(image, position)

    def show(self):
        """
        Draw's the app's image to the framebuffer. Avoid calling this whenever possible.
        :return: None
        """
        if not self.image:
            logger.error(
                "App '{0}' called 'show' without an image!".format(
                    self.__module__
                )
            )
            self.blank()
        if settings.SAVE_SCREENSHOTS:
            filename = "/tmp/{0}-{1}.png".format(self.__module__, uuid.uuid4())
            logger.debug("Saving screenshot to {}".format(filename))
            self.image.save(filename)
        self.framebuffer.show(self.image)

    def reload(self):
        """
        Runs when the app needs to redraw the app image, do your drawing here
        :return: None
        """
        raise NotImplementedError()

    def touch(self, position: tuple):
        """
        Called when the screen is tapped
        :param position: tuple where the screen was touched
        :return: None
        """
        logger.debug("Unhandled PiTFT touch event: {}".format(position))

    def run_iteration(self):
        """
        Main loop function.
        :return: None
        """
        self.reload_wait += 1
        if not self.image or self.reload_wait >= self.reload_interval:
            if self.image:
                logger.debug(
                    "App '{0}' hit auto-reload interval ({1} seconds)".format(
                        type(self).__module__, self.reload_interval
                    )
                )
            self.reload_wait = 0
            self.reload()


def get_apps():
    """
    Get the full list of apps in the apps directory
    :return: list of module names for the apps
    """
    apps: list = []

    path: str = os.path.dirname(
        os.path.abspath(inspect.getfile(inspect.currentframe()))
    )
    app_directory: Generator[Path, None, None] = pathlib.Path(path).rglob(
        "*.py"
    )

    for file in app_directory:
        if file.name == "__init__.py":
            continue
        module_name = file.name.split(".")[0]
        logger.debug("Found '{0}' in '{1}'".format(module_name, path))
        apps.append(module_name)

    return apps


if __name__ == "__main__":
    """
    If run directly, this module tests the get_apps() function and exits
    """
    logging.basicConfig(level=logging.DEBUG)
    get_apps()
