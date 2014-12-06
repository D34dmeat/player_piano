import flask
import flask.ext.sqlalchemy
import flask.ext.restless
import json

app = flask.Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/player_piano.db'
db = flask.ext.sqlalchemy.SQLAlchemy(app)

playlists = db.Table('playlists',
                     db.Column('playlist_id', db.Integer, db.ForeignKey('playlist.id')),
                     db.Column('track_id', db.Integer, db.ForeignKey('track.id')),
                     db.Column('track_num', db.Integer))

class AppModel():
    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class Track(db.Model, AppModel):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode)
    filename = db.Column(db.Unicode)

class Playlist(db.Model, AppModel):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode, unique=True)
    tracks = db.relationship('PlaylistTrack', backref='playlist', lazy='dynamic', order_by='PlaylistTrack.order')

class PlaylistTrack(db.Model, AppModel):
    id = db.Column(db.Integer, primary_key=True)
    order = db.Column(db.Integer)
    playlist_id = db.Column(db.Integer, db.ForeignKey('playlist.id'))
    track_id = db.Column(db.Integer, db.ForeignKey('track.id'))

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

# Create the database tables.
db.create_all()

# Create the Flask-Restless API manager.
manager = flask.ext.restless.APIManager(app, flask_sqlalchemy_db=db)

# Create API endpoints, which will be available at /api/<tablename> by
# default. Allowed HTTP methods can be specified as well.
manager.create_api(Track, methods=['GET', 'POST', 'DELETE', 'PUT'],
                   preprocessors={
                       'DELETE': [pre_delete_track]
                   })
manager.create_api(Playlist, methods=['GET', 'POST', 'DELETE', 'PUT'],
                   postprocessors={
                       'GET_SINGLE': [post_get_playlist],
                       'GET_MANY': [post_get_playlist]
                   })

# start the flask loop
app.run()
