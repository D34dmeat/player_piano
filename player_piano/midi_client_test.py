import Pyro4
import uuid

class CallbacksHandler(object):
    def __init__(self):
        self.client_id = uuid.uuid4()
        print("Client initialized: {}".format(self.client_id))

    def event(self, message):
        print(message)

daemon = Pyro4.core.Daemon()
callback = CallbacksHandler()
daemon.register(callback)
        
with Pyro4.core.Proxy("PYRONAME:midi") as server:
    print("subscribe...")
    server.subscribe(callback.client_id, callback)
    print("subscribed.")

print("Waiting for events...")
daemon.requestLoop()
