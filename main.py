import pathlib

from src.ui import UI
from src.core import WavFinder, WavFixer, MetaFinder


def main():
    # configure
    music_path = pathlib.Path.home() / "Music"
    path = music_path if music_path.is_dir() else pathlib.Path.home()

    # construct
    wav_finder = WavFinder(path)
    wav_fixer = WavFixer()
    meta_finder = MetaFinder(user_token_file="token.txt")
    ui = UI(wav_finder, wav_fixer, meta_finder)

    # run
    ui.run()


if __name__ == "__main__":
    main()
