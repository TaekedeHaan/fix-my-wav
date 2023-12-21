import pathlib
import logging
from typing import Optional

from src import constants
from src import utils

logger = logging.getLogger(__name__)


class Core:
    def __init__(self, base_path: pathlib.Path = pathlib.Path.home()):
        self._base_path = base_path
        self._files: list[pathlib.Path] = []
        self._suspicious_files: list[pathlib.Path] = []

        self.n_processed_files = 0
        self.suspicious_hex_value = f"{constants.WAVE_FORMAT_EXTENSIBLE:04X}"
        self.new_hex_value = f"{constants.WAVE_FORMAT_PCM:04X}"

    def reset(self):
        self.n_processed_files = 0
        self._files.clear()
        self._suspicious_files.clear()

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

    def find_suspicious_wav_files(self):
        self._suspicious_files.clear()
        self.n_processed_files = 0

        if not self._files:
            logger.warning(
                "Can not look for suspicious files among files: the files are still empty"
            )
            return False

        for file in self._files:
            self.n_processed_files = self.n_processed_files + 1
            if not self.is_wav_file_suspicious(file):
                continue

            self._suspicious_files.append(file)
            logger.debug(
                f"The wav file {file.name} contains the key {constants.WAVE_FORMAT_EXTENSIBLE} at the specified location. Storing the file name..."
            )

        if not self._suspicious_files:
            logger.info(f"Did not find any suspicious wav files at {self.base_path}")
            return False

        logger.info(f"Found {len(self._suspicious_files)} suspicious wav files")
        return True

    def is_wav_file_suspicious(self, file: pathlib.Path):
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

    def fix_suspicious_wav_files(self, indices: Optional[list[int]] = None):
        if not self._files:
            logger.info(
                "Can not fix suspicious files: first find some suspicious files!"
            )
            return False

        if indices is None:
            files = self._suspicious_files
        else:
            try:
                files = [self._suspicious_files[i] for i in indices]
            except Exception as e:
                logger.warning(
                    f"Failed to fix suspicious wav file, indices invalid. Caught the following exception:\n {e}\n\nFor indices\n{indices}"
                )
                return False

        overall_success = True
        for file in files:
            success = self.fix_suspicious_wav_file(file)
            overall_success = overall_success and success

        return overall_success

    def fix_suspicious_wav_file(self, file: pathlib.Path):
        if file not in self._suspicious_files:
            logger.warning(f"Refusing to fix {file.name}: there is nothing to fix!")
            return False

        logger.info(
            f"Will replace {self.suspicious_hex_value} at offset {constants.AUDIO_FORMAT_OFFSET} and field size {constants.AUDIO_FORMAT_FIELD_SIZE} with {self.new_hex_value} for file {file}"
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
        is_still_suspicious = self.is_wav_file_suspicious(file)
        if is_still_suspicious:
            logger.warning(
                f"Wav file {file.name} is still suspicious after trying to apply fix"
            )
            return False

        self._suspicious_files.remove(file)
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
    def suspicious_files(self):
        return self._suspicious_files.copy()

    @property
    def n_files(self):
        return len(self._files)

    @property
    def n_suspicious_files(self):
        return len(self._suspicious_files)


def main():
    core = Core()

    # set base path
    user_path = pathlib.Path.home()
    base_path = (
        user_path
        / "Downloads"
        / "Various Artists - Ritmo Fantasía- Balearic Spanish Synth-Pop- Boogie and House (1982-1992) -Compiled by DJ Trujillo"
    )
    core.base_path = base_path

    found_wav_files = core.find_wav_files()
    if not found_wav_files:
        return

    found_suspicious_wav_files = core.find_suspicious_wav_files()
    if not found_suspicious_wav_files:
        return

    fixed_suspicious_wav_files = core.fix_suspicious_wav_files()
    if not fixed_suspicious_wav_files:
        logger.info(
            f"Failed to fix the suspicious wav files at {core.base_path}, exiting"
        )
        return

    logger.info(f"Successfully fixed {len(core.suspicious_files)} suspicious wav files")


if __name__ == "__main__":
    main()
