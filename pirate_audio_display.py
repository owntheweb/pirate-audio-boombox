#!/usr/bin/env python
# Thanks: https://github.com/pimoroni/pirate-audio/tree/master/examples

from PIL import Image, ImageDraw, ImageFont
from ST7789 import ST7789
from pil_warp_speed import PilWarpSpeed

SCREEN_WIDTH = 240
SCREEN_HEIGHT = 240

COLOR_VOLUME_BAR = (255, 0, 152)
COLOR_RFID_LABEL = (255, 222, 243)


class PirateAudioDisplay:
    def __init__(self, font_dir, image_dir, rotation=90, spi_speed_mhz=80):
        self.font_dir = font_dir
        self.image_dir = image_dir
        self.rotation = rotation
        self.spi_speed_mhz = spi_speed_mhz
        self.run = True

        self.image_canvas = Image.open(
            self.image_dir + '/stephans_quintet.png'
            )
        self.image_background = Image.open(
            self.image_dir + '/stephans_quintet.png'
            )
        self.image_play = Image.open(self.image_dir + '/play.png')
        self.image_pause = Image.open(self.image_dir + '/pause.png')
        self.image_next = Image.open(self.image_dir + '/next.png')
        self.image_previous = Image.open(self.image_dir + '/previous.png')
        self.image_cartridge = Image.open(self.image_dir + '/cartridge.png')
        self.draw = ImageDraw.Draw(self.image_canvas)

        self.image_action = None
        self.image_action_show_for = 10
        self.image_action_i = 0

        self.scroll_text = ''
        self.scroll_text_x = 280
        self.scroll_text_y = 100
        self.scroll_text_font = ImageFont.truetype(
            self.font_dir + '/rainyhearts.ttf',
            40
        )
        self.scroll_text_speed = 3

        # init warp speed background effect
        self.warp_speed_effect = PilWarpSpeed(
            star_count=30,
            star_size=8,
            include_triangles=True,
            warp_speed_amount=0.02,
            canvas_width=240,
            canvas_height=240,
            throttle_frames=0
        )

        # init screen
        self.st7789 = ST7789(
            rotation=self.rotation,  # Display the right way up on Pirate Audio
            port=0,       # SPI port
            cs=1,         # SPI port Chip-select channel
            dc=9,         # BCM pin used for data/command
            backlight=13,
            spi_speed_hz=self.spi_speed_mhz * 1000 * 1000
        )

        # init volume bar
        self.volume = 0.0
        self.volume_show_for = 10
        self.volume_show_int = 0

        # init RFID details
        self.rfid_uid = ""
        self.rfid_show_for = 100
        self.rfid_show_int = 0
        # TODO: Define this elsewhere
        self.rfid_font = ImageFont.truetype(
            self.font_dir + '/rainyhearts.ttf',
            36
        )

    def set_scroll_text(self, text):
        self.scroll_text = text
        self.scroll_text_x = 280

    def draw_scroll_text(self):
        if self.scroll_text != '':
            _, _, w, h = self.draw.textbbox(
                (0, 0),
                self.scroll_text,
                font=self.scroll_text_font
            )

            self.scroll_text_x -= self.scroll_text_speed
            self.scroll_text_y = 120 - (h * 0.5)
            if self.scroll_text_x < -w:
                self.scroll_text_x = 280

            self.draw.text(
                (
                    self.scroll_text_x,
                    self.scroll_text_y
                ),
                self.scroll_text, font=self.scroll_text_font,
                fill=(255, 255, 255)
            )

    def set_volume(self, normalizedVolume):
        if normalizedVolume != self.volume:
            self.volume = normalizedVolume
            self.volume_show_int = 0

    def draw_action_image(self):
        if self.image_action_i > 0 and self.image_action:
            self.image_action_i -= 1

            self.image_canvas.paste(
                self.image_action,
                (0, 0),
                self.image_action
            )

    def set_action_image(self, image_name):
        if image_name == 'cartridge':
            self.image_action = self.image_cartridge
        if image_name == 'play':
            self.image_action = self.image_play
        elif image_name == 'pause':
            self.image_action = self.image_pause
        elif image_name == 'next':
            self.image_action = self.image_next
        elif image_name == 'previous':
            self.image_action = self.image_previous

        self.image_action_i = self.image_action_show_for

    # pass in normalized volume value (0.0 to 1.0), show volume bar for a
    # short while after change
    def draw_volume(self):
        if self.volume_show_int <= self.volume_show_for:
            bar_width = SCREEN_WIDTH * self.volume
            bar_height = 20
            self.draw.rectangle(
                (0, SCREEN_HEIGHT - bar_height, bar_width, SCREEN_HEIGHT),
                COLOR_VOLUME_BAR
            )
            self.volume_show_int = self.volume_show_int + 1

    def set_rfid(self, rfid_uid):
        self.rfid_uid = rfid_uid
        self.rfid_show_int = 0

    def draw_rfid(self):
        if self.rfid_show_int <= self.rfid_show_for:
            _, _, w, h = self.draw.textbbox(
                (0, 0),
                self.rfid_uid,
                font=self.rfid_font
            )
            self.draw.text(
                (
                    (SCREEN_WIDTH - w) * 0.5,
                    (SCREEN_HEIGHT - h) * 0.5
                ),
                self.rfid_uid, font=self.rfid_font,
                fill=COLOR_RFID_LABEL
                )
            self.rfid_show_int = self.rfid_show_int + 1

    def render_screen(self):
        self.st7789.display(self.image_canvas)

    def loop(self):
        if self.run is True:
            self.image_canvas.paste(self.image_background, (0, 0))
            self.warp_speed_effect.loop()
            self.warp_speed_effect.draw(self.draw, COLOR_VOLUME_BAR)
            self.draw_rfid()
            self.draw_volume()
            self.draw_action_image()
            self.draw_scroll_text()
            self.render_screen()
