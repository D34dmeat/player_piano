from ..midi import Midi
import os
import time

def play_pause_test():
    m = Midi(os.path.expanduser("~/git/player_piano/midi_files"))
    m.startup()
    m.load_track("test.mid")
    m.play()
    time.sleep(5)
    m.pause()
    time.sleep(5)
    m.play()
    time.sleep(2)
    m.pause()
    time.sleep(2)
    m.play()
    time.sleep(5)
    m.stop()
