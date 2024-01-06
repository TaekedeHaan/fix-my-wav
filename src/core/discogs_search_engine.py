# type: ignore
import logging

import discogs_client
from src.core.tag_reader import FileTagReader
from src.core.discogs_utils import print_master, print_release

logger = logging.getLogger(__name__)


class DiscogsSearchEngine:
    """Search for a discogs release"""

    def __init__(
        self, user_token: str | None = None, user_token_file: str | None = None
    ):
        if user_token_file:
            user_token = open(user_token_file).read()

        if user_token is None:
            logger.warning("No user token specified, functionality will be limited")

        self.discogs_candidates = 1
        self.discogs_client = discogs_client.Client(
            "ExampleApplication/0.1", user_token=user_token
        )

    def search_with_file(
        self, file_tag_reader: FileTagReader
    ) -> discogs_client.Release | None:

        artists: list[discogs_client.Artist] = []
        for artist_name in file_tag_reader.artists:
            artist = self.search_artist(artist_name)
            if artist is None:
                continue
            artists.append(artist)

        # Construct search prompt
        search_prompt = file_tag_reader.file.stem
        if file_tag_reader.album:
            search_prompt = file_tag_reader.album

            if file_tag_reader.artists:
                search_prompt = search_prompt + " " + " ".join(file_tag_reader.artists)

        search_prompt = clean_up_search_prompt(search_prompt)
        release = self.search_with_prompt(search_prompt, artists=artists)
        if release:
            return release

        search_prompt = file_tag_reader.file.stem
        return self.search_with_prompt(search_prompt)

    def search_with_prompt(
        self, search_prompt: str, artists: list[discogs_client.Artist] | None = None
    ) -> discogs_client.Release | None:
        # First try to find the master release
        master = self.search_master(search_prompt, artists=artists)
        if master:
            return master.main_release

        # Search for the normal release instead
        release = self.search_release(search_prompt, artists=artists)
        if release:
            return release

        logger.warning(f"Failed to find a release matching prompt {search_prompt}")
        return None

    def search_release(
        self, search_prompt: str, artists: list[discogs_client.Artist] | None = None
    ) -> discogs_client.Release | None:
        releases: list[discogs_client.Release] = []
        releases = self.discogs_client.search(search_prompt, type="release")

        if not releases:
            logger.info(
                f"Did not find any releases corresponding to search prompt {search_prompt}"
            )
            return None

        logger.info(
            f"Found {len(releases)} release(s) corresponding to search prompt {search_prompt}"
        )

        # filter based on artist
        filtered_releases: list[discogs_client.Release] = []
        for release in releases:
            if artists:
                if not release_contains_artist(release, artists):
                    continue

            filtered_releases.append(release)
            if len(filtered_releases) >= self.discogs_candidates:
                break

        if not filtered_releases:
            logger.info(
                "No releases left after filtering, the artist might be incorrect"
            )
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
        masters: list[discogs_client.Master] = []
        masters = self.discogs_client.search(search_prompt, type="master")

        if not masters:
            logger.info(
                f"Did not find any master releases corresponding to search prompt {search_prompt}"
            )
            return None

        logger.info(
            f"Found {len(masters)} master release(s) corresponding to search prompt {search_prompt}"
        )

        # filter based on artist
        filtered_masters: list[discogs_client.Master] = []
        for master in masters:
            if artists:
                release = master.main_release
                if not release_contains_artist(release, artists):
                    continue

            filtered_masters.append(master)
            if len(filtered_masters) >= self.discogs_candidates:
                break

        if not filtered_masters:
            logger.info(
                "No master releases left after filtering, the release might not have a master, or the artist might be incorrect"
            )
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

    logger.info(f"Release {release.title} featuring {", ".join(release_names)} contains {", ".join(artist_names)}")
    return True

def clean_up_search_prompt(search_prompt: str):
    # clean-up search prompt
    search_prompt = search_prompt.replace(" / ", " ")
    search_prompt = search_prompt.replace("/", " ")

    search_prompt = search_prompt.replace(" - ", " ")
    search_prompt = search_prompt.replace("-", " ")
    return search_prompt
