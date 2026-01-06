import pytesseract
from PIL import Image

img = Image.open("sample.png")  # use any scanned page image
text = pytesseract.image_to_string(img, lang='eng')

print(text)
