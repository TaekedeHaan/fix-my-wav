import pathlib
import tkinter as tk
import tkinter.ttk as ttk
import threading
from tkinter import filedialog
import logging

from src.core import Core

logger = logging.getLogger(__name__)

FIND_WAVS = "find_wavs"
FIND_INCOMPATIBLE_WAVS = "find_incompatible_wavs"
FIX_INCOMPATIBLE_WAVS = "fix_incompatible_wavs"


class UI:
    def __init__(self, core: Core):
        self.core = core

        # An easy but dirty way to detect whether these have been changes since the last call
        self.incompatible_files = []

        window = tk.Tk()
        image_subsample = 20

        # Load resources
        path_resources = pathlib.Path().absolute() / "resources"
        path_img_file = path_resources / "sound_black.png"
        path_img_repair = path_resources / "repair_black.png"
        self.img_file = tk.PhotoImage(file=path_img_file).subsample(
            image_subsample, image_subsample
        )
        self.img_repair = tk.PhotoImage(file=path_img_repair).subsample(
            image_subsample, image_subsample
        )

        # window layout
        window.iconphoto(False, self.img_file)
        window.title("FixMyWav")

        # list incompatible wavs
        frm_list_incompatible_wavs = ttk.Frame(window)

        # tree view
        frm_tree_view = ttk.Frame(frm_list_incompatible_wavs)
        tree = ttk.Treeview(
            frm_tree_view,
            columns=("file name", "path"),
        )

        yscrollbar = tk.Scrollbar(frm_tree_view, orient=tk.VERTICAL)
        yscrollbar.configure(command=tree.yview)
        tree.configure(yscrollcommand=yscrollbar.set)
        yscrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        xscrollbar = tk.Scrollbar(frm_tree_view, orient=tk.HORIZONTAL)
        tree.configure(xscrollcommand=xscrollbar.set)
        xscrollbar.configure(command=tree.xview)
        xscrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        tree.column("#0", anchor=tk.NW, stretch=False, width=50)
        tree.heading("#0", text="ID")
        tree.column("#1", anchor=tk.NW)
        tree.heading("#1", text="File name")
        tree.column("#2", anchor=tk.NW)
        tree.heading("#2", text="Path")

        tree.pack(side=tk.TOP, fill=tk.X)
        frm_tree_view.pack(fill=tk.X)

        # browse
        frm_browse = ttk.Frame(window)
        ent_directory = ttk.Entry(frm_browse)
        ent_directory.insert(0, str(self.core.base_path))

        btn_browse = ttk.Button(
            frm_browse,
            text="Browse",
            command=self._update_directory,
        )

        ent_directory.pack(fill=tk.X, side=tk.LEFT, expand=True)
        btn_browse.pack(side=tk.LEFT)

        ### execute
        frm_execute = ttk.Frame(window)

        # find incompatible wavs
        frm_find_incompatible_wavs = ttk.Frame(frm_execute)

        btn_find_incompatible_wav = ttk.Button(
            frm_find_incompatible_wavs,
            text="Find incompatible wav's",
            command=self._find_incompatible_wavs,
        )
        btn_find_incompatible_wav.pack(side=tk.LEFT)
        frm_find_incompatible_wavs.pack(fill=tk.X, side=tk.LEFT)

        # Fix boken wavs
        btn_fix_incompatible_wav = ttk.Button(
            frm_find_incompatible_wavs,
            text="Fix incompatible wav's",
            command=self._fix_incompatible_wavs,
        )
        btn_fix_incompatible_wav.pack(side=tk.LEFT)

        # status bar
        self.str_status_bar = tk.StringVar()
        lbl_status = ttk.Label(
            window,
            anchor=tk.W,
            textvariable=self.str_status_bar,
        )
        lbl_status.pack(fill=tk.X, side=tk.BOTTOM)

        # Pack main frames
        frm_list_incompatible_wavs.pack(fill=tk.X)
        frm_browse.pack(fill=tk.X)
        frm_execute.pack(fill=tk.X)

        # set members
        self.window = window
        self.ent_directory = ent_directory
        self.tree = tree

        # Threads
        self.threads: dict[str, threading.Thread] = {}

        # settings
        self.frequency = 50
        self.update_rate_ms = round(1000 / self.frequency)

        # start
        self._find_wavs()

    def _update_directory(self):
        if self.is_busy():
            return

        directory = filedialog.askdirectory(
            parent=self.window,
            title="Select a directory",
            initialdir=self.core.base_path,
            mustexist=True,
        )

        if not directory:
            logger.debug("No directory selected: nothing to do here")
            return

        path = pathlib.Path(directory)
        if self.core.base_path == path:
            logger.debug("Same directory selected: nothing to do here")
            return

        try:
            self.core.base_path = path
        except NotADirectoryError as e:
            logger.warning(
                f"Failed to set path to {self.core.base_path}, caught the following exception: {e}"
            )

        self.ent_directory.delete(0, tk.END)
        self.ent_directory.insert(0, str(self.core.base_path))
        self._find_wavs()

    def _find_wavs(self):
        if self.is_busy():
            return

        self.threads[FIND_WAVS] = threading.Thread(target=self.core.find_wav_files)
        self.threads[FIND_WAVS].start()

    def _find_incompatible_wavs(self):
        if self.is_busy():
            return

        self.threads[FIND_INCOMPATIBLE_WAVS] = threading.Thread(
            target=self.core.find_incompatible_wav_files
        )
        self.threads[FIND_INCOMPATIBLE_WAVS].start()

    def _fix_incompatible_wavs(self):
        if self.is_busy():
            return

        indices = self.tree.selection()
        if not indices:
            logger.info("No files selected")
            return

        int_indices = [int(index) for index in indices]
        self.threads[FIX_INCOMPATIBLE_WAVS] = threading.Thread(
            target=self.core.fix_incompatible_wav_files, args=(int_indices,)
        )
        self.threads[FIX_INCOMPATIBLE_WAVS].start()

    def _tick(self):
        self.cleanup_threads()

        self._update_status_bar()

        # Update list if change was detected
        if self.incompatible_files != self.core.incompatible_files:
            self._update_tree_view()

        # plan next tick
        self.window.after(self.update_rate_ms, self._tick)

    def _update_tree_view(self):
        factor = 6
        longest_file_name = 0
        longest_file_path = 0

        self.incompatible_files = self.core.incompatible_files
        self.tree.delete(*self.tree.get_children())
        for i, file in enumerate(self.core.incompatible_files):
            self.tree.insert(
                "",
                "end",
                text=str(i),
                iid=i,
                values=(file.name, file.parent),
            )

            longest_file_name = max(len(file.name), longest_file_name)
            longest_file_path = max(len(str(file.parent)), longest_file_path)

        self.tree.column("#1", minwidth=longest_file_name * factor)
        self.tree.column("#2", minwidth=longest_file_path * factor)

    def _update_status_bar(self):
        if self.is_find_wavs_active():
            self.str_status_bar.set(f"Found {self.core.n_files:,} wav files")
            return

        if self.is_find_incompatible_wavs_active():
            self.str_status_bar.set(
                f"Analyzed {self.core.n_processed_files:,}/{self.core.n_files:,} files"
            )
            return

        if self.is_fix_incompatible_wavs_active():
            self.str_status_bar.set(f"Fixing {len(self.tree.selection()):,} files")
            return

        self.str_status_bar.set(
            f" Selected {len(self.tree.selection()):,}/{self.core.n_incompatible_files:,} incompatible wav's:"
        )

    def cleanup_threads(self):
        finished_actions = [
            action for action, thread in self.threads.items() if not thread.is_alive()
        ]
        for action in finished_actions:
            logger.info(f"Completed {action}")
            del self.threads[action]

        # Automatically start a find incompatible wavs action once we have a list of all wavs
        if FIND_WAVS in finished_actions:
            self._find_incompatible_wavs()

    def is_busy(self):
        return len(self.threads) > 0

    def is_find_wavs_active(self):
        return FIND_WAVS in self.threads

    def is_find_incompatible_wavs_active(self):
        return FIND_INCOMPATIBLE_WAVS in self.threads

    def is_fix_incompatible_wavs_active(self):
        return FIX_INCOMPATIBLE_WAVS in self.threads

    def run(self):
        self._tick()
        self.window.mainloop()

    def exit(self):
        self.window.destroy()
