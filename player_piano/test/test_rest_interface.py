import json
import requests
from nose.tools import assert_equals

APP_URL = "http://localhost:5000/api/"

def post(query, data):
    r = requests.post(APP_URL + query,
                  data=json.dumps(data),
                  headers={'content-type': 'application/json'}
              )
    return json.loads(r.content)

def get(query):
    r = requests.get(APP_URL + query,
                 headers={'content-type': 'application/json'}
             )
    return json.loads(r.content)

def put(query, data):
    r = requests.put(APP_URL + query,
                  data=json.dumps(data),
                  headers={'content-type': 'application/json'}
              )
    return json.loads(r.content)

def delete(query):
    r = requests.delete(APP_URL + query,
                  headers={'content-type': 'application/json'}
              )
    return r.status_code == 204
    
    
def test_create_tracks_and_playlists():
    tracks = []
    for tnum in range(1,25):
        track = {
            'name': 'Track #{}'.format(tnum),
            'filename': 'track{}.mid'.format(tnum)
        }
        post('track', track)
        tracks.append(track)
        
    # Get three pages:
    for page in range(3):
        for i, trk in enumerate(get('track?page={}'.format(page+1))['objects'], page*10):
            assert_equals(tracks[i]['name'], trk['name'])
            assert_equals(tracks[i]['filename'], trk['filename'])
    # Fourth page is empty:
    assert_equals(get('track?page=4')['objects'], [])

    # Delete the third page:
    assert_equals(delete('track/21'), True)
    assert_equals(delete('track/22'), True)
    assert_equals(delete('track/23'), True)
    assert_equals(delete('track/24'), True)
    assert_equals(get('track?page=3')['objects'], [])
    

    # Create a playlist containing tracks 0-3:
    playlist = post('playlist', {'name':'Test playlist', 'tracks':[{"track_id":3, "order":1},{"track_id":2, "order":2},{"track_id":1, "order":3},{"track_id":4, "order":4}]})
    # Reverse the tracks:
    playlist = put('playlist/{}'.format(playlist['id']), {"tracks":[{"track_id":3, "order":4},{"track_id":2, "order":3},{"track_id":1, "order":2},{"track_id":4, "order":1}]})
    # Add a new track :
    playlist = put('playlist/{}'.format(playlist['id']), {"tracks":[{"track_id":3, "order":4},{"track_id":2, "order":3},{"track_id":1, "order":2},{"track_id":4, "order":1}, {"track_id":5, "order":5}]})

    #Delete track 1-4 which is part of our playlist:
    delete('track/1')
    delete('track/2')
    delete('track/3')
    delete('track/4')
    playlist = get('playlist/1')
    assert_equals(len(playlist['tracks']), 1)
    assert_equals(playlist['tracks'][0]['track_id'], 5)
