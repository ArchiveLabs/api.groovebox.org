import requests
import json
from utils import subdict

BASE_URL = "https://archive.org"
API_URL = "%s/advancedsearch.php" % BASE_URL
METADATA = "%s/metadata" % BASE_URL
COVERART_API_URL = "https://itunes.apple.com/search"
REQUIRED_KEYS = ['track', 'title', 'album', 'length', 'name', 'creator']
FILETYPE_PRIORITY = ['mp3', 'shn', 'flac', 'ogg']

class Crawler(object):

    def __init__(self):
        pass


    @staticmethod
    def concerts(artist, limit=20000):
        """Retrieves all the concerts (items) of a band from Archive.org API
        
        params:
            artist - the collection id for this artist (e.g. GratefulDead)
        """
        params = {
            "q": "collection:(%s)" % artist,
            "fl[]": "identifier",
            "rows": limit,
            "output": "json"
            }
        return requests.get(API_URL, params=params).json()


    @classmethod
    def concert(cls, concert):
        """Retrieves a concert's metadata + tracks from Archive.org API"""
        url = "%s/%s" % (METADATA, concert)
        r = requests.get(url).json()
        fs = r.pop('files')
        r = r.pop('metadata', {})
        try:
            r['tracks'] = cls._tracks(fs)
        except Exception as e:
            return e
        try:
            r['artist'] = cls.coverart(r['creator'])
        except Exception as e:
            return e
        return r


    @staticmethod
    def coverart(artist, song=""):
        """http://www.apple.com/itunes/affiliates/resources/documentation
               /itunes-store-web-service-search-api.html
        """        
        keep_keys = ["primaryGenreName", "coverArt"] + \
            (["collectionName", "trackName", "releaseDate"] if song else [])
        r = requests.get(COVERART_API_URL, params={
                "media": "music",
                "artistName": artist,
                "term": song or artist, #if no song available
                "country": "us",
                "limit": 1
                }).json()['results'][0]
        r["coverArt"] = r["artworkUrl100"].replace('.100x100-75', '')
        return dict([(key, r[key]) for key in keep_keys])


    @staticmethod
    def _tracks(files):
        """Returns a sorted list of tracks given Archive.org item
        (concert) metadata files
        """
        def get_filetype(files):
            available = set(f.get('name', '').lower().rsplit('.', 1)[1] for f in files)
            return next(ft if ft in available else False for ft in FILETYPE_PRIORITY)

        ts = []
        filetype = get_filetype(files)

        if not filetype:        
            return {} # better error handling required

        for f in files:
            try:
                track = subdict(f, REQUIRED_KEYS)
            except KeyError as e:            
                continue # Skip if track doesn't have required keys

            title = track.get('title')
            if track['name'].endswith(filetype):
                ts.append(track)
        return sorted(ts, key=lambda t: int(t['track']))
