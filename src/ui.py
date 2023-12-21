import pathlib
import tkinter as tk
import tkinter.ttk as ttk
import threading
from tkinter import filedialog
import logging

from src.core import Core

logger = logging.getLogger(__name__)


class UI:
    def __init__(self, core: Core):
        self.core = core

        # An easy but dirty way to detect whether these have been changes since the last call
        self.suspicious_files = []

        window = tk.Tk()

        # browse
        frm_browse = tk.Frame(window)

        label = ttk.Label(frm_browse, text="Configure")
        label.pack(side=tk.TOP, anchor=tk.NW)

        ent_directory = tk.Entry(frm_browse)
        ent_directory.insert(0, str(self.core.base_path))

        btn_browse = tk.Button(
            frm_browse, text="Browse", command=self.__update_directory
        )

        ent_directory.pack(fill=tk.X, side=tk.LEFT, expand=True)
        btn_browse.pack(side=tk.LEFT)

        ### execute
        frm_execute = tk.Frame(window)

        label = ttk.Label(frm_execute, text="Execute")
        label.pack(side=tk.TOP, anchor=tk.NW)

        # Find wavs
        frm_find_wavs = tk.Frame(frm_execute)
        btn_find_wav = tk.Button(
            frm_find_wavs, text="Find wav's", command=self.__find_wavs
        )
        btn_find_wav.pack(side=tk.LEFT)

        self.str_var_wavs = tk.StringVar()
        self.str_var_wavs.set(f"Found {self.core.n_files} files")
        lbl_wavs = tk.Label(frm_find_wavs, textvariable=self.str_var_wavs)
        lbl_wavs.pack(side=tk.LEFT)

        frm_find_wavs.pack(fill=tk.X, side=tk.LEFT)

        # find incompatible wavs
        frm_find_incompatible_wavs = tk.Frame(frm_execute)

        btn_find_incompatible_wav = tk.Button(
            frm_find_incompatible_wavs,
            text="Find incompatible wav's",
            command=self.__find_incompatible_wavs,
        )
        btn_find_incompatible_wav.pack(side=tk.LEFT)

        self.str_var_analyzed_wavs = tk.StringVar()
        lbl_analyzed_wavs = tk.Label(
            frm_find_incompatible_wavs, textvariable=self.str_var_analyzed_wavs
        )
        lbl_analyzed_wavs.pack(side=tk.LEFT)
        frm_find_incompatible_wavs.pack(fill=tk.X, side=tk.LEFT)

        # list incompatible wavs
        frm_list_incompatible_wavs = tk.Frame(window)

        label = ttk.Label(frm_list_incompatible_wavs, text="Incompatible wav's")
        label.pack(side=tk.TOP, anchor=tk.NW)

        # tree view
        frm_tree_view = tk.Frame(frm_list_incompatible_wavs)
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

        # results
        self.str_var_suspicious_wavs = tk.StringVar()
        lbl_suspicious_wavs = tk.Label(
            frm_list_incompatible_wavs,
            textvariable=self.str_var_suspicious_wavs,
        )
        lbl_suspicious_wavs.pack(side=tk.TOP, anchor=tk.NW)

        self.str_var_selected_wavs = tk.StringVar()
        lbl_selected_wavs = tk.Label(
            frm_list_incompatible_wavs,
            textvariable=self.str_var_selected_wavs,
        )
        lbl_selected_wavs.pack(side=tk.TOP, anchor=tk.NW)

        # Pack main frames
        frm_browse.pack(fill=tk.X)
        frm_execute.pack(fill=tk.X)
        frm_list_incompatible_wavs.pack(fill=tk.X)

        # set members
        self.window = window
        self.ent_directory = ent_directory
        self.tree = tree

        # settings
        self.frequency = 50
        self.update_rate_ms = round(1000 / self.frequency)

    def __update_directory(self):
        directory = filedialog.askdirectory(
            initialdir=self.core.base_path, mustexist=True
        )

        try:
            self.core.base_path = pathlib.Path(directory)
        except NotADirectoryError as e:
            logger.warning(
                f"Failed to set path to {self.core.base_path}, caught the following exception: {e}"
            )

        self.ent_directory.delete(0, tk.END)
        self.ent_directory.insert(0, str(self.core.base_path))
        self.__find_wavs()

    def __tick(self):
        self.str_var_wavs.set(f"Found {self.core.n_files:,} wav files")
        self.str_var_analyzed_wavs.set(
            f"Analyzed {self.core.n_processed_files:,}/{self.core.n_files:,} files"
        )
        self.str_var_suspicious_wavs.set(
            f"{self.core.n_suspicious_files:,}/{self.core.n_files:,} are incompatible"
        )

        self.str_var_selected_wavs.set(
            f"Selected {len(self.tree.selection()):,}/{self.core.n_suspicious_files:,} files"
        )

        # Update list if change was detected
        if self.suspicious_files != self.core.suspicious_files:
            self.__update_tree_view()

        # plan next tick
        self.window.after(self.update_rate_ms, self.__tick)

    def __update_tree_view(self):
        factor = 6
        longest_file_name = 0
        longest_file_path = 0

        self.suspicious_files = self.core.suspicious_files
        self.tree.delete(*self.tree.get_children())
        for i, file in enumerate(self.core.suspicious_files):
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

    def __find_wavs(self):
        thread = threading.Thread(target=self.core.find_wav_files)
        thread.start()

    def __find_incompatible_wavs(self):
        thread = threading.Thread(target=self.core.find_suspicious_wav_files)
        thread.start()

    def run(self):
        self.__tick()
        self.window.mainloop()

    def exit(self):
        self.window.destroy()
