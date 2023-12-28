import pathlib
import logging

from src import constants

logger = logging.getLogger(__name__)


class WavFinder:
    def __init__(self, base_path: pathlib.Path = pathlib.Path.home()):
        self._base_path = base_path
        self._files: list[pathlib.Path] = []

    def reset(self):
        self.n_processed_files = 0
        self._files.clear()

    def find_wav_files(self):
        self.reset()

        # The folder itself might have been changed or deleted since setting it
        if not self.base_path.is_dir():
            logger.warning("The provided base path {} does not exist")
            return False

        files_generator = self.base_path.rglob(constants.WAV_EXTENSION)
        for file in files_generator:
            self._files.append(file)

        if not self._files:
            logger.info(f"Did not find any wav files at {self.base_path}")
            return False

        logger.info(f"Found {len(self._files)} wav files, at {self.base_path}")
        return True

    @property
    def base_path(self):
        return self._base_path

    @base_path.setter
    def base_path(self, base_path: pathlib.Path):
        if not base_path.is_dir():
            raise NotADirectoryError(
                f"Can not set base path to {base_path}: it does not exist"
            )

        logger.info(f"Setting base path to {base_path}")
        self.reset()
        self._base_path = base_path

    @property
    def files(self):
        return self._files.copy()

    @property
    def n_files(self):
        return len(self._files)
