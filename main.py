import pathlib

from src.ui import UI
from src.core import Core


def main():
    # configure
    music_path = pathlib.Path.home() / "Music"
    path = music_path if music_path.is_dir() else pathlib.Path.home()

    # construct
    core = Core(path)
    ui = UI(core)

    # run
    ui.run()


if __name__ == "__main__":
    main()
