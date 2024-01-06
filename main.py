import pathlib

from src.ui import UI
from src.core import WavFinder, WavFixer, DiscogsSearchEngine


def main():
    # configure
    music_path = pathlib.Path.home() / "Music"
    path = music_path if music_path.is_dir() else pathlib.Path.home()

    # construct
    wav_finder = WavFinder(path)
    wav_fixer = WavFixer()
    discogs_search_engine = DiscogsSearchEngine(user_token_file="token.txt")
    ui = UI(wav_finder, wav_fixer, discogs_search_engine)

    # run
    ui.run()


if __name__ == "__main__":
    main()
