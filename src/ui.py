import pathlib
import tkinter as tk
import tkinter.ttk as ttk

from core import Core
from tkinter import filedialog


class UI:
    def __init__(self, core: Core):
        self.core = core

        window = tk.Tk()

        # browse
        frm_browse = tk.Frame()

        label = ttk.Label(frm_browse, text="Configure")
        label.pack(side=tk.TOP, anchor=tk.NW)

        ent_directory = tk.Entry(frm_browse)
        ent_directory.insert(0, str(self.core.base_path))

        btn_browse = tk.Button(
            frm_browse, text="Browse", command=self.__update_direcotry
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

        frm_find_wavs.pack(fill=tk.X, side=tk.TOP)

        # find incompatible wavs
        frm_find_incompatible_wavs = tk.Frame(frm_execute)

        btn_find_incompatible_wav = tk.Button(
            frm_find_incompatible_wavs,
            text="Find incompatible wav's",
            command=self.__find_incompatible_wavs,
        )
        btn_find_incompatible_wav.pack(side=tk.LEFT)

        self.str_var_suspicious_wavs = tk.StringVar()
        self.str_var_suspicious_wavs.set(f"Found {self.core.n_suspicious_files} files")
        lbl_suspicious_wavs = tk.Label(
            frm_find_incompatible_wavs, textvariable=self.str_var_suspicious_wavs
        )
        lbl_suspicious_wavs.pack(side=tk.LEFT)
        frm_find_incompatible_wavs.pack(fill=tk.X)

        listbox = tk.Listbox(frm_execute)
        for i, file in enumerate(self.core.suspicious_files):
            listbox.insert(i, file.name)

        listbox.pack(fill=tk.X, side=tk.BOTTOM)

        # Pack main frames
        frm_browse.pack(fill=tk.X)
        frm_execute.pack(fill=tk.X)

        # set members
        self.window = window
        self.ent_directory = ent_directory
        self.listbox = listbox

    def __update_direcotry(self):
        directory = filedialog.askdirectory(
            initialdir=self.core.base_path, mustexist=True
        )

        try:
            self.core.base_path = pathlib.Path(directory)
        except NotADirectoryError as e:
            print(
                f"Failed to set path to {self.core.base_path}, caught the following exception: {e}"
            )

        self.ent_directory.delete(0, tk.END)
        self.ent_directory.insert(0, str(self.core.base_path))
        self.__find_wavs()

    def __find_wavs(self):
        self.core.find_wav_files()
        self.str_var_wavs.set(f"Found {self.core.n_files} files")
        self.window.update_idletasks()

    def __find_incompatible_wavs(self):
        self.listbox.delete(0, tk.END)
        self.core.find_suspicious_wav_files()

        self.str_var_suspicious_wavs.set(f"Found {self.core.n_suspicious_files} files")
        self.window.update_idletasks()

        for i, file in enumerate(self.core.suspicious_files):
            self.listbox.insert(i, file.name)

    def run(self):
        self.window.mainloop()

    def exit(self):
        self.window.destroy()
