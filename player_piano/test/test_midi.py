from ..midi import Midi
import os
import time

def play_pause_test():
    m = Midi(library_path=os.path.expanduser("~/git/player_piano/midi_files"))
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

def play_test():
    m = Midi(os.path.expanduser("~/git/player_piano/midi_files"))
    m.load_track("test.mid")
    m.play()
    m.play_thread.join()
