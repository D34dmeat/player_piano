"""An API for midish"""

import os
import pexpect
import threading
from collections import namedtuple
import time

import logging
logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger('player_piano.midi')


TrackPosition = namedtuple('TrackPosition', ['measure', 'beat', 'tick'])

class MidishException(Exception):
    pass

class MidiPlayThread(threading.Thread):
    def __init__(self, midi):
        self.midi = midi 
        self.__stop_requested = False
        threading.Thread.__init__(self)
    def stop(self):
        self.__stop_requested = True
        self.join()
    def run(self):
        # Play until the end, unless interrupted:
        while not self.__stop_requested:
            pos = self.midi._update_position()
            if pos.measure >= self.midi.track_length:
                self.midi._track_end()
                break
        log.debug("MidiPlayThread terminated")

class Midi(object):
    def __init__(self, library_path):
        self.library_path = library_path
        self.current_track = None
        self.current_pos = TrackPosition(0,0,0)
        self.track_length = 0
        self.play_thread = None

    def startup(self):
        cwd = os.getcwd()
        os.chdir(self.library_path)
        self.midish = pexpect.spawn('midish -v')
        os.chdir(cwd)
        self._update_position()
        self.midish.expect("\+ready")
        log.info("midish initialized")

    def load_track(self, name):
        self.midish.sendline('import "{}"'.format(name))
        # Tracks that load properly show the initialized position:
        try:
            self._update_position()
        except Exception:
            raise AssertionError("Could not load track: {}".format(name))
        self.midish.expect("\+ready")
        # Get the track length in measures
        self.midish.sendline("print [mend]")
        self.midish.expect('[0-9]+')
        self.track_length = int(self.midish.match.group())
        self.midish.expect("\+ready")
        log.info("Track loaded: {} - {} measures".format(name, self.track_length))

    def stop(self):
        if self.play_thread:
            self.play_thread.stop()
        self.midish.sendline("s")
        self.midish.expect("\+ready")
        log.info("Playback stopped")


    def pause(self):
        if self.play_thread:
            self.play_thread.stop()
        self.midish.sendline("i")
        self.midish.expect("\+ready")
        log.info("Playback Paused")

    def _track_end(self):
        """Track end event trigger from MidiPlayThread"""
        log.info("Track end")
        self.stop()

    def play(self):
        self.midish.sendline("p")
        self.midish.expect("\+ready")
        self.play_thread = MidiPlayThread(self)
        self.play_thread.start()
        log.info("Playback started")
        
    def _update_position(self, catch_exception=True):
        pats = ['\+pos ([0-9]+) ([0-9]+) ([0-9]+)']
        if catch_exception:
            pats.append('\+ready')
        index = self.midish.expect(pats)
        if index == 0:
            self.current_pos = TrackPosition(*[int(x) for x in self.midish.match.groups()])
        else:
            raise MidishException('expecting a track position, but got +ready instead')
        log.debug(self.current_pos)
        return self.current_pos

