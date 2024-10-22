import logging
import tkinter as tk
import tkinter.ttk as ttk
import webbrowser  # for opening search results in your webbrowser

from src.ui import constants
from src.ui.utils.displacement_tracker import DisplacementTracker
from src.core import MetaFinder
from src.core.tag_reader import Tag, DiscogsTagReader

logger = logging.getLogger(__name__)

ROW_HEIGHT = 25
TAGS = ["Status", "Title", "Artists", "Album", "Year", "Date", "Genres", "#"]

WIDTH = 600
HEIGHT = len(TAGS) * ROW_HEIGHT + 60
MISSING_COLOR = "grey"


class TagWindow(tk.Toplevel):

    def __init__(
        self,
        meta_finder: MetaFinder,
        master: tk.Tk | None = None,
    ):
        super().__init__(master=master)
        self.focus_set()
        self.geometry(f"{WIDTH}x{HEIGHT}")

        if self.master:
            self.transient(master)

        self.meta_finder = meta_finder
        self.menu: tk.Menu | None = None
        self.master_displacement_tracker = DisplacementTracker(self.master)
        self.displacement_tracker = DisplacementTracker(self)

        self.x_disp_command_total = 0.0
        self.y_disp_command_total = 0.0

        self.is_first_tick = True

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
        self.update_rate_ms = round(1000 / constants.UPDATE_FREQUENCY)

        # block interaction with the underlying window
        self.grab_set()

        # to detect change
        self.selected_tags: list[str] = []
        self.files_tags: list[str] = []
        self.discogs_tags: list[str] = []

    def _get_selected_tag(self, event: tk.Event):
        col = self.tree.identify_column(event.x)

        if col == "#0":
            logger.debug("Selected tag column")
            return
        elif col == "#1":
            logger.debug("Selected file tag writer column")
            return self.meta_finder.file_tag_writer
        elif col == "#2":
            logger.debug("Selected file tag reader column")
            return self.meta_finder.file_tag_reader
        elif col == "#3":
            logger.debug("Selected Discogs tag reader column")
            return self.meta_finder.discogs_tag_reader

    def _options_tree(self, event: tk.Event):
        logger.debug("Show options")
        self.tree.item(self.tree.focus())
        self.menu = tk.Menu(self, tearoff=0)

        open_item = lambda: self._open_item(event)
        self.menu.add_command(label="open", command=open_item)

        select_items = lambda: self._select_items(event)
        self.menu.add_command(label="select", command=select_items)

        try:
            self.menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.menu.grab_release()

    def _open_item(self, event: tk.Event):
        logger.debug("Open item")
        self.tree.item(self.tree.focus())
        selected_tag = self._get_selected_tag(event)

        if not isinstance(selected_tag, DiscogsTagReader):
            return

        if not selected_tag.url:
            logger.debug("url is empty")
            return

        logger.info(f"Opening {selected_tag.url} in web browser")
        webbrowser.open("{}".format(selected_tag.url))

    def _select_items(self, event: tk.Event):
        logger.debug("Select item(s)")
        self.tree.item(self.tree.focus())

        # select tags
        file_tag_writer = self.meta_finder.file_tag_writer
        selected_tag = self._get_selected_tag(event)
        if not selected_tag:
            logger.debug("No tag selected")
            return

        selected_fields = self.tree.selection()

        # TODO: we need some way tu update a set of tags from an other object
        for iid in selected_fields:
            if iid == "title":
                file_tag_writer.title = selected_tag.title
            if iid == "artists":
                file_tag_writer.artists = selected_tag.artists
            if iid == "album":
                file_tag_writer.album = selected_tag.album
            elif iid == "year":
                file_tag_writer.year = selected_tag.year
            elif iid == "date":
                file_tag_writer.date = selected_tag.date
            elif iid == "genres":
                file_tag_writer.genres = selected_tag.genres

    def _construct_tree_view(self, frm: ttk.Frame):
        # tree view
        tree = ttk.Treeview(
            frm,
            columns=("tag", "selected", "file", "discogs"),
        )

        style = ttk.Style()
        style.configure(
            "Treeview",
            background="white",
            foreground="black",
            rowheight=ROW_HEIGHT,
            fieldbackground="white",
        )
        style.map(
            "Treeview",
            foreground=[("selected", "black")],
            background=[("selected", "white")],
        )

        tree.column("#0", anchor=tk.NW, stretch=False, width=50)
        tree.heading("#0", text="Tag")
        tree.column("#1", anchor=tk.NW)
        tree.heading("#1", text="Selected")
        tree.column("#2", anchor=tk.NW)
        tree.heading("#2", text="File")
        tree.column("#3", anchor=tk.NW)
        tree.heading("#3", text="Discogs")

        # tree.tag_configure("missing", background=MISSING_COLOR)

        tree.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        tree.bind(sequence="<Double-1>", func=self._open_item)
        tree.bind(sequence="<Button-3>", func=self._options_tree)
        return tree

    def _clear_tree_view(self):
        logger.debug("Clearing tree view")
        children = self.tree.get_children()
        self.tree.delete(*children)

    def _update_tree_view(self):
        selected_tags = [""] + self.collect_tags(self.meta_finder.file_tag_writer)
        file_tags = self.collect_file_tags()
        discogs_tags = self.collect_discogs_tags()

        if (
            selected_tags == self.selected_tags
            and file_tags == self.files_tags
            and discogs_tags == self.discogs_tags
        ):
            return

        self._clear_tree_view()
        for tags in zip(TAGS, selected_tags, file_tags, discogs_tags):
            iid = tags[0].lower()
            found = tags[1] != "-"
            self.tree.insert(
                "",
                "end",
                text=tags[0],
                iid=iid,
                values=tags[1:],
                tags=("found" if found else "missing",),
            )

        # update
        self.selected_tags = selected_tags
        self.files_tags = file_tags
        self.discogs_tags = discogs_tags

    def _update_position(self):
        if self.is_first_tick:
            self.center()
            return

        x = self.winfo_x()
        y = self.winfo_y()
        x_master_displacement, y_master_displacement = (
            self.master_displacement_tracker.get_displacement()
        )

        x_error = x_master_displacement - self.x_disp_command_total
        y_error = y_master_displacement - self.y_disp_command_total

        # a simple P(ID) controller to smoothen the motion
        x_disp_command = round(constants.WINDOW_TRACKING_STIFFNESS * x_error)
        y_disp_command = round(constants.WINDOW_TRACKING_STIFFNESS * y_error)

        self.x_disp_command_total = self.x_disp_command_total + x_disp_command
        self.y_disp_command_total = self.y_disp_command_total + y_disp_command

        self.geometry(f"+{x + int(x_disp_command)}+{y + int(y_disp_command)}")

    def collect_discogs_tags(self) -> list[str]:
        discogs_tag_reader = self.meta_finder.discogs_tag_reader
        if not discogs_tag_reader:
            return ["searching"] + (len(TAGS) - 1) * ["-"]

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
        w = WIDTH  # self.winfo_width()
        h = HEIGHT  # self.winfo_height()
        if self.master:
            x = self.master.winfo_x() + (self.master.winfo_width() - w) / 2
            y = self.master.winfo_y() + (self.master.winfo_height() - h) / 2
        else:
            x = 600
            y = 500

        self.geometry(f"+{x:.0f}+{y:.0f}")

    def _tick(self):
        self._update_tree_view()
        self._update_position()

        self.is_first_tick = False

        # plan next tick
        self.after(self.update_rate_ms, self._tick)

    def run(self):
        self._tick()
        self.mainloop()
