import pathlib
import logging

import discogs_client
import taglib

logger = logging.getLogger(__name__)

tags = ["album", "artist", "title", "year", "date", "genre", "tracknumber"]


class MetaFinder:
    def __init__(
        self, user_token: str | None = None, user_token_file: str | None = None
    ):
        if user_token_file:
            user_token = open(user_token_file).read()

        if user_token is None:
            logger.warning("No user token specified, functionality will be limited")

        self.discogs_client = discogs_client.Client(
            "ExampleApplication/0.1", user_token=user_token
        )

    def search(self, file: pathlib.Path):

        artists: list[discogs_client.Artist] = []
        concatenated_artist_names = obtain_tag(file, "artist")
        if concatenated_artist_names:
            artist_names = concatenated_artist_names.split(", ")
            for artist_name in artist_names:
                artist = self.search_artist(artist_name)
                if artist is not None:
                    artists.append(artist)

        album = obtain_tag(file, "album")

        # Construct search prompt
        search_prompt = file.stem 
        if album:
            search_prompt = album

            if concatenated_artist_names:
                search_prompt = search_prompt + " " + concatenated_artist_names

        search_prompt = clean_up_search_prompt(search_prompt)
        
        # First try to find the master release
        master = self.search_master(search_prompt, artists=artists)
        if master:
            return True

        # Search for the normal release instead
        release = self.search_release(search_prompt, artists=artists)
        if release:
            return True
        
        if search_prompt == file.stem:
            return False
        
        # Try again using the file stem
        search_prompt = file.stem
        release = self.search_release(search_prompt, artists=artists)
        if release:
            return True

        logger.warning("Failed to find release")
        return False

    def search_release(self, search_prompt: str, artists: list[discogs_client.Artist] | None = None
    ) -> discogs_client.Release | None:
        releases: list[discogs_client.Release] = self.discogs_client.search(
            search_prompt, type="release"
        )

        if not releases:
            logger.info(
                f"Did not find any releases corresponding to search prompt {search_prompt}"
            )
            return None

        logger.info(
            f"Found {len(releases)} release(s) corresponding to search prompt {search_prompt}"
        )

        # filter based on artist
        filtered_releases = []
        for release in releases:
            if artists:
                if not release_contains_artist(release, artists):
                    continue

            filtered_releases.append(release)

        if not filtered_releases:
            logger.info("No releases left after filtering, the artist might be incorrect")
            return None

        logger.info(f"Found {len(filtered_releases)} release(s) after filtering")
        for release in filtered_releases:
            print_release(release)

        release = filtered_releases[0]

        # print result
        if release.master:
            logger.info(f"Selected the following master release:")
            print_master(release.master)
        else:
            logger.info(f"Selected the following release:")
            print_release(release)

        return release


    def search_master(
        self, search_prompt: str, artists: list[discogs_client.Artist] | None = None
    ) -> discogs_client.Master | None:
        masters: list[discogs_client.Master] = self.discogs_client.search(search_prompt, type="master")

        if not masters:
            logger.info(
                f"Did not find any master releases corresponding to search prompt {search_prompt}"
            )
            return None

        logger.info(
            f"Found {len(masters)} master release(s) corresponding to search prompt {search_prompt}"
        )

        # filter based on artist
        filtered_masters = []
        for master in masters:
            if artists:
                release = master.main_release
                if not release_contains_artist(release, artists):
                    continue

            filtered_masters.append(master)

        if not filtered_masters:
            logger.info("No master releases left after filtering, the release might not have a master, or the artist might be incorrect")
            return None

        logger.info(f"Found {len(filtered_masters)} master release(s) after filtering")
        for master in filtered_masters:
            print_master(master)
        
        master = filtered_masters[0]

        # print result
        logger.info(f"Selected the following master release:")
        print_master(master)
        return master

    def search_artist(self, search_prompt: str) -> discogs_client.Artist | None:
        artists: list[discogs_client.Artist] = []
        artists = self.discogs_client.search(search_prompt, type="artist")

        if not artists:
            logger.info(
                f"Did not find any artists corresponding to search prompt {search_prompt}"
            )
            return None

        if len(artists) > 1:
            logger.info(
                f"Found {len(artists)} artists corresponding to search prompt {search_prompt}: will use the first one"
            )

        else:
            logger.info(
                f"Found the artist corresponding to search prompt {search_prompt}"
            )

        artist = artists[0]
        return artist


def print_release(release: discogs_client.Release):
    print(f"Release: {release.title}")
    print(f" - id: {release.id}")
    print(f" - artists: {", ".join([artist.name for artist in release.artists])}")
    print(f" - year: {release.year}")
    print(f" - data quality: {release.data_quality}")
    print(f" - styles: {(', '.join(release.styles) if release.styles else "None")}")
    print(f" - genres: {(', '.join(release.genres) if release.genres else "None")}")
    print(f" - url {release.url}")


def print_master(master: discogs_client.Master):
    print(f"Master release {master.title}")
    print(f" - id: {master.id}")
    print(f" - year: {master.year}")
    print(f" - data quality: {master.data_quality}")
    print(f" - styles: {(', '.join(master.styles) if master.styles else "None")}")
    print(f" - genres: {(', '.join(master.genres) if master.genres else "None")}")
    print(f" - url {master.url}")


def print_artist(artist: discogs_client.Artist):
    print(f"Name: {artist.name}")


def obtain_tag(file: pathlib.Path, tag: str) -> str | None:
    if not file.exists():
        logger.debug("File does not exist")
        return None

    song = taglib.File(file, save_on_exit=False)
    if not song.tags:
        logger.debug("Song does not contain any tags")
        return None

    if tag.upper() not in song.tags:
        logger.debug(f"Song does not contain {tag} tag")
        return None
    
    values = song.tags[tag.upper()]
    if not values:
        logger.debug(f"The {tag} field is empty")
        return None

    if len(values) > 1:
        logger.debug(
            f"The tag {tag} contains multiple fields: selecting the first entry"
        )

    return values[0]

def release_contains_artist(release : discogs_client.Release, artists: list[discogs_client.Artist]):
    try:
        release.artists
    except discogs_client.exceptions.HTTPError as e:
        logger.error(f"Failed to fetch release: caught the following expcetion {e}")
        return False

    if not release.artists:
        logger.warning(f"The release {release.title} does not contain any artists")
        return False

    release_names = [artist.name for artist in release.artists]
    artist_names = [artist.name for artist in artists]
    for artist in artists:
        if artist not in release.artists:
            logger.debug(
                f"Release {release.title} featuring {", ".join(release_names)} does not contain {artist.name}"
            )
            return False

    logger.info(f"Release {release.title} featuring {", ".join(release_names)} contains  {", ".join(artist_names)}")
    return True

def clean_up_search_prompt(search_prompt: str):
    # clean-up search prompt
    search_prompt = search_prompt.replace(" / ", " ")
    search_prompt = search_prompt.replace("/", " ")

    search_prompt = search_prompt.replace(" - ", " ")
    search_prompt = search_prompt.replace("-", " ")
    return search_prompt
