# Platypus Styles
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_RIGHT
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

styles = getSampleStyleSheet()

RED = colors.Color(201/255, 33/255, 30/255)
BLACK = colors.Color(0, 0, 0)

DATE_STYLE = ParagraphStyle(name='Normal',
                            fontName="RobotoBold",
                            fontSize=60,
                            alignment=TA_RIGHT,
                            leading= 52,
                            textColor= RED)

HEADING_STYLE = styles['Heading1'].clone("")
HEADING_STYLE.textColor = RED
HEADING_STYLE.fontSize = 44
HEADING_STYLE.leading = 40

HOST_STYLE = styles['Heading2'].clone("")
HOST_STYLE.fontSize = 20
HOST_STYLE.leading = 24

TITLE_STYLE = ParagraphStyle(name='title',
                            fontName="RobotoBold",
                            fontSize=44,
                            alignment=TA_LEFT,
                            leading= 44,)

DESCRIPTION_STYLE = styles['Heading2'].clone("")
DESCRIPTION_STYLE.fontSize = 18
DESCRIPTION_STYLE.leading = 18

TIME_STYLE = ParagraphStyle(name='time',
                            fontName="RobotoBold",
                            fontSize=26,
                            alignment=TA_RIGHT,
                            leading= 26,)



DATE_STYLE_HALF = ParagraphStyle(name='Normal',
                            fontName="RobotoBold",
                            fontSize=54,
                            alignment=TA_RIGHT,
                            leading= 52,
                            textColor= RED)

HEADING_STYLE_HALF = styles['Heading1'].clone("")
HEADING_STYLE_HALF.textColor = colors.red
HEADING_STYLE_HALF.fontSize = 40
HEADING_STYLE_HALF.leading = 40

HOST_STYLE_HALF = styles['Heading2'].clone("")
HOST_STYLE_HALF.fontSize = 20
HOST_STYLE_HALF.leading = 24

TITLE_STYLE_HALF = ParagraphStyle(name='title',
                            fontName="RobotoBold",
                            fontSize=32,
                            alignment=TA_LEFT,
                            leading= 44,)

DESCRIPTION_STYLE_HALF = styles['Heading2'].clone("")
DESCRIPTION_STYLE_HALF.fontSize = 18
DESCRIPTION_STYLE_HALF.leading = 18

TIME_STYLE_HALF = ParagraphStyle(name='time',
                            fontName="RobotoBold",
                            fontSize=20,
                            alignment=TA_RIGHT,
                            leading= 26,)