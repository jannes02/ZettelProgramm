from typing import List
from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A3, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, Frame

from src.backend.event_description import EventDescription

# Platypus Styles
styles = getSampleStyleSheet()

date_style = ParagraphStyle(name='Normal',
                            fontName="RobotoBold",
                            fontSize=60,
                            alignment=TA_RIGHT,
                            leading= 52,
                            textColor= colors.red)

heading_style = styles['Heading1'].clone("")
heading_style.textColor = colors.red
heading_style.fontSize = 44
heading_style.leading = 40

host_style = styles['Heading2'].clone("")
host_style.fontSize = 20
host_style.leading = 24
title_style = styles['Heading2'].clone("")
title_style.fontSize = 44
title_style.leading = 44
title_style.spaceBefore = 0
title_style.spaceAfter = 0
description_style = styles['Heading2'].clone("")
description_style.fontSize = 14
description_style.leading = 18
time_style = styles['Heading2'].clone("")
time_style.alignment = TA_RIGHT
time_style.fontSize = 20
time_style.leading = 24

class FlyerBuilder:

    def __init__(self, output_file_name):
        self.filename = output_file_name
        self.width, self.height = A3  # A3 Hochformat (842x1191 Punkte)
        self.paragraph_padding = 16
        self.frame_top_margin = 8 #export
        self.c = canvas.Canvas(self.filename, pagesize=A3)
        self.last_line = 0.0
        self.color = colors.black
        self.is_debug = False

    def build(self,title="Heute im Haus", date="", event_descriptions:List[EventDescription]=None, first_run=True) -> int:
        if event_descriptions is None:
            print("Keine Events gefunden!")
            return -1

        start_height = self._build_header(title, date)

        for ed in event_descriptions:
            start_height = self._build_event(ed, start_height)

        if first_run:

            if start_height > A4[0] + 10:
                print("Recompile in A4 Format")
                self.frame_top_margin = self.last_line/40 if self.last_line  > 760 else 8
                self.height, self.width = A4[0], A4[1]
                self.c = canvas.Canvas(self.filename, pagesize=(self.width, self.height))
                self.build(title=title, date=date, event_descriptions=event_descriptions, first_run=False)
                return 0
            else:
                self.frame_top_margin = self.last_line/20 if self.last_line  > (A3[0]/3) else 8
                self.c = canvas.Canvas(self.filename, pagesize=(self.width, self.height))
                self.build(title=title, date=date, event_descriptions=event_descriptions, first_run=False)
                return 0


        self.c.showPage()
        self.c.save()
        return 0


    def _build_header(self, title, date) -> float:

        heading = Paragraph(title, heading_style)
        date = Paragraph(date, date_style)

        frame_heading = Frame(50, self.height - 150, self.width / 2 - 50, 100, showBoundary=self.is_debug)
        frame_date = Frame(self.width / 2, self.height - 150, self.width / 2 - 50, 100, showBoundary=self.is_debug)


        self.c.setStrokeColor(colors.black)
        self.c.setLineWidth(1)
        frame_heading.addFromList([heading], self.c)
        frame_date.addFromList([date], self.c)


        return self.height - 160

    def _build_event(self, ed:EventDescription, start_height) -> float:

        self.color = colors.black if ed.id % 2 == 0 else colors.red
        self.c.setStrokeColor(self.color)

        print(f"{ed.title} ist: {self.color}")
        host_style.textColor = self.color
        time_style.textColor = self.color
        title_style.textColor = self.color
        description_style.textColor = self.color

        host = Paragraph(ed.host_name, host_style)
        event_time = Paragraph(ed.time, time_style)
        title = Paragraph(ed.title, title_style)
        description = Paragraph(ed.description, description_style)
        location = Paragraph(ed.location, time_style)

        # calculate height for each section
        host_height = max(host.wrap((self.width - 100) * 3 / 4, 1000)[1], event_time.wrap((self.width - 100) * 1 / 4, 1000)[1])
        host_height += self.paragraph_padding
        title_height = title.wrap(self.width - 100, 1000)[1]
        title_height += self.paragraph_padding
        description_height = description.wrap((self.width - 100) * 3 / 4, 1000)[1]
        description_height += self.paragraph_padding
        location_height = location.wrap((self.width - 100) * 1 / 4, 1000)[1]
        location_height += self.paragraph_padding

        self.c.setLineWidth(3)
        self.c.line(50, start_height, self.width - 50, start_height)

        start_height -= host_height + self.frame_top_margin
        frame_host = Frame(50, start_height, (self.width - 100) * 3 / 4, host_height, showBoundary=self.is_debug)
        frame_time = Frame(self.width - 50 - ((self.width - 100) * 1 / 4), start_height, (self.width - 100) * 1 / 4, host_height,
                           showBoundary=self.is_debug)

        start_height -= title_height + self.frame_top_margin
        frame_title = Frame(50, start_height, self.width - 100, title_height, showBoundary=self.is_debug, topPadding=0)

        start_height -= description_height + self.frame_top_margin + 10
        frame_description = Frame(50, start_height, (self.width - 100) * 3 / 4, description_height, showBoundary=self.is_debug)
        frame_location = Frame(self.width - 50 - ((self.width - 100) * 1 / 4), start_height, (self.width - 100) * 1 / 4,
                               location_height, showBoundary=self.is_debug)

        start_height -= self.frame_top_margin


        self.last_line = start_height


        self.c.setLineWidth(1)
        frame_host.addFromList([host], self.c)
        frame_time.addFromList([event_time], self.c)
        frame_title.addFromList([title], self.c)
        frame_description.addFromList([description], self.c)
        frame_location.addFromList([location], self.c)



        return start_height