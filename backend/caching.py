from datetime import datetime,timedelta
IN_MEMORY_CACHE={}

TOP_TRACKS="TOP_TRACKS"
TOP_TRACKS_TTL=3600

ALL_TRACKS="ALL_TRACKS"
ALL_TRACKS_TTL=86400

def get_all_cache():
    return IN_MEMORY_CACHE


def is_track_present():
    if ALL_TRACKS in IN_MEMORY_CACHE:
        if IN_MEMORY_CACHE[ALL_TRACKS]["expiry"]<datetime.now():
            del IN_MEMORY_CACHE[ALL_TRACKS]
            return False
        else:
            return True
    return False


def update_cache(key:str,track,data,ttl):
    
    if key == ALL_TRACKS:
        if key in IN_MEMORY_CACHE:
            IN_MEMORY_CACHE[key]['data'].append(track)
        else:
            IN_MEMORY_CACHE[key]={
                'data':data,
                'expiry':datetime.now()+timedelta(seconds=ttl)
            }
    else:
        IN_MEMORY_CACHE[key]={
            'data':data,
            'expiry':datetime.now()+timedelta(seconds=ttl)
        }
    # return {}

def get_cache(key:str):
    if key in IN_MEMORY_CACHE:
        if IN_MEMORY_CACHE[key]["expiry"]>datetime.now():
            return IN_MEMORY_CACHE[key]
        else:
            del IN_MEMORY_CACHE[key]
    return None

def set_top_tracks(data):
    return update_cache(TOP_TRACKS,None,data,TOP_TRACKS_TTL)

def add_track_to_all(track):
    return update_cache(ALL_TRACKS,track,None,ALL_TRACKS_TTL)

def set_all_tracks(data):
    return update_cache(ALL_TRACKS,None,data,ALL_TRACKS_TTL)

def get_top_tracks():
    return get_cache(TOP_TRACKS)

def get_all_tracks():
    return get_cache(ALL_TRACKS)
