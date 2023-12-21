import pathlib
import tkinter as tk
import tkinter.ttk as ttk

from core import Core
from tkinter import filedialog


class UI:
    def __init__(self):
        self.core = Core()

        window = tk.Tk()
        frame = tk.Frame()

        label = ttk.Label(frame, text="Hello, Tkinter")
        label.pack()

        ent_directory = tk.Entry(frame)
        ent_directory.insert(0, self.core.base_path)
        ent_directory.pack(fill=tk.X)

        btn_browse = tk.Button(frame, text="Browse", command=self.__update_direcotry)
        btn_browse.pack()

        btn_find_wav = tk.Button(frame, text="Find wav's", command=self.__find_wavs)
        btn_find_wav.pack()

        btn_find_incompatible_wav = tk.Button(
            frame, text="Find incompatible wav's", command=self.__find_incompatible_wavs
        )
        btn_find_incompatible_wav.pack()

        listbox = tk.Listbox(frame)
        for i, file in enumerate(self.core.suspicious_files):
            listbox.insert(i, file.name)

        listbox.pack(fill=tk.X)

        frame.pack(fill=tk.X)

        self.window = window
        self.ent_directory = ent_directory
        self.listbox = listbox

    def __update_direcotry(self):
        self.core.base_path = pathlib.Path(
            filedialog.askdirectory(initialdir=self.core.base_path, mustexist=True)
        )
        self.ent_directory.delete(1, tk.END)  # Remove current text in entry
        self.ent_directory.insert(0, self.core.base_path)  # Insert the 'path'

    def __find_wavs(self):
        self.core.find_wav_files()

    def __find_incompatible_wavs(self):
        self.listbox.delete(0, tk.END)
        self.core.find_suspicious_wav_files()
        for i, file in enumerate(self.core.suspicious_files):
            self.listbox.insert(i, file.name)

    def run(self):
        self.window.mainloop()

    def exit(self):
        self.window.destroy()


def main():
    ui = UI()
    ui.run()


if __name__ == "__main__":
    main()
