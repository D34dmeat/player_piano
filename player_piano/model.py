import flask.ext.sqlalchemy

from sqlalchemy import Table, Column, Date, DateTime, Float, Integer, Unicode
from sqlalchemy import ForeignKey
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import backref, relationship
from sqlalchemy.orm import scoped_session, sessionmaker
import os.path

db_uri = 'sqlite:///{}'.format(os.path.join(os.path.split(os.path.realpath(__file__))[0], "player_piano.db"))
print(db_uri)
engine = create_engine(db_uri, convert_unicode=True)
Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
dbsession = scoped_session(Session)
Base = declarative_base()
Base.metadata.bind = engine


# playlists = Table('playlists',
#                      Column('playlist_id', Integer, ForeignKey('playlist.id')),
#                      Column('track_id', Integer, ForeignKey('track.id')),
#                      Column('track_num', Integer))

class AppModel():
    class Query(object):
        def __get__(self, obj, type):
            return dbsession.query(type)
    query = Query()

    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class Folder(Base, AppModel):
    __tablename__ = "folder"
    id = Column(Integer, primary_key=True)
    name = Column(Unicode)
    artists = relationship('Artist', backref='folder', lazy='dynamic', order_by='Artist.name')

class Artist(Base, AppModel):
    __tablename__ = "artist"
    id = Column(Integer, primary_key=True)
    name = Column(Unicode)
    collections = relationship('Collection', backref='artist', lazy='dynamic', order_by='Collection.name')
    folder_id = Column(Integer, ForeignKey('folder.id'), nullable=False)

class Collection(Base, AppModel):
    __tablename__ = "collection"
    """Colection of tracks (eg. albumn, symphony)"""
    id = Column(Integer, primary_key=True)
    name = Column(Unicode)
    tracks = relationship('Track', backref='collection', lazy='dynamic', order_by='Track.collection_order')
    artist_id = Column(Integer, ForeignKey('artist.id'))

class Track(Base, AppModel):
    __tablename__ = "track"
    id = Column(Integer, primary_key=True)
    title = Column(Unicode)
    collection_id = Column(Integer, ForeignKey('collection.id'), nullable=False)
    collection_order = Column(Integer, nullable=False)
    length = Column(Integer)
    human_tempo = Column(Unicode)
    midi = None

class Playlist(Base, AppModel):
    __tablename__ = "playlist"
    id = Column(Integer, primary_key=True)
    name = Column(Unicode, unique=True)
    tracks = relationship('PlaylistTrack', backref='playlist', lazy='dynamic', order_by='PlaylistTrack.order')

class PlaylistTrack(Base, AppModel):
    __tablename__ = "playlisttrack"
    id = Column(Integer, primary_key=True)
    order = Column(Integer)
    playlist_id = Column(Integer, ForeignKey('playlist.id'))
    track_id = Column(Integer, ForeignKey('track.id'))


Base.metadata.create_all()
