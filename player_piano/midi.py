import os
import pexpect
import threading
from collections import namedtuple
import time
import json

from twisted.internet.defer import inlineCallbacks
from autobahn.twisted.util import sleep
from autobahn import wamp
from autobahn.twisted.wamp import ApplicationSession, ApplicationRunner



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
        if threading.current_thread() != self:
            self.join()

    def run(self):
        # Play until the end, unless interrupted:
        while not self.__stop_requested:
            pos = self.midi._update_position()
            if pos.measure >= self.midi.track_length:
                self.midi._track_end()
                break
        log.debug("MidiPlayThread terminated")

class MidiQueue(object):
    def __init__(self, name="untitled", publish_callback=None):
        self.name = name
        self.publish_callback = publish_callback
        self.midi = Midi(track_end_callback=self.next_track, position_update_callback=self.position_update_callback,
                         player_state_callback=self.player_state_callback)
        self.clear()

    def publish(self, message):
        if not self.publish_callback:
            raise AssertionError("No publish callback was registered.")
        self.publish_callback('player_piano.midi.event.{}'.format(message['type']), message)

    def position_update_callback(self, pos):
        self.publish({'type':'position_update',
                      'pos': {'measure': pos.measure,
                              'beat': pos.beat,
                              'tick': pos.tick}})

    def player_state_callback(self, state):
        """Notify player state change: playing, paused, stopped"""
        self.publish({'type':'player_state',
                            'state': state})

    @wamp.register(u'player_piano.midi.clear')
    def clear(self):
        self.midi.stop()
        self.name = "untitled"
        self.repeat = False
        self.current_track_num = -1
        self.queue = []
        self.state = "initialized"
        self.publish(self.get_player_state())

    @wamp.register(u'player_piano.midi.add')
    def add(self, track_id, position=None):
        if position is None:
            self.queue.append(track_id)
            log.info("Added {} to end of playlist (index {})".format(track_id, len(self.queue)-1))
        else:
            self.queue.insert(position, track_id)
            log.info("Added {} as index {} of playlist".format(track_id, position))

    @wamp.register(u'player_piano.midi.remove')
    def remove(self, position):
        if self.current_track_num == position:
            self.next_track()
        elif self.current_track_num > position:
            self.current_track_num -= 1
        self.queue.pop(position)

    @wamp.register(u'player_piano.midi.get_current_track')
    def get_current_track(self):
        if self.current_track_num < 0:
            track_id = None
        else:
            track_id = self.queue[self.current_track_num] 
        data = {"track_id": track_id,
                "track_length": self.midi.track_length,
                "current_track_num": self.current_track_num,
                "current_pos": dict(self.midi.current_pos._asdict())}
        return data

    @wamp.register(u'player_piano.midi.set_next_track')
    def set_next_track(self, track_num):
        # next_track() increments current_track_num, so set it one
        # lower than what it will become:
        self.current_track_num = track_num - 1
        log.info("Set current track: {}".format(self.current_track_num))

    @wamp.register(u'player_piano.midi.get_queue')
    def get_queue(self):
        return {'current_track_num': self.current_track_num,
                'tracks': self.queue}

    @wamp.register(u'player_piano.midi.get_player_state')
    def get_player_state(self):
        if self.current_track_num >= 0:
            track_id = self.queue[self.current_track_num]
        else:
            track_id = None
        return {"play_state": self.state,
                "type":"load_track",
                "track_id": track_id,
                "queue": self.get_queue(),
                "track_length": self.midi.track_length}

    @wamp.register(u'player_piano.midi.next_track')
    def next_track(self, force_play=False, **kw):
        self.midi.stop()
        time.sleep(2)
        if self.current_track_num >= len(self.queue)-1:
            if self.repeat or force_play:
                log.info("Queue finished, looping back to the beginning")
                self.current_track_num = -1
            else:
                log.info("Queue finished")
                self.state = "stopped"
                self.current_track_num = -1
                return

        self.current_track_num += 1
        log.info("Loading track index {} ...".format(self.current_track_num))
        self.midi.load_track(self.queue[self.current_track_num])
        self.publish(self.get_player_state())
        if self.state in ("playing",) or force_play:
            self.midi.play()

    @wamp.register(u'player_piano.midi.prev_track')
    def prev_track(self, force_play=False, **kw):
        # re-use next_track() by setting the current_track_num back two
        if self.current_track_num > 0:
            self.current_track_num -= 2
            self.next_track()
        else:
            # If this is the first track of the queue, just restart:
            self.midi.stop()
            self.midi.play()
        
    @wamp.register(u'player_piano.midi.play')
    def play(self):
        if self.state in ('paused', 'stopped'):
            if self.current_track_num >= 0:
                self.midi.play()
            else:
                self.next_track(force_play=True)
        elif self.state in ("finished", "initialized"):
            self.next_track(force_play=True)
        self.state = "playing"

    @wamp.register(u'player_piano.midi.stop')
    def stop(self, sleep=None):
        if sleep is not None:
            time.sleep(sleep)
        self.midi.stop()
        self.state = "stopped"

    @wamp.register(u'player_piano.midi.pause')
    def pause(self):
        self.midi.pause()
        self.state = "paused"

class Midi(object):
    """Low level midi interface via midish"""
    def __init__(self, track_end_callback=None, position_update_callback=None, 
                 player_state_callback=None, library_path=os.path.join(os.path.split(os.path.realpath(__file__))[0], "midi_store")):
        self.library_path = library_path
        self.current_track = None
        self.current_pos = TrackPosition(0,0,0)
        self.track_length = 0
        self.play_thread = None
        self.track_end_callback = track_end_callback
        self.position_update_callback = position_update_callback
        self.player_state_callback = player_state_callback
        self.player_state("stopped")
        self._startup()

    def _startup(self):
        cwd = os.getcwd()
        os.chdir(self.library_path)
        self.midish = pexpect.spawn('midish -v')
        os.chdir(cwd)
        self._update_position()
        self.midish.expect("\+ready")
        log.info("midish initialized")

    def load_track(self, track_id):
        self.stop()
        name = "{}.mid".format(track_id)
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
        self.current_track = name
        log.info("Track loaded: {} - {} measures".format(name, self.track_length))
        return self.track_length

    def player_state(self, state):
        self._playing_state = state
        if self.player_state_callback:
            self.player_state_callback(state)

    def stop(self):
        if self.play_thread:
            self.play_thread.stop()
        self.midish.sendline("s")
        self.midish.expect("\+ready")
        self.player_state("stopped")
        log.info("Playback stopped")

    def pause(self):
        if self.play_thread:
            self.play_thread.stop()
        self.midish.sendline("i")
        self.midish.expect("\+ready")
        self.player_state("paused")
        log.info("Playback Paused")

    def _track_end(self):
        """Track end event trigger when track finished playing through to the end"""
        log.info("Track end")
        self.stop()
        if self.track_end_callback:
            self.track_end_callback(current_track=self.current_track)

    def play(self):
        if self._playing_state == "playing":
            return
        self.midish.sendline("p")
        self.midish.expect("\+ready")
        log.info("Playback started for {}".format(self.current_track))
        self.play_thread = MidiPlayThread(self)
        self.play_thread.start()
        self.player_state("playing")
        
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
        if self.position_update_callback:
            self.position_update_callback(self.current_pos)
        return self.current_pos

class WampMidiQueue(ApplicationSession):
    @inlineCallbacks
    def onJoin(self, details): 
        midiqueue = MidiQueue(publish_callback=self.publish)            
        registrations = yield self.register(midiqueue)


def server():
    runner = ApplicationRunner("ws://127.0.0.1:5000/ws", "realm1")
    runner.run(WampMidiQueue)

if __name__ == "__main__":
    server()

