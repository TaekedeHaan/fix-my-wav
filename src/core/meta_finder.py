import pathlib
import logging

logger = logging.getLogger(__name__)

import discogs_client


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

    def search_release(self, file: pathlib.Path):
        releases: list[discogs_client.Release] = self.discogs_client.search(
            file.stem, type="release"
        )

        if not releases:
            logger.info(f"Did not find any releases corresponding to file {file.stem}")
            return False

        if len(releases) > 1:
            logger.info(
                f"Found {len(releases)} release(s) corresponding to file {file.stem}: will use the first one"
            )

        else:
            logger.info(f"Found the release corresponding to file {file.stem}")

        release = releases[0]
        self.print_release(release)
        return True

    def print_release(self, release: discogs_client.Release):
        print(release.id)
        print(release.title)
        print(release.data_quality)
        print(release.styles)
        print(release.year)
        print(release.genres)
        print(release.images)
        # print(release.url)
        # print(release.videos)
        # print(release.tracklist)
        # print(release.main_release)
        # print(release.versions)
