from itertools import count
from typing import List
from reportlab.lib import colors
from reportlab.lib.pagesizes import A3, A4
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, Frame

from src.backend.event_description import EventDescription
import src.backend.styles as styles


class FlyerBuilder:

    def __init__(self, output_file_name):
        self.filename = output_file_name
        self.width, self.height = A3  # A3 Hochformat (842x1191 Punkte)
        self.paragraph_padding = 16
        self.frame_top_margin = 8 #export
        self.c = canvas.Canvas(self.filename, pagesize=A3)
        self.last_line = 0.0
        self.color = styles.BLACK
        self.is_debug = False
        self.count = 0
        self.left_anchor = 0
        self.y_offset = 0

    def build(self,title="Heute im Haus", date="", event_descriptions:List[EventDescription]=None, first_run=True) -> int:
        if event_descriptions is None:
            print("Keine Events gefunden!")
            return -1

        self.count = len(event_descriptions)
        format_mode = 1
        if self.count == 1: format_mode = 1
        elif 4 >= self.count >= 2: format_mode = 2
        elif self.count > 4: format_mode = 3

        if format_mode == 1:
            print("Recompile in A4 Format")
            self.frame_top_margin = 8
            self.height, self.width = A4[0], A4[1]
            self.c = canvas.Canvas(self.filename, pagesize=(self.width, self.height))
        elif format_mode == 2:
            print("Recompile in A3 Format - portrait")
            self.frame_top_margin = 8
            self.height, self.width = A3[1], A3[0]
            self.c = canvas.Canvas(self.filename, pagesize=(self.width, self.height))
        else:
            print("Recompile in A3 Format - landscape")
            self.frame_top_margin = 8
            self.height, self.width = A3
            self.c = canvas.Canvas(self.filename, pagesize=(self.width, self.height))


        self.frame_top_margin = 16 / (self.count or 1)

        self.header_height = self._build_header(title, date)

        start_height = self.header_height
        for ed in event_descriptions:
            start_height = self._build_event(ed, start_height) if self.count < 5 else self._build_event_multicolumn(ed, start_height)

        self.c.showPage()
        self.c.save()
        return 0


    def _build_header(self, title, date) -> float:

        heading = Paragraph(title, styles.HEADING_STYLE)
        date = Paragraph(date, styles.DATE_STYLE)

        frame_heading = Frame(50, self.height - 150, self.width / 2 - 50, 100, showBoundary=self.is_debug)
        frame_date = Frame(self.width / 2, self.height - 150, self.width / 2 - 50, 100, showBoundary=self.is_debug)


        self.c.setStrokeColor(styles.BLACK)
        self.c.setLineWidth(1)
        frame_heading.addFromList([heading], self.c)
        frame_date.addFromList([date], self.c)


        return self.height - 160

    def _build_event(self, ed:EventDescription, start_height) -> float:

        self.color = styles.BLACK if ed.id % 2 == 0 else styles.RED
        self.c.setStrokeColor(self.color)

        print(f"{ed.title} ist: {self.color}")
        styles.HOST_STYLE.textColor = self.color
        styles.TIME_STYLE.textColor = self.color
        styles.TITLE_STYLE.textColor = self.color
        styles.DESCRIPTION_STYLE.textColor = self.color

        host = Paragraph(ed.host_name, styles.HOST_STYLE)
        event_time = Paragraph(ed.time, styles.TIME_STYLE)
        title = Paragraph(ed.title, styles.TITLE_STYLE)
        description = Paragraph(ed.description, styles.DESCRIPTION_STYLE)
        location = Paragraph(ed.location, styles.TIME_STYLE)

        # calculate height for each section
        host_height = max(host.wrap((self.width - 100) * 3 / 4, 1000)[1], event_time.wrap((self.width - 100) * 1 / 4, 1000)[1])
        host_height += self.paragraph_padding
        title_height = title.wrap(self.width - 100, 1000)[1]
        title_height += self.paragraph_padding
        description_height = description.wrap((self.width - 100) * 7/8, 1000)[1]
        description_height += self.paragraph_padding
        location_height = location.wrap(self.width - 100, 1000)[1]
        location_height += self.paragraph_padding

        self.c.setLineWidth(5)
        self.c.line(50, start_height, self.width - 50, start_height)

        start_height -= host_height + self.frame_top_margin
        frame_host = Frame(50, start_height, (self.width - 100) * 3 / 4, host_height, showBoundary=self.is_debug)
        frame_time = Frame(self.width - 50 - ((self.width - 100) * 1 / 4), start_height, (self.width - 100) * 1 / 4, host_height,
                           showBoundary=self.is_debug)

        start_height -= title_height + self.frame_top_margin
        frame_title = Frame(50, start_height, self.width - 100, title_height, showBoundary=self.is_debug, topPadding=0)

        start_height -= description_height
        frame_description = Frame(50, start_height, self.width - 100, description_height, showBoundary=self.is_debug)

        start_height -= location_height + self.frame_top_margin + 20
        frame_location = Frame(50, start_height, self.width - 100, location_height,
                               leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
                               showBoundary=self.is_debug)


        start_height -= self.frame_top_margin


        self.last_line = start_height


        self.c.setLineWidth(1)
        frame_host.addFromList([host], self.c)
        frame_time.addFromList([event_time], self.c)
        frame_title.addFromList([title], self.c)
        frame_description.addFromList([description], self.c)
        frame_location.addFromList([location], self.c)



        return start_height


    def _build_event_multicolumn(self, ed:EventDescription, start_height) -> float:

        self.frame_top_margin = 4

        self.color = styles.BLACK if ed.id % 2 == 0 else styles.RED
        self.c.setStrokeColor(self.color)

        self.left_anchor = 25 if ed.id <= 2 else 25 + A3[1]/2

        print(f"{ed.title} ist: {self.color}")
        styles.HOST_STYLE_HALF.textColor = self.color
        styles.TIME_STYLE_HALF.textColor = self.color
        styles.TITLE_STYLE_HALF.textColor = self.color
        styles.DESCRIPTION_STYLE_HALF.textColor = self.color

        host = Paragraph(ed.host_name, styles.HOST_STYLE_HALF)
        event_time = Paragraph(ed.time, styles.TIME_STYLE_HALF)
        title = Paragraph(ed.title, styles.TITLE_STYLE_HALF)
        description = Paragraph(ed.description, styles.DESCRIPTION_STYLE_HALF)
        location = Paragraph(ed.location, styles.TIME_STYLE_HALF)

        # calculate height for each section
        host_height = max(host.wrap((self.width - 100) * 3 / 4, 1000)[1], event_time.wrap((self.width - 100) * 1 / 4, 1000)[1])
        host_height += self.paragraph_padding
        title_height = title.wrap(self.width - 100, 1000)[1]
        title_height += self.paragraph_padding
        description_height = description.wrap((self.width - 100) * 7 / 8, 1000)[1]
        description_height += self.paragraph_padding
        location_height = location.wrap(self.width/2 - 50, 1000)[1]
        location_height += self.paragraph_padding

        self.c.setLineWidth(5)
        self.c.line(self.left_anchor, start_height, (self.width - 50)/2 + self.left_anchor - 25, start_height)

        start_height -= host_height + self.frame_top_margin
        frame_host = Frame(self.left_anchor, start_height, ((self.width - 100) * 3 / 4) / 2, host_height, showBoundary=self.is_debug)
        frame_time = Frame(((self.width/2 - 50 - ((self.width - 100) * 1 / 4)) + self.left_anchor), start_height, (self.width - 100) * 1 / 4, host_height,
                           showBoundary=self.is_debug)

        start_height -= title_height + self.frame_top_margin
        frame_title = Frame(self.left_anchor, start_height, self.width - 100, title_height, showBoundary=self.is_debug, topPadding=0)

        start_height -= description_height - 20
        frame_description = Frame(self.left_anchor, start_height, self.width - 100, description_height, showBoundary=self.is_debug)

        start_height -= location_height + self.frame_top_margin + 20
        frame_location = Frame(self.left_anchor, start_height, self.width/2 - 100, location_height,
                               leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
                               showBoundary=self.is_debug)


        start_height -= self.frame_top_margin


        self.last_line = start_height


        self.c.setLineWidth(1)
        frame_host.addFromList([host], self.c)
        frame_time.addFromList([event_time], self.c)
        frame_title.addFromList([title], self.c)
        frame_description.addFromList([description], self.c)
        frame_location.addFromList([location], self.c)

        if self.count > 4 and ed.id == 2:
            start_height = self.header_height

        return start_height