import pathlib

from ui import UI
from core import Core


def main():
    core = Core(pathlib.Path.home() / "Music" / "PioneerDJ" / "Tracks")
    ui = UI(core)

    ui.run()


if __name__ == "__main__":
    main()
