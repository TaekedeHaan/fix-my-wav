import pathlib
import tkinter as tk
import tkinter.ttk as ttk
import threading
from tkinter import filedialog
import logging

from src.core import WavFinder, WavFixer, MetaFinder

logger = logging.getLogger(__name__)

FIND_WAVS = "find_wavs"
FIND_INCOMPATIBLE_WAVS = "find_incompatible_wavs"
FIX_INCOMPATIBLE_WAVS = "fix_incompatible_wavs"
SEARCH_META_DATA = "search_meta_data"


class UI:
    def __init__(
        self, wav_finder: WavFinder, wav_fixer: WavFixer, meta_finder: MetaFinder
    ):
        self.wav_finder = wav_finder
        self.wav_fixer = wav_fixer
        self.meta_finder = meta_finder

        # set callbacks
        self.wav_fixer.cb_found_incompatible_file = self._found_incompatible_file
        self.wav_fixer.cb_fixed_incompatible_file = self._fixed_incompatible_file

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
        tree = ttk.Treeview(
            frm_list_incompatible_wavs,
            columns=("file name", "path"),
        )

        yscrollbar = tk.Scrollbar(frm_list_incompatible_wavs, orient=tk.VERTICAL)
        yscrollbar.configure(command=tree.yview)
        tree.configure(yscrollcommand=yscrollbar.set)
        yscrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        xscrollbar = tk.Scrollbar(frm_list_incompatible_wavs, orient=tk.HORIZONTAL)
        tree.configure(xscrollcommand=xscrollbar.set)
        xscrollbar.configure(command=tree.xview)
        xscrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        tree.column("#0", anchor=tk.NW, stretch=False, width=50)
        tree.heading("#0", text="ID")
        tree.column("#1", anchor=tk.NW)
        tree.heading("#1", text="File name")
        tree.column("#2", anchor=tk.NW)
        tree.heading("#2", text="Path")

        tree.tag_configure("incompatible", background="red")
        tree.tag_configure("fixed", background="green")

        tree.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        frm_list_incompatible_wavs.pack(fill=tk.X)

        # browse
        frm_browse = ttk.Frame(window)
        ent_directory = ttk.Entry(frm_browse)
        ent_directory.insert(0, str(self.wav_finder.base_path))

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

        # Fix boken wavs
        btn_fix_incompatible_wav = ttk.Button(
            frm_find_incompatible_wavs,
            text="Fix incompatible wav's",
            command=self._fix_incompatible_wavs,
        )
        btn_fix_incompatible_wav.pack(side=tk.LEFT)
        frm_find_incompatible_wavs.pack(fill=tk.X)

        # Find meta data
        frm_find_meta_data = ttk.Frame(frm_execute)

        btn_find_find_meta_data = ttk.Button(
            frm_find_meta_data,
            text="Find meta data",
            command=self._find_meta_data,
        )
        btn_find_find_meta_data.pack(side=tk.LEFT)
        frm_find_meta_data.pack(fill=tk.X)

        # status bar
        self.str_status_bar = tk.StringVar()
        lbl_status = ttk.Label(
            window,
            anchor=tk.W,
            textvariable=self.str_status_bar,
        )
        lbl_status.pack(fill=tk.X, side=tk.BOTTOM)

        # Pack main frames
        frm_list_incompatible_wavs.pack(fill=tk.BOTH, expand=True)
        frm_browse.pack(fill=tk.X)
        frm_execute.pack(fill=tk.X, expand=False)

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
            initialdir=self.wav_finder.base_path,
            mustexist=True,
        )

        if not directory:
            logger.debug("No directory selected: nothing to do here")
            return

        path = pathlib.Path(directory)
        if self.wav_finder.base_path == path:
            logger.debug("Same directory selected: nothing to do here")
            return

        try:
            self.wav_finder.base_path = path
        except NotADirectoryError as e:
            logger.warning(
                f"Failed to set path to {self.wav_finder.base_path}, caught the following exception: {e}"
            )

        self.ent_directory.delete(0, tk.END)
        self.ent_directory.insert(0, str(self.wav_finder.base_path))
        self._find_wavs()

    def _find_wavs(self):
        if self.is_busy():
            return

        self._clear_tree_view()

        self.threads[FIND_WAVS] = threading.Thread(
            target=self.wav_finder.find_wav_files
        )
        self.threads[FIND_WAVS].start()

    def _find_incompatible_wavs(self):
        if self.is_busy():
            return

        self.threads[FIND_INCOMPATIBLE_WAVS] = threading.Thread(
            target=self.wav_fixer.find_incompatible_wav_files,
            args=(self.wav_finder.files,),
        )
        self.threads[FIND_INCOMPATIBLE_WAVS].start()

    def _fix_incompatible_wavs(self):
        if self.is_busy():
            return

        files = self._get_selected_tree_view_files(tag="incompatible")
        if not files:
            logger.info("No incompatible files have been selected")
            return

        self.threads[FIX_INCOMPATIBLE_WAVS] = threading.Thread(
            target=self.wav_fixer.fix_incompatible_wav_files, args=(files,)
        )
        self.threads[FIX_INCOMPATIBLE_WAVS].start()

    def _find_meta_data(self):
        if self.is_busy():
            return

        files = self._get_selected_tree_view_files()
        if not files:
            logger.info("No files have been selected")
            return

        if len(files) > 1:
            logger.info(
                "Currently only single files are supported, selecting the first file "
            )

        self.threads[SEARCH_META_DATA] = threading.Thread(
            target=self.meta_finder.search, args=(files[0],)
        )
        self.threads[SEARCH_META_DATA].start()

    def _tick(self):
        self.cleanup_threads()

        self._update_status_bar()

        # Update list if change was detected
        self._update_tree_view_items()

        # plan next tick
        self.window.after(self.update_rate_ms, self._tick)

    def _clear_tree_view(self):
        logger.debug("Clearing tree view")
        children = self.tree.get_children()
        self.tree.delete(*children)

    def _update_tree_view_items(self):
        items_per_tick = 1000

        # determine tree size
        children = self.tree.get_children()
        n_tree = len(children)
        n_files = self.wav_finder.n_files

        if n_files == n_tree:
            return

        if n_files < len(children):
            logger.warning(
                f"Something is going wrong as the tree of {n_tree} is longer than the files {n_files}"
            )
            self._clear_tree_view()

        i_start = n_tree
        i_end = min(i_start + items_per_tick, n_files)
        new_files = self.wav_finder.files[i_start:i_end]

        # insert new items
        for i, file in enumerate(new_files):
            iid = i + n_tree
            self.tree.insert(
                "",
                "end",
                text=str(iid),
                iid=iid,
                values=(file.name, file.parent),
            )

    def _get_tree_view_item(self, file: pathlib.Path):
        file_name = file.name
        file_path = file.parent

        children = self.tree.get_children("")
        for item in children:
            values = self.tree.item(item, "values")
            if not values:
                logger.warning("Tree contains items which are empty")
                continue
            if len(values) < 2:
                logger.warning("Tree contains items with wrong number of values")
                continue

            item_name = values[0]
            item_path = values[1]
            if file_name == item_name and str(file_path) == item_path:
                return item

        return None

    def _get_selected_tree_view_files(self, tag: str | None = None):
        files: list[pathlib.Path] = []
        indices = self.tree.selection()
        if not indices:
            logger.info("No items selected")
            return files

        items = [self.tree.item(index) for index in indices]

        for item in items:
            if tag is not None and tag not in item["tags"]:
                continue

            file = pathlib.Path(item["values"][1]) / item["values"][0]
            files.append(file)

        return files

    def _found_incompatible_file(self, file: pathlib.Path):
        logger.info("Found incompatible wav is called")

        item = self._get_tree_view_item(file)
        if item is None:
            # This is possible if we find a file while still adding the items to the tree view, we need to add some memory such that it can be added later
            logger.error(f"Failed to find item matching to incompatible {file}")
            return

        self.tree.item(item, tags=("incompatible",))
        self.tree.move(item, "", 0)

    def _fixed_incompatible_file(self, file: pathlib.Path):
        logger.info("Fixed incompatible wav is called")
        item = self._get_tree_view_item(file)
        if item is None:
            # This is possible if we find a file while still adding the items to the tree view, we need to add some memory such that it can be added later
            logger.error(f"Failed to find item matching to fixed {file}")
            return

        self.tree.item(item, tags=("fixed",))

    def _update_tree_column_width(self, iids: list[int] | None = None):
        # TODO: Too slow
        factor = 6
        longest_file_name = 0
        longest_file_path = 0

        iids = iids if iids is not None else []
        for iid in iids:
            values = self.tree.item(iid)["values"]
            longest_file_name = max(len(values[0]), longest_file_name)
            longest_file_path = max(len(values[1]), longest_file_path)

        column = self.tree.column("#1")
        old_width = column["minwidth"] if column else 0
        new_width = longest_file_name * factor
        if new_width > old_width:
            self.tree.column("#1", minwidth=new_width)

        column = self.tree.column("#2")
        old_width = column["minwidth"] if column else 0
        new_width = longest_file_path * factor
        if new_width > old_width:
            self.tree.column("#2", minwidth=new_width)

    def _update_status_bar(self):
        if self.is_find_wavs_active():
            self.str_status_bar.set(f"Found {self.wav_finder.n_files:,} wav file(s)")
            return

        if self.is_find_incompatible_wavs_active():
            self.str_status_bar.set(
                f"Analyzed {self.wav_fixer.n_processed_files:,}/{self.wav_finder.n_files:,} file(s)"
            )
            return

        if self.is_fix_incompatible_wavs_active():
            self.str_status_bar.set(f"Fixing {len(self.tree.selection()):,} file(s)")
            return

        self.str_status_bar.set(f" Selected {len(self.tree.selection()):,} file(s)")

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
