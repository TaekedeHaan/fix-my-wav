import pathlib

from src.ui import UI
from src.core import WavFinder, WavFixer


def main():
    # configure
    music_path = pathlib.Path.home() / "Music"
    path = music_path if music_path.is_dir() else pathlib.Path.home()

    # construct
    wav_finder = WavFinder(path)
    wav_fixer = WavFixer()
    ui = UI(wav_finder, wav_fixer)

    # run
    ui.run()


if __name__ == "__main__":
    main()
