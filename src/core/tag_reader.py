import pathlib
import logging
import copy

import discogs_client
import taglib

logger = logging.getLogger(__name__)


class FILE_TAG:
    ALBUM = "album"
    ARTIST = "artist"
    TITLE = "title"
    YEAR = "year"
    DATE = "date"
    GENRE = "genre"
    TRACK_NUMBER = "tracknumber"


TAGS = [
    FILE_TAG.ALBUM,
    FILE_TAG.ARTIST,
    FILE_TAG.TITLE,
    FILE_TAG.YEAR,
    FILE_TAG.DATE,
    FILE_TAG.GENRE,
    FILE_TAG.TRACK_NUMBER,
]


class Tag:
    def __init__(self):
        self.album = ""
        self.artists: list[str] = []
        self.title = ""
        self.year = None
        self.date = ""
        self.genres: list[str] = []
        self.track_number = None

    def print(self):
        print(f"Tag info: ")
        print(f"Album: {self.album}")
        print(f"Artists: {", ".join(self.artists)}")
        print(f"Title: {self.title}")
        print(f"Year: {self.year}")
        print(f"Date: {self.date}")
        print(f"Genre: {", ".join(self.genres)}")
        print(f"track number: {self.track_number}")

    def copy(self):
        return copy.deepcopy(self)


class FileTagReader(Tag):
    def __init__(self, file: pathlib.Path):
        super().__init__()

        if not file.exists():
            raise FileNotFoundError(f"File {file} does not exist")

        self.song = taglib.File(file, save_on_exit=False)
        self.file = file
        self.load_tags()

    def load_tags(self):
        found_any = False
        for key in TAGS:
            tag = self.load_tag(key)

            if tag is None:
                continue

            found_any = True
            logger.debug(f"Found {tag} as {key} of {self.file}")
            if key == FILE_TAG.ALBUM:
                self.album = tag
            elif key == FILE_TAG.ARTIST:
                self.artists = tag.split(", ")
            elif key == FILE_TAG.TITLE:
                self.title = tag
            elif key == FILE_TAG.YEAR:
                self.year = tag
            elif key == FILE_TAG.DATE:
                self.date = tag
            elif key == FILE_TAG.GENRE:
                self.genres = tag.split(", ")
            elif key == FILE_TAG.TRACK_NUMBER:
                self.track_number = tag

        return found_any

    def load_tag(self, key: str) -> str | None:
        if not self.song.tags:
            logger.debug("Song does not contain any tags")
            return None

        if key.upper() not in self.song.tags:
            logger.debug(f"Song does not contain {key} tag")
            return None

        values = self.song.tags[key.upper()]
        if not values:
            logger.debug(f"The {key} field is empty")
            return None

        if len(values) > 1:
            logger.debug(
                f"The tag {key} contains multiple fields: selecting the first entry"
            )

        return values[0]

    def copy(self):
        self.song = None  # can not copy taglib.File
        return super().copy()


class DiscogsTagReader(Tag):
    def __init__(self, release: discogs_client.Release):
        super().__init__()
        self.release = release
        self.load_tags()

    def load_tags(self):
        self.album = str(self.release.title)
        self.title = ""
        self.year = str(self.release.year)
        self.genres = self.release.genres
        self.artists = [artist.name for artist in self.release.artists]
        self.url = self.release.url
