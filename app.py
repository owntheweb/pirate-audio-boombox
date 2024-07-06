import socket
import RPi.GPIO as GPIO
from pn532pi import Pn532, pn532, Pn532Hsu
import board
import busio
import adafruit_ads1x15.ads1015 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
from pirate_audio_display import PirateAudioDisplay
from audio_player import AudioPlayer
from rfid_library import RfidLibrary
import time

AUDIO_DIR = '/home/chris/experiments/audio'
DATA_DIR = '/home/chris/experiments/data'
FONT_DIR = '/home/chris/experiments/fonts'
IMAGE_DIR = '/home/chris/experiments/images'
MAX_VOLUME = 0.5  # The super bass songs will kill app with cheap USB battery


class App():
    def __init__(self):
        # Setup RPi.GPIO with the "BCM" numbering scheme
        GPIO.setmode(GPIO.BCM)

        self.active_rfid_uid = ''
        self.last_rfid_scan = time.time() - 10000

        self.setup_rfid()
        self.setup_volume()
        self.setup_display()
        self.setup_audio_player()
        self.setup_rfid_library()
        self.setup_buttons()

    def setup_buttons(self):
        # The buttons on Pirate Audio are connected to pins 5, 6, 16 and 24
        # Boards prior to 23 January 2020 used 5, 6, 16 and 20 
        # try changing 24 to 20 if your Y button doesn't work.
        self.buttons = [5, 6, 16, 24]

        # These correspond to buttons A, B, X and Y respectively
        self.button_labels = ['A', 'B', 'X', 'Y']

        # Buttons connect to ground when pressed, so we should set them up
        # with a "PULL UP", which weakly pulls the input signal to 3.3V.
        GPIO.setup(self.buttons, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        # Loop through out buttons and attach the "handle_button" function to
        # each. We're watching the "FALLING" edge (transition from 3.3V to
        # Ground) and picking a generous bounce time of 200ms to smooth out
        # button presses.
        for pin in self.buttons:
            GPIO.add_event_detect(
                pin,
                GPIO.FALLING,
                self.handle_button,
                bouncetime=200
            )

    def setup_rfid(self):
        PN532_HSU = Pn532Hsu(0)
        self.nfc = Pn532(PN532_HSU)
        self.nfc.begin()

        version_data = self.nfc.getFirmwareVersion()
        if not version_data:
            print("Didn't find PN53x board")
            raise RuntimeError("Didn't find PN53x board")  # halt
        print("Found chip PN5 {:#x} Firmware ver. {:d}.{:d}".format(
            (version_data >> 24) & 0xFF,
            (version_data >> 16) & 0xFF,
            (version_data >> 8) & 0xFF)
        )
        # 0xFF = 255 retries, 0x0A = 10 retries, 0x00 = no retries, just scan
        # once as we loop
        # retries in general == added lag in the app
        self.nfc.setPassiveActivationRetries(0x00)
        # setup for RFID
        self.nfc.SAMConfig()

    def setup_volume(self):
        # analogue volume potentiometer to Pi-supported digital
        # reading through ADC
        i2c = busio.I2C(board.SCL, board.SDA)
        ads = ADS.ADS1015(i2c)
        self.volume_pot = AnalogIn(ads, ADS.P0)

    def setup_display(self):
        self.display = PirateAudioDisplay(
            font_dir=FONT_DIR,
            image_dir=IMAGE_DIR
        )

    def setup_audio_player(self):
        self.audio = AudioPlayer(
            audio_dir=AUDIO_DIR,
            max_volume=MAX_VOLUME,
            on_load_song=self.handle_on_song_loaded
        )

    def setup_rfid_library(self):
        self.rfid_library = RfidLibrary(data_dir=DATA_DIR)

    def make_audio_scroll_text(self):
        track_data = self.audio.playlist_data['items'][
            self.audio.playlist_index
        ]
        return (
            track_data['title'] +
            ' by ' +
            track_data['author'] +
            ', Album: ' +
            track_data['album']
        )

    # "handle_button" will be called every time a button is pressed
    # It receives one argument: the associated input pin.
    def handle_button(self, pin):
        label = self.button_labels[self.buttons.index(pin)]
        music_active = (
            self.active_rfid_uid != '' and
            hasattr(self.audio.playlist_data, 'items') and
            len(self.audio.playlist_data['items']) > 0
        )
        print("Button press detected on pin: {} label: {}".format(pin, label))
        if label == 'A' and music_active:
            paused = self.audio.toggle_pause()
            if paused:
                self.display.set_scroll_text('')
                self.display.set_action_image('pause')
            else:
                scroll_text = self.make_audio_scroll_text()
                self.display.set_scroll_text(scroll_text)
                self.display.set_action_image('play')
        elif label == 'X':
            # TEMP
            ip = self.get_local_ip()
            self.display.set_rfid(ip)
        # TODO: hmm Y and B may be reversed in code
        elif label == 'Y' and music_active:
            self.audio.next_song()
            scroll_text = self.make_audio_scroll_text()
            self.display.set_scroll_text(scroll_text)
            self.display.set_action_image('next')
        elif label == 'B' and music_active:
            self.audio.prev_song()
            scroll_text = self.make_audio_scroll_text()
            self.display.set_scroll_text(scroll_text)
            self.display.set_action_image('previous')

    def handle_rfid_scan(self, uid):
        if self.active_rfid_uid != uid:
            self.active_rfid_uid = uid
            print(uid)
            data = self.rfid_library.get_data(uid)
            if data:
                self.audio.set_playlist(data)
                scroll_text = self.make_audio_scroll_text()
                self.display.set_scroll_text(scroll_text)
                self.display.set_action_image('cartridge')
            else:
                self.audio.stop_song()
                self.display.set_rfid(uid)
                self.display.set_scroll_text('')
        elif self.active_rfid_uid != 'EMPTY':
            # in case cartridge signal was temporarily lost,
            # unpause audio and continue (if paused)
            self.audio.unpause_song()

    def get_local_ip(self):
        try:
            # Attempt to connect to an arbitrary IP on the internet
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))  # Using Google DNS IP and port
            ip = s.getsockname()[0]
            s.close()
        except Exception as e:
            ip = "Error: " + str(e)
        return ip

    def normalized_volume(self, pot_value):
        max_value = 26400
        normalized = round(pot_value / max_value, 2)
        return normalized

    def handle_on_song_loaded(self):
        self.display.set_scroll_text('')
        scroll_text = self.make_audio_scroll_text()
        self.display.set_scroll_text(scroll_text)

    def loop(self):
        # act on scanned RFID changes
        success, uid = self.nfc.readPassiveTargetID(
            pn532.PN532_MIFARE_ISO14443A_106KBPS
        )
        if success:
            self.last_rfid_scan = time.time()
            self.handle_rfid_scan(uid.hex())
        elif time.time() - self.last_rfid_scan > 0.2:
            if self.active_rfid_uid == 'EMPTY':
                return
            # rfid cartridge removed (maybe), pause music
            # sometimes scanner looses rfid, so give it time before
            # completely stopping
            self.audio.pause_song()

            # pause animation of sorts:
            print('.', end="", flush=True)
            if time.time() - self.last_rfid_scan > 3:
                # reset music, wait for next cartridge
                self.audio.stop_song()
                self.active_rfid_uid = 'EMPTY'
                print('EMPTY')
                self.display.set_scroll_text('')

        volume = self.normalized_volume(self.volume_pot.value)
        self.audio.set_volume(volume)
        self.display.set_volume(volume)

        self.display.loop()
        self.audio.loop()


print('here we go...')
app = App()

while True:
    app.loop()
