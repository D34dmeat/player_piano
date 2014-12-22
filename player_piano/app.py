import flask
import flask.ext.sqlalchemy
import flask.ext.restless
from flask import ( Flask, render_template, request, redirect, abort, Response,
                    jsonify, make_response, session)
import Pyro4
import base64
import os
import json

app = flask.Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///player_piano.db'
app.config['MIDI_STORE_PATH'] = 'midi_store'

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

artist_tracks = db.Table('artist_tracks',
                         db.Column('artist_id', db.Integer, db.ForeignKey('artist.id')),
                         db.Column('track_id', db.Integer, db.ForeignKey('track.id')))

artist_collections = db.Table('artist_collections',
                         db.Column('artist_id', db.Integer, db.ForeignKey('artist.id')),
                         db.Column('collection_id', db.Integer, db.ForeignKey('collection.id')))

class Artist(db.Model, AppModel):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode)
    tracks = db.relationship('Track', secondary=artist_tracks, backref=db.backref('artists', lazy='dynamic'))
    collections = db.relationship('Collection', secondary=artist_collections, backref=db.backref('artists', lazy='dynamic'))

class Collection(db.Model, AppModel):
    """Colection of tracks (eg. albumn, symphony)"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode)
    tracks = db.relationship('Track', backref='collection', lazy='dynamic')

class Track(db.Model, AppModel):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Unicode)
    collection_id = db.Column(db.Integer, db.ForeignKey('collection.id'))
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
        with open(os.path.join(app.config['MIDI_STORE_PATH'], '{}.mid'.format(instance_id)), "wb") as f:
            f.write(midi)
    del data['midi']

# Create the database tables.
db.create_all()

# Create the Flask-Restless API manager.
manager = flask.ext.restless.APIManager(app, flask_sqlalchemy_db=db)

# Create API endpoints, which will be available at /api/<tablename> by
# default. Allowed HTTP methods can be specified as well.
manager.create_api(Track, methods=['GET', 'POST', 'DELETE', 'PUT'],
                   preprocessors={
                       'DELETE': [pre_delete_track],
                       'PUT_SINGLE': [save_track_midi_data]
                   })
manager.create_api(Playlist, methods=['GET', 'POST', 'DELETE', 'PUT'],
                   postprocessors={
                       'GET_SINGLE': [post_get_playlist],
                       'GET_MANY': [post_get_playlist]
                   })
manager.create_api(Collection, methods=['GET', 'POST', 'DELETE', 'PUT'])
manager.create_api(Artist, methods=['GET', 'POST', 'DELETE', 'PUT'])


################################################################################
## Action api
################################################################################

@app.route('/api/player/play/<play_type>/<play_id>')
def play_track(play_type, play_id):
    """Clear the current playlist and load a playlist/collection/track."""
    if play_type not in ('collection', 'track', 'playlist'):
        return make_response(jsonify({"message":"invalid type for playing"}), 400)
    midi.clear()
    if play_type == 'track':
        midi.add(play_id)
    elif play_type == 'collection':
        collection = Collection.query.get(play_id)
        for track in collection.tracks:
            midi.add(track.id)
    midi.play()
    return jsonify({"status":"ok"})

@app.route('/api/player/status')
def status():
    midi_details = midi.get_current_track()
    track_data = None
    if midi_details['id'] is not None:
        track = Track.query.get(midi_details['id'])
        track_data = track.as_dict()
        track_data['collection'] = track.collection.as_dict()
        track_data['artists'] = [a.as_dict() for a in track.artists]
        track_data.update(midi_details)
        
    midi_playlist = midi.get_playlist()
    
    return jsonify({"current_track": track_data,
                    "playlist": midi_playlist})

@app.route('/api/player/stop')
def stop():
    """Stop playback"""
    midi.stop()
    return jsonify({"status":"ok"})

# start the flask loop
app.run()
