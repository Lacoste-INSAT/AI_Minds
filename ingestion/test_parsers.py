import sys; sys.path.insert(0, ".")

# PDF
# from parsers.pdf_parser import PdfParser
# print(PdfParser.parse("C:/Users/Asus/Downloads/Tech Stack AI Minds.pdf")[:200])

# TXT / MD
# from parsers.text_parser import TextParser
# print(TextParser.parse("C:\\Users\\Asus\\Desktop\\AI_Minds\\README.md")[:200])

# DOCX
# from parsers.docx_parser import DocxParser
# print(DocxParser.parse("c:/Users/Asus/Documents/CV/Makki/Makki Aloulou.docx")[:200])

# Image (needs Tesseract installed)
from parsers.image_parser import ImageParser
print(ImageParser.parse("C:\\Users\\Asus\\Downloads\\Ingestion Brain-2026-02-14-192023.png")[:200])

# Audio (first call loads model ~1 min)
# from parsers.audio_parser import AudioParser
# print(AudioParser.parse("C:/Users/Asus/Downloads/harvard.wav")[:200])

# # Via router (end-to-end)
# from router import route
# parser = route("../README.md")
# print(parser.parse("../README.md")[:200])