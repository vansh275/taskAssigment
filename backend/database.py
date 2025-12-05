from sqlalchemy import create_engine,Column,String,Integer,DateTime,Text,func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import json

engine=create_engine("sqlite:///site.db", connect_args={"check_same_thread": False})

SessionLocal=sessionmaker(bind=engine,autoflush=False,autocommit=False)
Base=declarative_base()

class Track(Base):
    __tablename__="tracks"
    id=Column(Integer,primary_key=True)
    name=Column(String,nullable=False)
    used=Column(Integer,nullable=False)
    genre=Column(String,nullable=False)
    file_path = Column(String, nullable=False)

    def to_dict(self):
        return{
            "id":self.id,
            "name":self.name,
            # "used":self.used,
            "file_path": self.file_path,
            "genre":self.genre
        }
    def get_used(self):
        return{
            "name":self.name,
            "used":self.used
        }
    
class Playlist(Base):
    __tablename__="playlists"
    id=Column(Integer,primary_key=True)
    mood_prompt=Column(String,nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    tracks_json=Column(Text,nullable=False)

    def set_tracks(self,tracks:list):
        self.tracks_json=json.dumps(tracks)
    def get_tracks(self):
        return json.loads(self.tracks_json)
