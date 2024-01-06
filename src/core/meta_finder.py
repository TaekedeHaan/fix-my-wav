import pathlib
import logging

from src.core.discogs_search_engine import DiscogsSearchEngine
from src.core.tag_reader import FileTagReader, DiscogsTagReader

logger = logging.getLogger(__name__)


class MetaFinder:
    def __init__(
        self,
        file: pathlib.Path,
        discogs_search_engine: DiscogsSearchEngine | None = None,
    ):
        self.file_tag_reader = FileTagReader(file)
        self.file_tag_writer = self.file_tag_reader.copy()
        self.discogs_tag_reader = None
        self.discogs_search_engine = discogs_search_engine

    def search(self):
        if self.discogs_search_engine is None:
            logger.warning(
                "Can not search for release on discogs: first initialize the discogs finder"
            )
            return

        release = self.discogs_search_engine.search_with_file(self.file_tag_reader)
        if release:
            self.discogs_tag_reader = DiscogsTagReader(release)

        if self.discogs_tag_reader:
            logger.info("Discogs tags: ")
            self.discogs_tag_reader.print()

        if self.file_tag_reader:
            logger.info("file tags: ")
            self.file_tag_reader.print()
