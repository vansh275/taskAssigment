from fastapi import FastAPI, Request,UploadFile,File,Form,Depends,HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
import os,shutil,json,mutagen
from .database import Base,engine,SessionLocal,Track,Playlist
from sqlalchemy.orm import session
from pydantic import BaseModel
from google import genai
from google.genai.errors import APIError
from dotenv import load_dotenv
from .caching import add_track_to_all,is_track_present,set_all_tracks,get_all_tracks,get_all_cache,get_top_tracks,set_top_tracks

load_dotenv()

app = FastAPI()
client=genai.Client()

BASE_DIR=Path(__file__).resolve().parent.parent
TRACK_DIR=os.path.join(BASE_DIR,"tracks")

if not os.path.exists(TRACK_DIR):
    os.makedirs(TRACK_DIR)

def get_db():
    db=SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_all_tracks_from_db(db:session):
    all_tracks=db.query(Track).all()
    all_tracks_list=[track.to_dict() for track in all_tracks]
    return all_tracks_list

def save_track_to_db(tag:dict,db:session):
    existing_track=db.query(Track).filter(Track.name==tag.get("title")).first()
    if existing_track:
        return {"status":"updated","id":existing_track.id}
    else:
        newTrack=Track(name=tag.get("title"),mix_count=1,genre=tag.get("genre"),file_path=tag.get("file_path"))
        db.add(newTrack)
        db.commit()
        db.refresh(newTrack)
        if is_track_present():
            add_track_to_all(newTrack.to_dict())
            print("added track",flush=True)
        else:
            all_tracks=get_all_tracks_from_db(db)
            set_all_tracks(all_tracks)
            print("genreated all track",flush=True)
            
        return {"status":"created","id":newTrack.id,"name":tag.get("filename")}
    
def all_tracks_from_cache():
    data= get_all_tracks()
    if data is not None:
        data=data.get("data")
        return data
    else:
        return []
    # print("data list ",data,flush=True)


async def startup_clean():
    DB_DIR=os.path.join(BASE_DIR,"site.db")
    try:
        engine.dispose()
    except Exception as e:
        print(f"failed to dispose the engine {e}")
        
    if os.path.exists(DB_DIR):
        os.remove(DB_DIR)
    if os.path.exists(TRACK_DIR):
        shutil.rmtree(TRACK_DIR)
        if not os.path.exists(TRACK_DIR):
            os.makedirs(TRACK_DIR)
    Base.metadata.create_all(bind=engine)
    
# IMPORTANT: The path to 'static' is now relative to the root execution directory (DJ Mixer)
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/tracks",StaticFiles(directory="tracks"),name="tracks")

# Templates should also point to the sibling 'static' folder
templates = Jinja2Templates(directory="static")

@app.get("/", include_in_schema=False)
async def serve_index(request: Request):
    await startup_clean()
    # This renders the 'index.html' file inside the 'static' directory
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/track/upload")
async def uploadTrack(file:UploadFile=File(...),genre:str=Form(...),db:session=Depends(get_db)):
    audio=await file.read()
    audioName=file.filename 
    file_path=os.path.join(TRACK_DIR,audioName)
    try:
        with open(file_path,'wb') as f:
            f.write(audio)
    except IOError as e:
        return {"error":e}
    finally:
        await file.close()
    

    fileInfo=mutagen.File(file_path)

    tags = {
        "filename": audioName,
        "file_path": file_path,
        "title": audioName,
        "genre": fileInfo.get('TCON', [''])[0] or genre,
        "duration_sec": fileInfo.info.length,
    }
    if not tags["title"] and not tags["filename"]:
        return JSONResponse(
            status_code=400,
            content={"error":"filename cannot be empty"}
        )

    # print("file info ",tags,flush=True)

    result=save_track_to_db(tags,db)

    return result

def save_playlist_to_db(user_prompt:str,playlist,db:session):
    new_playlist=Playlist(mood_prompt=user_prompt)
    new_playlist.set_tracks(playlist)

    db.add(new_playlist)
    db.commit()
    db.refresh(new_playlist)
    print("pllst",new_playlist,flush=True)
    return "ok"

def top_track_from_db(db:session):
    top_tracks_orm = db.query(Track).order_by(Track.mix_count.desc()).limit(10).all()
    if not top_tracks_orm:
        set_top_tracks([])
        return []

    print("got top tracks from db ",flush=True)

    tracks_in_list=[track.to_dict() for track in top_tracks_orm]
    return tracks_in_list

def increment_used(id:int,db:session):
    track=db.query(Track).get(id)
    if track is None:
        raise HTTPException(status_code=404,detail=f"Track with ID {id} not found.")
    try:
        track.mix_count+=1
        db.commit()
        db.refresh(track)
        tracks_in_list=top_track_from_db(db)
        set_top_tracks(tracks_in_list)

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500,detail=f"Database error during increment: {e}")
    return {"id":id,"used_count":track.mix_count}

class UserPromptRequest(BaseModel):
    user_prompt:str

@app.post("/api/playlist/generate")
async def generate(prompt:UserPromptRequest,db:session=Depends(get_db)):    
    # print("promt",prompt,flush=True)
    all_tracks=all_tracks_from_cache()
    # print("type -> ",type(all_tracks),flush=True)
    if not all_tracks:
        all_tracks=get_all_tracks_from_db(db)
        if all_tracks:
            set_all_tracks(all_tracks)
        else:
            raise HTTPException(status_code=404,detail="No tracks available to generate a mix.")

    all_tracks_json=json.dumps(all_tracks,indent=2)
    system_instruction = (
        "You are an expert Music Mood DJ. Your task is to select 3 to 6 tracks "
        "from the provided list that best fit the user's mood. "
        "You MUST only use the 'id' of the available tracks. "
        "You MUST strictly return the result as a single JSON object conforming "
        "to the provided schema. The 'id' must be an integer, 'order' must be 1 to 6, "
        "and 'weight' must be a float between 0.0 and 1.0."
    )
    
    user_content = (
        f"MOOD: '{prompt.user_prompt}'\n\n"
        f"AVAILABLE TRACKS:\n{all_tracks_json}\n\n"
    )

    try:
        response=client.models.generate_content(
            model="gemini-2.0-flash", contents=[system_instruction,user_content],
            config={
                    "response_mime_type": "application/json", #JSON mode for structured output
                    "response_schema": {
                    "type": "object",
                    "properties": {
                        "playlist": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "integer", "description": "ID of the selected track from the available list."},
                                    "name":{"type":"string","description": "The title or name of the track."},
                                    "order": {"type": "integer", "description": "The order of playback (1 to 6)."},
                                    "weight": {"type": "number", "format": "float", "description": "Fit to mood (0.0 to 1.0)."}
                                },
                                "required": ["id", "name","order","weight"]
                            }
                        }
                    },
                    "required": ["playlist"]
                    }
                }
        )
    except APIError as e:
        raise HTTPException(
            status_code=500,
            detail=f"error connecting ai {e}"
        )
    except Exception as e:
        raise HTTPException(status_code=500,detail=f"An unexpected error occurred: {e}")

    response_data=json.loads(response.text)
    for track in response_data.get("playlist"):
        id=track.get("id")
        increment_used(id,db)
    save_playlist_to_db(prompt.user_prompt,response_data.get("playlist"),db)
    # print("result type",type(result),flush=True)
    print("fetch done",flush=True)
    return response_data.get("playlist")
    # return {"hello":"pk"}



@app.get("/api/tracks", response_model=list) # Create a Pydantic model for the list items later
def get_all_tracks_api(db: session = Depends(get_db)):
    return get_all_tracks_from_db(db)




@app.get("/stats/top-tracks")
def top_tracks(db:session=Depends(get_db)):
    tracks=get_top_tracks()
    if tracks is not None:
        print("got top tracks from cache ",flush=True)
        return tracks
    top_tracks_orm = db.query(Track).order_by(Track.mix_count.desc()).limit(10).all()
    if not top_tracks_orm:
        set_top_tracks([])
        return []

    print("got top tracks from db ",flush=True)

    tracks_in_list=top_track_from_db(db)
    set_top_tracks(tracks_in_list)

    return tracks_in_list

# just to check for DEV
@app.get("/all_tracks_from_cache")
def gettracks():
    return all_tracks_from_cache()

@app.get("/getcache")
def getcache():
    data= get_all_cache()  
    # print(data,flush=False)
    data=data.get("ALL_TRACKS")
    return data

@app.get("/used")
def used(db:session=Depends(get_db)):
    results=db.query(Track).all()
    used_list=[item.get_used() for item in results]
    return used_list
