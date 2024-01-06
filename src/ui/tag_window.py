import logging
import tkinter as tk
import tkinter.ttk as ttk

from src.core import MetaFinder
from src.core.tag_reader import Tag, DiscogsTagReader

logger = logging.getLogger(__name__)


class TagWindow(tk.Toplevel):
    WIDTH = 600
    HEIGHT = 200
    TAGS = ["status", "title", "artists", "album", "year", "date", "genres", "#"]

    def __init__(
        self,
        meta_finder: MetaFinder,
        master: tk.Tk | None = None,
    ):
        super().__init__(master=master)
        self.geometry(f"{self.WIDTH}x{self.HEIGHT}")
        self.center()

        self.meta_finder = meta_finder

        # fill window
        self.title("Tag finder")

        frm_label = ttk.Frame(self)
        lbl = tk.Label(
            frm_label,
            text=f"Looking for tags for {meta_finder.file_tag_reader.file.name}",
        )
        lbl.pack()
        frm_label.pack()

        frm_tree = ttk.Frame(self)
        self.tree = self._construct_tree_view(frm_tree)
        frm_tree.pack(fill=tk.BOTH, expand=True)

        # settings
        self.frequency = 50
        self.update_rate_ms = round(1000 / self.frequency)

        # block interaction with the underlying window
        self.grab_set()

        # to detect change
        self.files_tags: list[str] = []
        self.discogs_tags: list[str] = []

    def _get_selected_item(self, event: tk.Event):
        col = self.tree.identify_column(event.x)

        if col == "#0":
            logger.debug("Selected tag column")
            return
        elif col == "#1":
            logger.debug("Selected file tag column")
            return self.meta_finder.file_tag_reader
        elif col == "#2":
            logger.debug("Selected Discogs tag column")
            return self.meta_finder.discogs_tag_reader

    def _click_tree(self, event: tk.Event):
        self.tree.item(self.tree.focus())
        tag_reader = self._get_selected_item(event)

        if not isinstance(tag_reader, DiscogsTagReader):
            return

        # for opening the link in browser
        if not tag_reader.url:
            logger.debug("url is empty")
            return

        logger.info(f"Opening {tag_reader.url} in web browser")
        import webbrowser

        webbrowser.open("{}".format(tag_reader.url))

    def _construct_tree_view(self, frm: ttk.Frame):
        # tree view
        tree = ttk.Treeview(
            frm,
            columns=("tag", "file", "Discogs"),
        )

        tree.column("#0", anchor=tk.NW, stretch=False, width=50)
        tree.heading("#0", text="Tag")
        tree.column("#1", anchor=tk.NW)
        tree.heading("#1", text="File")
        tree.column("#2", anchor=tk.NW)
        tree.heading("#2", text="Discogs")

        tree.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        tree.bind(sequence="<Double-1>", func=self._click_tree)
        return tree

    def _clear_tree_view(self):
        logger.debug("Clearing tree view")
        children = self.tree.get_children()
        self.tree.delete(*children)

    def _update_tree_view(self):
        files_tags = self.collect_file_tags()
        discogs_tags = self.collect_discogs_tags()

        if files_tags == self.files_tags and discogs_tags == self.discogs_tags:
            return

        self._clear_tree_view()
        for iid, tags in enumerate(zip(self.TAGS, files_tags, discogs_tags)):
            self.tree.insert(
                "",
                "end",
                text=tags[0],
                iid=iid,
                values=tags[1:],
            )

        self.files_tags = files_tags
        self.discogs_tags = discogs_tags

    def collect_discogs_tags(self) -> list[str]:
        discogs_tag_reader = self.meta_finder.discogs_tag_reader
        if not discogs_tag_reader:
            return ["searching"] + (len(self.TAGS) - 1) * ["-"]

        return ["found"] + self.collect_tags(discogs_tag_reader)

    def collect_file_tags(self) -> list[str]:
        file_tag_reader = self.meta_finder.file_tag_reader
        return ["found"] + self.collect_tags(file_tag_reader)

    def collect_tags(self, tag_reader: Tag):
        missing_tag = "-"
        title = tag_reader.title or missing_tag
        artists = ", ".join(tag_reader.artists) or missing_tag
        album = tag_reader.album or missing_tag
        year = tag_reader.year or missing_tag
        date = tag_reader.date or missing_tag
        genres = ", ".join(tag_reader.genres) or missing_tag
        track_number = tag_reader.track_number or missing_tag
        return [title, artists, album, year, date, genres, track_number]

    def center(self):
        w = self.WIDTH  # self.winfo_width()
        h = self.HEIGHT  # self.winfo_height()
        x = self.master.winfo_x() + (self.master.winfo_width() - w) / 2
        y = self.master.winfo_y() + (self.master.winfo_height() - h) / 2

        self.geometry(f"+{x:.0f}+{y:.0f}")

    def _tick(self):
        self._update_tree_view()

        # plan next tick
        self.after(self.update_rate_ms, self._tick)

    def run(self):
        self._tick()
        self.mainloop()
