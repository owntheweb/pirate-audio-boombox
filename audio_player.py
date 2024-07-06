import pygame
import os
import math


class AudioPlayer:
    def __init__(
            self,
            audio_dir='/home/pi/Music',
            max_volume=0.8,
            on_load_song=None
    ):
        self.audio_dir = audio_dir
        self.max_volume = max_volume
        self.on_load_song = on_load_song
        self.rfid_uid = ''
        self.playlist_data = {
            'id': '',
            'items': []
        }
        self.playlist_index = 0
        self.paused = False

        # Prevent pygame from displaying game window in terminal, run headless
        os.environ['SDL_VIDEODRIVER'] = 'dummy'

        # Initialize Pygame
        pygame.init()

        # listen for song end events to play next song in playlist
        self.music_end_event = pygame.USEREVENT + 1
        pygame.mixer.music.set_endevent(self.music_end_event)

    def set_playlist(self, playlist_data):
        self.playlist_data = playlist_data
        self.playlist_index = 0
        self.paused = False
        self.load_song(playlist_data['items'][self.playlist_index]['file'])
        self.play_song()

    def load_song(self, fileName):
        try:
            pygame.mixer.music.load(self.audio_dir + '/' + fileName)
            if self.on_load_song:
                self.on_load_song()
        except pygame.error as e:
            print('error loading song')
            print(e)

    def play_song(self):
        pygame.mixer.music.play()

    def stop_song(self):
        pygame.mixer.music.stop()

    def pause_song(self):
        if self.paused is False:
            pygame.mixer.music.pause()
            self.paused = True

    def unpause_song(self):
        if self.paused is True:
            pygame.mixer.music.unpause()
            self.paused = False

    def toggle_pause(self):
        if self.paused is False:
            pygame.mixer.music.pause()
            self.paused = True
        else:
            pygame.mixer.music.unpause()
            self.paused = False

        return self.paused

    def next_song(self):
        self.playlist_index += 1
        self.paused = False
        self.stop_song()
        if self.playlist_index > len(self.playlist_data['items']) - 1:
            self.playlist_index = 0
        self.load_song(
            self.playlist_data['items'][self.playlist_index]['file']
        )
        self.play_song()

    def prev_song(self):
        if pygame.mixer.music.get_pos() >= 2000:
            # set pos to beginning of song on first press
            self.paused = False
            self.stop_song()
            self.load_song(
                self.playlist_data['items'][self.playlist_index]['file']
            )
            self.play_song()
        else:
            # pos already moved to beginning of song, play previous song
            self.playlist_index -= 1
            self.paused = False
            self.stop_song()
            if self.playlist_index < 0:
                self.playlist_index = 0
            self.load_song(
                self.playlist_data['items'][self.playlist_index]['file']
            )
            self.play_song()

    def set_volume(self, volume):
        # thanks!:
        # https://probesys.blogspot.com/2011/10/useful-math-functions.html
        eased_volume = 0.0
        if volume < 0.0:
            eased_volume = 0.0
        elif volume > 1.0:
            eased_volume = 1.0
        else:
            eased_volume = math.sin(volume * (math.pi / 2.0))

        pygame.mixer.music.set_volume(eased_volume * self.max_volume)

    def loop(self):
        for event in pygame.event.get():
            if event.type == self.music_end_event:
                print('song ended!')
                self.next_song()
