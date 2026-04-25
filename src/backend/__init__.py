import os
import reportlab
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from rsc_path import rsc_path

pdfmetrics.registerFont(TTFont('Roboto', rsc_path("fonts\\roboto.ttf")))

# we know some glyphs are missing, suppress warnings
import reportlab.rl_config
reportlab.rl_config.warnOnMissingFontGlyphs = 0

reportlab.rl_config.canvas_basefontname = 'Roboto'
