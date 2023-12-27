import pathlib
import logging
from typing import Optional

from src import constants
from src import utils

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


class WavFixer:
    def __init__(self):
        self._incompatible_files: list[pathlib.Path] = []

        self.n_processed_files = 0
        self.incompatible_hex_value = f"{constants.WAVE_FORMAT_EXTENSIBLE:04X}"
        self.new_hex_value = f"{constants.WAVE_FORMAT_PCM:04X}"

    def reset(self):
        self.n_processed_files = 0
        self._incompatible_files.clear()

    def find_incompatible_wav_files(self, files: list[pathlib.Path]):
        self._incompatible_files.clear()
        self.n_processed_files = 0

        if not files:
            logger.warning(
                "Can not look for incompatible files among files: the files are still empty"
            )
            return False

        for file in files:
            self.n_processed_files = self.n_processed_files + 1
            if not self.is_wav_file_incompatible(file):
                continue

            self._incompatible_files.append(file)
            logger.debug(
                f"The wav file {file.name} contains the key {constants.WAVE_FORMAT_EXTENSIBLE} at the specified location. Storing the file name..."
            )

        if not self._incompatible_files:
            logger.info(f"Did not find any incompatible wav files")
            return False

        logger.info(f"Found {len(self._incompatible_files)} incompatible wav files")
        return True

    def is_wav_file_incompatible(self, file: pathlib.Path):
        hex_value = utils.read_hex_value(
            file, constants.AUDIO_FORMAT_OFFSET, constants.AUDIO_FORMAT_FIELD_SIZE
        )
        if not hex_value:
            logger.warning(f"Failed to read the hex value from the file {file}")
            return False

        int_value = int(hex_value, 16)
        if int_value != constants.WAVE_FORMAT_EXTENSIBLE:
            return False

        return True

    def fix_incompatible_wav_files(self, indices: Optional[list[int]] = None):
        if not self._incompatible_files:
            logger.info(
                "Can not fix incompatible files: first find some incompatible files!"
            )
            return False

        if indices is None:
            files = self._incompatible_files
        else:
            try:
                files = [self._incompatible_files[i] for i in indices]
            except Exception as e:
                logger.warning(
                    f"Failed to fix incompatible wav file, indices invalid. Caught the following exception:\n {e}\n\nFor indices\n{indices}"
                )
                return False

        overall_success = True
        for file in files:
            success = self.fix_incompatible_wav_file(file)
            overall_success = overall_success and success

        return overall_success

    def fix_incompatible_wav_file(self, file: pathlib.Path):
        if file not in self._incompatible_files:
            logger.warning(f"Refusing to fix {file.name}: there is nothing to fix!")
            return False

        logger.info(
            f"Will replace {self.incompatible_hex_value} at offset {constants.AUDIO_FORMAT_OFFSET} and field size {constants.AUDIO_FORMAT_FIELD_SIZE} with {self.new_hex_value} for file {file}"
        )

        success = utils.set_hex_data(
            file,
            constants.AUDIO_FORMAT_OFFSET,
            constants.AUDIO_FORMAT_FIELD_SIZE,
            self.new_hex_value,
        )
        if not success:
            logger.error(f"Failed to fix {file.name}")
            return False

        # verify whether problem was fixed
        is_still_incompatible = self.is_wav_file_incompatible(file)
        if is_still_incompatible:
            logger.warning(
                f"Wav file {file.name} is still incompatible after trying to apply fix"
            )
            return False

        self._incompatible_files.remove(file)
        return True

    @property
    def incompatible_files(self):
        return self._incompatible_files.copy()

    @property
    def n_incompatible_files(self):
        return len(self._incompatible_files)
