import Pyro4
import uuid
import logging
import threading
from six.moves import queue

log = logging.getLogger("midi_event_client")

class MidiEventQueue(threading.Thread):
    def __init__(self):
        self.midi_event_client = MidiEventClient(self.process_event)
        self.event_queue = queue.Queue()
        threading.Thread.__init__(self)

    def process_event(self, message):
        self.event_queue.put(message)

    def get_event(self, timeout=0.1):
        return self.event_queue.get(timeout=timeout)

    def stop(self):
        self.midi_event_client.abort = True
    
    def run(self):
        self.midi_event_client.process_events()

class MidiEventClient(object):
    def __init__(self, event_callback=None):
        self.client_id = uuid.uuid4()
        self.event_callback = event_callback
        self.abort = False
        log.info("Client initialized: {}".format(self.client_id))

    def event(self, message):
        log.info(message)
        if self.event_callback:
            self.event_callback(message)

    def process_events(self):
        daemon = Pyro4.core.Daemon()
        daemon.register(self)
        with Pyro4.core.Proxy("PYRONAME:midi") as server:
            server.subscribe(self.client_id, self)
        daemon.requestLoop(lambda: not self.abort)

if __name__ == "__main__":
    queue = MidiEventQueue()
    queue.start()
    while True:
        print(queue.get_event())
