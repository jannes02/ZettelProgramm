from typing import List

from reportlab.lib.pagesizes import A3, A4
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, Frame

from src.backend.event_description import EventDescription
import src.backend.styles as styles


class FlyerBuilder:

    # Maximum number of events that is guaranteed to fit (4 columns / 2 pages).
    MAX_EVENTS = 12

    # Upper bound for the extra gap inserted between events in a column. Keeps
    # sparse columns compact (top-aligned) rather than spread over the full page.
    MAX_EVENT_GAP = 40

    def __init__(self, output_file_name):
        self.filename = output_file_name
        self.width, self.height = A3
        self.paragraph_padding = 16
        self.frame_top_margin = 8
        self.bottom_margin = 50  # bottom safety margin
        self.c = canvas.Canvas(self.filename, pagesize=A3)
        self.last_line = 0.0
        self.color = styles.BLACK
        self.is_debug = False
        self.count = 0
        self.header_height = 0.0
        self.title = ""
        self.date = ""

    # ------------------------------------------------------------------ #
    #  Main flow
    # ------------------------------------------------------------------ #
    def build(self, title="Heute im Haus", date="",
              event_descriptions: List[EventDescription] = None, first_run=True) -> int:
        if event_descriptions is None:
            print("Keine Events gefunden!")
            return -1

        self.title = title
        self.date = date
        self.count = len(event_descriptions)

        if self.count > self.MAX_EVENTS:
            print(f"Warnung: mehr als {self.MAX_EVENTS} Events - Inhalt kann abgeschnitten werden.")

        layout = self._decide_layout(event_descriptions)

        self._setup_canvas(layout)

        if layout == "landscape":
            self._render_multicolumn(event_descriptions)
        else:
            self._render_singlecolumn(event_descriptions)

        self.c.showPage()
        self.c.save()
        return 0

    def _decide_layout(self, events) -> str:
        """Returns 'a4', 'portrait' or 'landscape'.

        1 event    -> A4 (landscape, as before)
        2-3 events -> A3 portrait, single column (3 always fits on one page)
        4 events   -> A3 portrait single column; only switches to A3 landscape
                      two-column layout if the content would overflow the page
        5+ events  -> always A3 landscape, two-column layout
        """
        if self.count == 1:
            return "a4"
        if self.count <= 3:
            return "portrait"
        if self.count >= 5:
            return "landscape"

        # 4 events: measure whether the single-column (portrait) layout fits
        self._apply_dims("portrait")
        usable = (self.height - 160) - self.bottom_margin
        total = sum(self._measure_single(ed) for ed in events)
        return "portrait" if total <= usable else "landscape"

    # ------------------------------------------------------------------ #
    #  Canvas / dimensions
    # ------------------------------------------------------------------ #
    def _apply_dims(self, layout: str):
        if layout == "a4":
            self.height, self.width = A4[0], A4[1]          # A4 landscape
            self.frame_top_margin = 16
        elif layout == "portrait":
            self.height, self.width = A3[1], A3[0]          # A3 portrait
            self.frame_top_margin = 16 / (self.count or 1)
        else:  # landscape
            self.height, self.width = A3                    # A3 landscape
            # Multi-column layout is packed a bit tighter (closer to the Word
            # template): a smaller inter-element margin compresses each event
            # block and lets a column hold slightly more before it breaks.
            # paragraph_padding stays >=12 because ReportLab frames reserve
            # ~12 pt of internal padding - smaller values silently drop text.
            self.frame_top_margin = 2

    def _setup_canvas(self, layout: str):
        self._apply_dims(layout)
        self.c = canvas.Canvas(self.filename, pagesize=(self.width, self.height))
        if layout == "a4":
            print("Recompile in A4 Format")
        elif layout == "portrait":
            print("Recompile in A3 Format - portrait")
        else:
            print("Recompile in A3 Format - landscape")

    # ------------------------------------------------------------------ #
    #  Header
    # ------------------------------------------------------------------ #
    def _build_header(self, title, date) -> float:
        heading = Paragraph(title, styles.HEADING_STYLE)
        date_p = Paragraph(date, styles.DATE_STYLE)

        frame_heading = Frame(50, self.height - 150, self.width / 2 - 50, 100, showBoundary=self.is_debug)
        frame_date = Frame(self.width / 2, self.height - 150, self.width / 2 - 50, 100, showBoundary=self.is_debug)

        self.c.setStrokeColor(styles.BLACK)
        self.c.setLineWidth(1)
        frame_heading.addFromList([heading], self.c)
        frame_date.addFromList([date_p], self.c)

        self.header_height = self.height - 160
        return self.header_height

    # ------------------------------------------------------------------ #
    #  Single-column renderer (1 / 2 / 3-4 events)
    # ------------------------------------------------------------------ #
    def _render_singlecolumn(self, events):
        self._build_header(self.title, self.date)

        heights = [self._measure_single(ed) for ed in events]
        usable = self.header_height - self.bottom_margin
        n = len(events)
        # Distribute the remaining space evenly as gaps (vertical justification).
        # For a single event keep the original behaviour (top aligned).
        gap = max(0.0, usable - sum(heights)) / (n + 1) if n > 1 else 0.0

        top = self.header_height
        for ed in events:
            top -= gap
            top = self._draw_event_single(ed, top)

    # ------------------------------------------------------------------ #
    #  Multi-column / multi-page renderer (4-event overflow, 5+)
    # ------------------------------------------------------------------ #
    def _render_multicolumn(self, events):
        self.header_height = self.height - 160
        # Hard cap: down to just before the page edge (content is never cut,
        # only the safety margin may be eaten into).
        fit_cap = self.header_height - 10

        heights = [self._measure_multi(ed) for ed in events]
        # Fill columns front to back: pack each column up to the cap before
        # starting the next one. This keeps the first columns (and the first
        # page) as full as possible and leaves any short column at the end
        # (e.g. 3-2, 2-2-1). If the first events are large, the next column
        # simply starts earlier. It also uses the minimum number of columns,
        # so a second page is only started once the first one is really full.
        groups = self._greedy_partition(heights, fit_cap)
        # More than 4 columns means the content exceeds two A3 pages; fall back
        # to a balanced split across the 4 available columns (best effort).
        if len(groups) > 4:
            groups = self._balanced_partition(heights, 4)

        for ci, (start, end) in enumerate(groups):
            page = ci // 2
            col = ci % 2

            if col == 0:
                if page > 0:
                    self.c.showPage()
                self._build_header(self.title, self.date)

            left_anchor = 25 if col == 0 else 25 + self.width / 2

            group_events = events[start:end]
            group_heights = heights[start:end]
            usable = self.header_height - self.bottom_margin
            m = len(group_events)
            # Distribute the remaining space AFTER each event, not before. That
            # way the first separator line of every column starts exactly at
            # header_height -> the top lines of all columns share the same height
            # (table look). The gap is capped so sparse columns pack towards the
            # top (compressed, like the Word template) instead of stretching the
            # few events across the whole page height.
            gap = max(0.0, usable - sum(group_heights)) / m if m > 0 else 0.0
            gap = min(gap, self.MAX_EVENT_GAP)

            top = self.header_height
            for ed in group_events:
                top = self._draw_event_multi(ed, left_anchor, top)
                top -= gap

    # ------------------------------------------------------------------ #
    #  Column / page partitioning
    # ------------------------------------------------------------------ #
    @staticmethod
    def _greedy_columns(heights, cap) -> int:
        """Minimum number of columns when filling sequentially (first-fit)."""
        cols, cur = 1, 0.0
        for h in heights:
            if cur > 0 and cur + h > cap:
                cols += 1
                cur = h
            else:
                cur += h
        return cols

    @staticmethod
    def _greedy_partition(heights, cap):
        """Pack events into contiguous columns front to back: keep adding to the
        current column until the next event would exceed the cap, then start a
        new column. Earlier columns are filled first and any leftover (short)
        column ends up last. Uses the minimum number of contiguous columns."""
        groups = []
        start = 0
        cur = 0.0
        for i, h in enumerate(heights):
            if i > start and cur + h > cap:
                groups.append((start, i))
                start = i
                cur = h
            else:
                cur += h
        groups.append((start, len(heights)))
        return groups

    @staticmethod
    def _minimax_value(heights, k) -> float:
        """Smallest possible largest column sum for k columns (DP minimax)."""
        n = len(heights)
        if n == 0:
            return 0.0
        k = max(1, min(k, n))
        pre = [0.0]
        for h in heights:
            pre.append(pre[-1] + h)
        inf = float("inf")
        dp = [[inf] * (k + 1) for _ in range(n + 1)]
        dp[0][0] = 0.0
        for i in range(1, n + 1):
            for j in range(1, min(i, k) + 1):
                for pp in range(j - 1, i):
                    val = max(dp[pp][j - 1], pre[i] - pre[pp])
                    if val < dp[i][j]:
                        dp[i][j] = val
        return dp[n][k]

    def _needed_columns(self, heights, cap) -> int:
        """Fewest columns (max. 4) where every column still fits on the page
        (balanced via minimax). This keeps the layout compact - only as many
        columns/pages as necessary are used. If it does not fit in <=4 columns
        (genuine over-capacity), 4 columns are used."""
        n = len(heights)
        if n == 0:
            return 1
        max_cols = min(4, n)
        for k in range(1, max_cols + 1):
            if self._minimax_value(heights, k) <= cap + 1e-6:
                return k
        return max_cols

    @staticmethod
    def _balanced_partition(heights, k, min_size=1):
        """Split the ordered list into <=k contiguous groups so that the largest
        column sum is minimised (DP minimax). Order is preserved. With min_size
        every group is forced to contain at least min_size items; if that is
        infeasible (n < k * min_size) it falls back to min_size = 1."""
        n = len(heights)
        if n == 0:
            return []
        k = max(1, min(k, n))
        min_size = max(1, min_size)

        pre = [0.0]
        for h in heights:
            pre.append(pre[-1] + h)

        inf = float("inf")
        dp = [[inf] * (k + 1) for _ in range(n + 1)]
        cut = [[0] * (k + 1) for _ in range(n + 1)]
        dp[0][0] = 0.0
        for i in range(1, n + 1):
            for j in range(1, min(i, k) + 1):
                # group j is [p, i]; it must hold >= min_size items and leave
                # room for the earlier j-1 groups (each also >= min_size).
                lo = (j - 1) * min_size
                hi = i - min_size
                for p in range(max(j - 1, lo), hi + 1):
                    if dp[p][j - 1] == inf:
                        continue
                    val = max(dp[p][j - 1], pre[i] - pre[p])
                    if val < dp[i][j]:
                        dp[i][j] = val
                        cut[i][j] = p

        if dp[n][k] == inf:
            # min_size made the split infeasible -> retry without the constraint
            return FlyerBuilder._balanced_partition(heights, k, 1)

        groups, i, j = [], n, k
        while j > 0:
            p = cut[i][j]
            groups.append((p, i))
            i, j = p, j - 1
        groups.reverse()
        return groups

    # ------------------------------------------------------------------ #
    #  Height calculation (measuring and drawing share these formulas)
    # ------------------------------------------------------------------ #
    def _heights_single(self, host, event_time, title, description, location):
        pad = self.paragraph_padding
        host_h = max(host.wrap((self.width - 100) * 3 / 4, 1000)[1],
                     event_time.wrap((self.width - 100) * 1 / 4, 1000)[1]) + pad
        title_h = title.wrap(self.width - 100, 1000)[1] + pad
        desc_h = description.wrap((self.width - 100) * 7 / 8, 1000)[1] + pad
        loc_h = location.wrap(self.width - 100, 1000)[1] + pad
        return host_h, title_h, desc_h, loc_h

    def _heights_multi(self, host, event_time, title, description, location):
        pad = self.paragraph_padding
        host_h = max(host.wrap((self.width - 100) * 3 / 4, 1000)[1],
                     event_time.wrap((self.width - 100) * 1 / 4, 1000)[1]) + pad
        title_h = title.wrap(self.width / 2 - 50, 1000)[1] + pad
        desc_h = description.wrap((self.width / 2 - 50) * 7 / 8, 1000)[1] + pad
        loc_h = location.wrap(self.width / 2 - 50, 1000)[1] + pad
        return host_h, title_h, desc_h, loc_h

    def _measure_single(self, ed: EventDescription) -> float:
        host = Paragraph(ed.host_name, styles.HOST_STYLE)
        event_time = Paragraph(ed.time + " Uhr", styles.TIME_STYLE)
        title = Paragraph(ed.title, styles.TITLE_STYLE)
        description = Paragraph(ed.description, styles.DESCRIPTION_STYLE)
        location = Paragraph(ed.location, styles.TIME_STYLE)
        host_h, title_h, desc_h, loc_h = self._heights_single(host, event_time, title, description, location)
        return host_h + title_h + desc_h + loc_h + 4 * self.frame_top_margin + 20

    def _measure_multi(self, ed: EventDescription) -> float:
        host = Paragraph(ed.host_name, styles.HOST_STYLE_HALF)
        event_time = Paragraph(ed.time + " Uhr", styles.TIME_STYLE)
        title = Paragraph(ed.title, styles.TITLE_STYLE_HALF)
        description = Paragraph(ed.description, styles.DESCRIPTION_STYLE_HALF)
        location = Paragraph(ed.location, styles.TIME_STYLE_HALF)
        host_h, title_h, desc_h, loc_h = self._heights_multi(host, event_time, title, description, location)
        return host_h + title_h + desc_h + loc_h + 4 * self.frame_top_margin

    # ------------------------------------------------------------------ #
    #  Drawing a single event - single column
    # ------------------------------------------------------------------ #
    def _draw_event_single(self, ed: EventDescription, start_height) -> float:
        self.color = styles.BLACK if ed.id % 2 == 0 else styles.RED
        self.c.setStrokeColor(self.color)

        styles.HOST_STYLE.textColor = self.color
        styles.TIME_STYLE.textColor = self.color
        styles.TITLE_STYLE.textColor = self.color
        styles.DESCRIPTION_STYLE.textColor = self.color

        host = Paragraph(ed.host_name, styles.HOST_STYLE)
        event_time = Paragraph(ed.time + " Uhr", styles.TIME_STYLE)
        title = Paragraph(ed.title, styles.TITLE_STYLE)
        description = Paragraph(ed.description, styles.DESCRIPTION_STYLE)
        location = Paragraph(ed.location, styles.TIME_STYLE)

        host_height, title_height, description_height, location_height = \
            self._heights_single(host, event_time, title, description, location)

        ftm = self.frame_top_margin

        self.c.setLineWidth(5)
        self.c.line(50, start_height, self.width - 50, start_height)

        start_height -= host_height + ftm
        frame_host = Frame(50, start_height, (self.width - 100) * 3 / 4, host_height, showBoundary=self.is_debug)
        frame_time = Frame(self.width - 50 - ((self.width - 100) * 1 / 4), start_height,
                           (self.width - 100) * 1 / 4, host_height, showBoundary=self.is_debug)

        start_height -= title_height + ftm
        frame_title = Frame(50, start_height, self.width - 100, title_height, showBoundary=self.is_debug, topPadding=0)

        start_height -= description_height
        frame_description = Frame(50, start_height, self.width - 100, description_height, showBoundary=self.is_debug)

        start_height -= location_height + ftm + 20
        frame_location = Frame(50, start_height, self.width - 100, location_height,
                               leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
                               showBoundary=self.is_debug)

        start_height -= ftm
        self.last_line = start_height

        self.c.setLineWidth(1)
        frame_host.addFromList([host], self.c)
        frame_time.addFromList([event_time], self.c)
        frame_title.addFromList([title], self.c)
        frame_description.addFromList([description], self.c)
        frame_location.addFromList([location], self.c)

        return start_height

    # ------------------------------------------------------------------ #
    #  Drawing a single event - column (multi-column)
    # ------------------------------------------------------------------ #
    def _draw_event_multi(self, ed: EventDescription, left_anchor, start_height) -> float:
        self.color = styles.BLACK if ed.id % 2 == 0 else styles.RED
        self.c.setStrokeColor(self.color)

        styles.HOST_STYLE_HALF.textColor = self.color
        styles.TIME_STYLE.textColor = self.color
        styles.TIME_STYLE_HALF.textColor = self.color
        styles.TITLE_STYLE_HALF.textColor = self.color
        styles.DESCRIPTION_STYLE_HALF.textColor = self.color

        host = Paragraph(ed.host_name, styles.HOST_STYLE_HALF)
        event_time = Paragraph(ed.time + " Uhr", styles.TIME_STYLE)
        title = Paragraph(ed.title, styles.TITLE_STYLE_HALF)
        description = Paragraph(ed.description, styles.DESCRIPTION_STYLE_HALF)
        location = Paragraph(ed.location, styles.TIME_STYLE_HALF)

        host_height, title_height, description_height, location_height = \
            self._heights_multi(host, event_time, title, description, location)

        ftm = self.frame_top_margin

        self.c.setLineWidth(5)
        self.c.line(left_anchor, start_height, (self.width - 50) / 2 + left_anchor - 25, start_height)

        start_height -= host_height + ftm
        frame_host = Frame(left_anchor, start_height, ((self.width - 100) * 3 / 4) / 2, host_height,
                           showBoundary=self.is_debug)
        frame_time = Frame((self.width / 2 - 50 - ((self.width - 100) * 1 / 4)) + left_anchor, start_height,
                           (self.width - 100) * 1 / 4, host_height, showBoundary=self.is_debug)

        start_height -= title_height + ftm
        frame_title = Frame(left_anchor, start_height, self.width / 2 - 50, title_height,
                            showBoundary=self.is_debug, topPadding=0)

        start_height -= description_height - 20
        frame_description = Frame(left_anchor, start_height, self.width / 2 - 50, description_height,
                                  showBoundary=self.is_debug)

        start_height -= location_height + ftm + 20
        frame_location = Frame(left_anchor, start_height, self.width / 2 - 50, location_height,
                               leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
                               showBoundary=self.is_debug)

        start_height -= ftm
        self.last_line = start_height

        self.c.setLineWidth(1)
        frame_host.addFromList([host], self.c)
        frame_time.addFromList([event_time], self.c)
        frame_title.addFromList([title], self.c)
        frame_description.addFromList([description], self.c)
        frame_location.addFromList([location], self.c)

        return start_height
