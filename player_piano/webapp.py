import flask
import flask.ext.restless
from flask import ( Flask, render_template, request, redirect, abort, Response,
                    jsonify, make_response, session)
import mido
import base64
import os
import sys
import time
import json
from six.moves import queue
from autobahn.twisted.wamp import Application

from model import dbsession, Folder, Artist, Collection, Track, Playlist, PlaylistTrack

app = flask.Flask(__name__, static_folder="../static", static_url_path="/static")
wapp = Application()
app.config['HOST'] = '0.0.0.0'
app.config['PORT'] = 5000
app.config['THREAD_POOL_SIZE'] = 10
app.config['DEBUG'] = True
app.config['MIDI_STORE_PATH'] = os.path.join(os.path.split(os.path.realpath(__file__))[0], "midi_store")
print(app.config['MIDI_STORE_PATH'])

try:
    os.makedirs(app.config['MIDI_STORE_PATH'])
except OSError:
    pass

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


# Create the Flask-Restless API manager.
manager = flask.ext.restless.APIManager(app, session=dbsession)

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
@app.route('/library', defaults={'path':'/library'})
@app.route('/library/<path:path>')
@app.route('/queue', defaults={'path':'/queue'})
@app.route('/about', defaults={'path':'/about'})
@app.route('/upload', defaults={'path':'/upload'})
def index(path):    
    """Most pages redirect to this controller and relies on asynchronous page generation on the client"""
    return render_template("main.jinja2.html")
    

################################################################################
## Action api
################################################################################




if __name__ == "__main__":
    app.run(host='0.0.0.0')
