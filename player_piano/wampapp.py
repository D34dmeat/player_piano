from autobahn.twisted.wamp import Application
from twisted.internet.defer import returnValue

#The DB model is a blocking API, but we should be fine as long as
#we're just doing primary key fetches here. We don't really expect
#more than one user anyway.
from model import Folder, Artist, Collection, Track, Playlist, PlaylistTrack

app = Application()

@app.register('player_piano.player.play')
def play(play_type=None, play_id=None, track_num=0):
    """Play the current queue, or clear the queue and play a fresh playlist/collection/track."""

    if play_type is None and play_id is None:
        # Don't queue anything, just play.
        yield app.session.call('player_piano.midi.play')
        return 

    if play_type not in ('collection', 'track', 'playlist'):
        raise AssertionError("invalid type for playing")


    yield app.session.call('player_piano.midi.clear')
    if play_type == 'track':
        yield app.session.call('player_piano.midi.add', play_id)
    elif play_type == 'collection':
        collection = Collection.query.get(play_id)
        for track in collection.tracks:
            yield app.session.call('player_piano.midi.add', track.id)

    if track_num > 0:
        yield app.session.call('player_piano.midi.set_next_track', track_num)

    yield app.session.call('player_piano.midi.play')


@app.register('player_piano.player.enqueue')
def enqueue(play_type, play_id):
    """Add a playlist/collection/track onto the end of the queue."""

    if play_type not in ('collection', 'track', 'playlist'):
        raise AssertionError("invalid type for playing")
    if play_type == 'track':
        yield app.session.call('player_piano.midi.play', play_id)
    elif play_type == 'collection':
        collection = Collection.query.get(play_id)
        for track in collection.tracks:
            yield app.session.call('player_piano.midi.add', track.id)

@app.register('player_piano.player.queue')
def queue():
    """Get the current play queue"""
    midi_details = yield app.session.call('player_piano.midi.get_current_track')
    track_data = None
    if midi_details['track_id'] is not None:
        track = Track.query.get(midi_details['track_id'])
        track_data = track.as_dict()
        track_data['collection'] = track.collection.as_dict()
        track_data['collection']['artist'] = track.collection.artist.as_dict()
        track_data.update(midi_details)
        
    midi_queue = yield app.session.call('player_piano.midi.get_queue')
    queue = []
    for t in midi_queue['tracks']:
        track = Track.query.get(t)
        q_track = track.as_dict()
        q_track['collection'] = track.collection.as_dict()
        q_track['collection']['artist'] = track.collection.artist.as_dict()
        queue.append(q_track)

    returnValue( {"current_track": track_data,
            "queue": queue})

@app.register('player_piano.player.clear_queue')
def clear_queue():
    yield app.session.call('player_piano.midi.clear')

@app.register('player_piano.player.stop')
def stop():
    """Stop playback"""
    yield app.session.call('player_piano.midi.stop')

@app.register('player_piano.player.pause')
def pause():
    """Pause playback"""
    yield app.session.call('player_piano.midi.pause')

@app.register('player_piano.player.next_track')
def next_track():
    """Play next track in queue"""
    yield app.session.call('player_piano.midi.next_track', force_play=True)

@app.register('player_piano.player.prev_track')
def prev_track():
    """Play previous track in queue"""
    yield app.session.call('player_piano.midi.prev_track', force_play=True)

@app.register('player_piano.player.play_queue_track')
def play_queue_track(track_num):
    """Play a track already in the queue"""
    yield app.session.call('player_piano.midi.stop')
    yield app.session.call('player_piano.midi.set_next_track', track_num)
    yield app.session.call('player_piano.midi.next_track', force_play=True)

@app.register('player_piano.player.register')
def restart_track():
    """Restart the current track in the queue from the beginning"""
    yield app.session.call('player_piano.midi.stop', sleep=1)
    yield app.session.call('player_piano.midi.play')
