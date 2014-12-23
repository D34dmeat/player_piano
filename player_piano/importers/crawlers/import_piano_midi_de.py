"""Import previously scraped piano-midi.de midi files"""

import json
import re
import base64
from player_piano.client import CRUD

def main():
    api = CRUD()
    with open("midipiano_de.items.json") as f:
        data = json.loads(f.read(), "utf-8")

    folder = api.post('folder', {'name':'Classical'})

    for artist in data:
        artist_name = re.sub('[ ]+', ' ', artist['name'])
        print(artist_name)

        artist_obj = api.post('artist', {'name': artist_name, 'folder':{'id':folder['id']}})
        
        for playlist in artist['playlists']:
            pl_title = playlist['title']
            print("\t"+pl_title)

            collection = api.post('collection', {'name':pl_title, 'artist':{'id':artist_obj['id']}})

            for num, t in enumerate(playlist['tracks']):
                t_title = t['title']
                print("\t\t"+t_title)
                track = {'title': t_title, 'collection': {'id': collection['id']}, 'collection_order':num}
                if 'length' in t.keys():
                    track['length'] = t['length']
                if 'tempo' in t.keys():
                    track['human_tempo'] = t['tempo']
                track = api.post('track', track)
                with open("www.piano-midi.de/"+t['midi_url'], 'rb') as f:
                    midi = base64.b64encode(f.read()).decode("utf-8")
                track = api.put('track/{}'.format(track['id']), {'midi': midi})
                
                
                

if __name__ == "__main__":
    main()
