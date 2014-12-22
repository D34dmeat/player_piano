import json
import os
import requests
import base64
import glob
from nose.tools import assert_equals

from player_piano.client import CRUD
    
def test_create_tracks_and_playlists():
    api = CRUD("http://localhost:5000/api")
    tracks = []
    for tnum in range(1,25):
        track = {
            'title': 'Track #{}'.format(tnum)
        }
        track = api.post('track', track)
        tracks.append(track)

    # Add midi data to tracks:
    test_midi_dir = os.path.join(os.path.split(os.path.realpath(__file__))[0], os.pardir, os.pardir, 'midi_files')
    test_midi_files = glob.glob(os.path.join(test_midi_dir, '*'))
    for n, track in enumerate(tracks):
        with open(test_midi_files[n%len(test_midi_files)], 'rb') as m:
            midi = m.read()
            midi = base64.b64encode(midi).decode("utf-8")
            api.put('track/{}'.format(track['id']), {'midi':midi, 'title':track['title']})

    # Get three pages:
    for page in range(3):
        for i, trk in enumerate(api.get('track?page={}'.format(page+1))['objects'], page*10):
            assert_equals(tracks[i]['title'], trk['title'])
    # Fourth page is empty:
    assert_equals(api.get('track?page=4')['objects'], [])

    # Delete the third page:
    assert_equals(api.delete('track/21'), True)
    assert_equals(api.delete('track/22'), True)
    assert_equals(api.delete('track/23'), True)
    assert_equals(api.delete('track/24'), True)
    assert_equals(api.get('track?page=3')['objects'], [])
    

    # Create a playlist containing tracks 0-3:
    playlist = api.post('playlist', {'name':'Test playlist', 'tracks':[{"track_id":3, "order":1},{"track_id":2, "order":2},{"track_id":1, "order":3},{"track_id":4, "order":4}]})
    # Reverse the tracks:
    playlist = api.put('playlist/{}'.format(playlist['id']), {"tracks":[{"track_id":3, "order":4},{"track_id":2, "order":3},{"track_id":1, "order":2},{"track_id":4, "order":1}]})
    # Add a new track :
    playlist = api.put('playlist/{}'.format(playlist['id']), {"tracks":[{"track_id":3, "order":4},{"track_id":2, "order":3},{"track_id":1, "order":2},{"track_id":4, "order":1}, {"track_id":5, "order":5}]})

    #Delete track 1-4 which is part of our playlist:
    api.delete('track/1')
    api.delete('track/2')
    api.delete('track/3')
    api.delete('track/4')
    playlist = api.get('playlist/1')
    assert_equals(len(playlist['tracks']), 1)
    assert_equals(playlist['tracks'][0]['track_id'], 5)

