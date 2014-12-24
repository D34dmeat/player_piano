import flask
import flask.ext.sqlalchemy
import flask.ext.restless
from flask import ( Flask, render_template, request, redirect, abort, Response,
                    jsonify, make_response, session)
from flask.ext.uwsgi_websocket import WebSocket
import Pyro4
import mido
import base64
import os
import time
import json

from midi_event_client import MidiEventQueue

app = flask.Flask(__name__, static_folder="../static", static_url_path="/static")
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///player_piano.db'
app.config['MIDI_STORE_PATH'] = 'midi_store'
ws = WebSocket(app)

try:
    os.makedirs(app.config['MIDI_STORE_PATH'])
except OSError:
    pass

midi = Pyro4.Proxy("PYRONAME:midi")

db = flask.ext.sqlalchemy.SQLAlchemy(app)

playlists = db.Table('playlists',
                     db.Column('playlist_id', db.Integer, db.ForeignKey('playlist.id')),
                     db.Column('track_id', db.Integer, db.ForeignKey('track.id')),
                     db.Column('track_num', db.Integer))

class AppModel():
    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class Folder(db.Model, AppModel):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode)
    artists = db.relationship('Artist', backref='folder', lazy='dynamic', order_by='Artist.name')

class Artist(db.Model, AppModel):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode)
    collections = db.relationship('Collection', backref='artist', lazy='dynamic', order_by='Collection.name')
    folder_id = db.Column(db.Integer, db.ForeignKey('folder.id'), nullable=False)

class Collection(db.Model, AppModel):
    """Colection of tracks (eg. albumn, symphony)"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode)
    tracks = db.relationship('Track', backref='collection', lazy='dynamic', order_by='Track.collection_order')
    artist_id = db.Column(db.Integer, db.ForeignKey('artist.id'))

class Track(db.Model, AppModel):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Unicode)
    collection_id = db.Column(db.Integer, db.ForeignKey('collection.id'), nullable=False)
    collection_order = db.Column(db.Integer, nullable=False)
    length = db.Column(db.Integer)
    human_tempo = db.Column(db.Unicode)
    midi = None

class Playlist(db.Model, AppModel):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode, unique=True)
    tracks = db.relationship('PlaylistTrack', backref='playlist', lazy='dynamic', order_by='PlaylistTrack.order')

class PlaylistTrack(db.Model, AppModel):
    id = db.Column(db.Integer, primary_key=True)
    order = db.Column(db.Integer)
    playlist_id = db.Column(db.Integer, db.ForeignKey('playlist.id'))
    track_id = db.Column(db.Integer, db.ForeignKey('track.id'))

################################################################################
## Data API
################################################################################


def post_get_playlist(result, **kw):
    """Eagerly load the track information after requesting a playlist"""
    if result and 'tracks' in result:
        for playlist_track in result['tracks']:
            track = Track.query.filter_by(id=playlist_track['track_id']).first()
            if track:
                playlist_track['track'] = track.as_dict()

def pre_delete_track(instance_id, **kw):
    # Delete track from playlists:
    for playlist_track in PlaylistTrack.query.filter_by(track_id=instance_id):
        db.session.delete(playlist_track)

def save_track_midi_data(instance_id, data, **kw):
    midi = base64.b64decode(data.get('midi', None))
    if midi:
        midi_path = os.path.join(app.config['MIDI_STORE_PATH'], '{}.mid'.format(instance_id))
        with open(midi_path, "wb") as f:
            f.write(midi)
        if 'length' not in data.keys():
            mido_midi = mido.MidiFile(midi_path)
            data['length'] = round(mido_midi.length)
    del data['midi']

# Create the database tables.
db.create_all()

# Create the Flask-Restless API manager.
manager = flask.ext.restless.APIManager(app, flask_sqlalchemy_db=db)

# Create API endpoints, which will be available at /api/<tablename> by
# default. Allowed HTTP methods can be specified as well.
manager.create_api(Track, methods=['GET', 'POST', 'DELETE', 'PUT'], 
                   max_results_per_page=0,
                   results_per_page=0,
                   preprocessors={
                       'DELETE': [pre_delete_track],
                       'PUT_SINGLE': [save_track_midi_data]
                   })
manager.create_api(Playlist, methods=['GET', 'POST', 'DELETE', 'PUT'],
                   max_results_per_page=0,
                   results_per_page=0,
                   postprocessors={
                       'GET_SINGLE': [post_get_playlist],
                       'GET_MANY': [post_get_playlist]
                   })
manager.create_api(Collection, methods=['GET', 'POST', 'DELETE', 'PUT'],
                   max_results_per_page=0,
                   results_per_page=0,
)
manager.create_api(Artist, methods=['GET', 'POST', 'DELETE', 'PUT'],
                   max_results_per_page=0,
                   results_per_page=0,
)
manager.create_api(Folder, methods=['GET', 'POST', 'DELETE', 'PUT'],
                   max_results_per_page=0,
                   results_per_page=0,
)


################################################################################
## Views
################################################################################

@app.route('/', defaults={'path':'/'})
@app.route('/<path:path>')
def index(path):    
    """Most pages redirect to this controller and relies on asynchronous page generation on the client"""
    return render_template("main.jinja2.html")
    
# @app.route('/queue')
# def view_queue():
#     return render_template("queue.jinja2.html")

# @app.route('/library')
# @app.route('/library/folder/<int:folder_id>/<name>')
# @app.route('/library/folder/<int:folder_id>/artist/<int:artist_id>/<name>')
# @app.route('/library/folder/<int:folder_id>/collection/<int:collection_id>/<name>')
# def view_library_browse(play_type=None, folder_id=None, play_id=None, artist_id=None, collection_id=None, name=None):
#     links = []
#     title = ""
#     show_tracks = False
#     tracks_type = None

#     if collection_id is not None:
#         collection = Collection.query.get(collection_id)
#         artist = collection.artist
#         folder = Folder.query.get(folder_id)
#         for track in collection.tracks:
#             links.append({'type':'track', 
#                           'name':track.title, 
#                           'collection':collection.id, 
#                           'track_id': track.id, 
#                           'length':"%i:%02i" % (track.length/60, track.length%60), 
#                           'collection_order':track.collection_order
#                       })
#             title = '<a href="/library">Library</a> / <a href="/library/folder/{folder_id}/{folder_name}">{folder_name}</a> / <a href="/library/folder/{folder_id}/artist/{artist_id}/{artist_name}">{artist_name}</a> / {collection_name}'.format(
#                 folder_id=folder.id, folder_name=folder.name, artist_id=artist.id, artist_name=artist.name, collection_name=collection.name)
#             tracks_type = 'collection'
#             show_tracks = True
            
#     elif artist_id is not None:
#         artist = Artist.query.get(artist_id)
#         folder = Folder.query.get(folder_id)
#         for collection in artist.collections:
#             links.append({'type':'collection', 
#                           'name':collection.name, 
#                           'href': '/library/folder/{}/collection/{}/{}'.format(folder.id,collection.id,collection.name)
#                       })
#             title = '<a href="/library">Library</a> / <a href="/library/folder/{folder_id}/{folder_name}">{folder_name}</a> / {artist_name}'.format(
#                 folder_id=folder.id, folder_name=folder.name, artist_name=artist.name)
#     elif folder_id is not None:
#         folder = Folder.query.get(folder_id)
#         for artist in folder.artists:
#             links.append({'type':'artist', 'name':artist.name, 'href': '/library/folder/{}/artist/{}/{}'.format(folder.id,artist.id,artist.name)})
#             title = '<a href="/library">Library</a> / {}'.format(folder.name)
#     else:
#         folders = Folder.query.all()
#         for folder in folders:
#             links.append({'type':'folder', 'name':folder.name, 'href': '/library/folder/{}/{}'.format(folder.id,folder.name)})
#             title = 'Library'
            

#     return render_template("library.jinja2.html", title=title, links=links, show_tracks=show_tracks, tracks_type=tracks_type)


# @app.route('/library/<play_type>/<int:play_id>/<name>')
# def view_library_direct(play_type=None, folder_id=None, play_id=None, artist_id=None, collection_id=None, name=None):
#     links = []
#     title = ""
    
#     if play_id is not None:
#         # Direct link to folder, artist, or collection without going
#         # through the library hierarchy
#         if play_type == 'folder':
#             folder = Folder.query.get(play_id)
#             for artist in folder.artists:
#                 links.append({'type':'artist', 'name': artist.name, 'href': '/library/artist/{}/{}'.format(artist.id,artist.name)})
#         elif play_type == 'artist':
#             thing = Artist.query.get(play_id)
#         elif play_type == 'collection':
#             thing = Collection.query.get(play_id)
#             return render_template("library.jinja2.html", title=title, links=links)


################################################################################
## Action api
################################################################################
@app.route('/api/player/play', methods=['POST'])
def replace_queue():
    """Play the current queue, or clear the queue and play a fresh playlist/collection/track."""
    
    data = request.get_json()
    if data.get('id', None) is None:
        # Don't queue anything, just play.
        midi.play()
        return jsonify({"status": "ok"})

    if data['type'] not in ('collection', 'track', 'playlist'):
        return make_response(jsonify({"message":"invalid type for playing"}), 400)
    midi.clear()
    if data['type'] == 'track':
        midi.add(data.get('id'))
    elif data['type'] == 'collection':
        collection = Collection.query.get(data.get('id'))
        for track in collection.tracks:
            midi.add(track.id)

    track_num = data.get('track_num', 0)
    if track_num > 0:
        midi.set_next_track(track_num)

    midi.play()
    return jsonify({"status":"ok"})

@app.route('/api/player/enqueue', methods=['POST'])
def enqueue():
    """Add a playlist/collection/track onto the end of the queue."""

    data = request.get_json()
    if data.get('type', None) not in ('collection', 'track', 'playlist'):
        return make_response(jsonify({"message":"invalid type for playing"}), 400)
    if data.get('type') == 'track':
        midi.add(data.get('id'))
    elif data.get('type') == 'collection':
        collection = Collection.query.get(data.get('id'))
        for track in collection.tracks:
            midi.add(track.id)
    return jsonify({"status":"ok"})

@app.route('/api/player/queue')
def queue():
    midi_details = midi.get_current_track()
    track_data = None
    if midi_details['track_id'] is not None:
        track = Track.query.get(midi_details['track_id'])
        track_data = track.as_dict()
        track_data['collection'] = track.collection.as_dict()
        track_data['collection']['artist'] = track.collection.artist.as_dict()
        track_data.update(midi_details)
        
    midi_queue = midi.get_queue()
    queue = []
    for t in midi_queue['tracks']:
        track = Track.query.get(t)
        q_track = track.as_dict()
        q_track['collection'] = track.collection.as_dict()
        q_track['collection']['artist'] = track.collection.artist.as_dict()
        queue.append(q_track)

    return jsonify({"current_track": track_data,
                    "queue": queue})

@app.route('/api/player/stop', methods=['POST'])
def stop():
    """Stop playback"""
    midi.stop()
    return jsonify({"status":"ok"})


@ws.route('/api/player/events')
def events(ws):
    current_track = midi.get_current_track()
    current_track['type'] = 'load_track'
    current_track.pop('current_pos', None)
    if current_track['track_id'] != None:
        ws.send(json.dumps(current_track))
        
    midi_event_queue = MidiEventQueue()
    midi_event_queue.start()
    while True:
        ws.send(json.dumps(midi_event_queue.get_event()))

# start the flask loop
if __name__ == "__main__":
    app.run(host='0.0.0.0', threads=16)
