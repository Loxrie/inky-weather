import cairosvg
from pathlib import Path

def convert2Png(fileName):
    print(fileName)
    cairosvg.svg2png(url=fileName, write_to=f"{fileName[:-4]}.png", output_width=128)
    cairosvg.svg2png(url=fileName, write_to=f"64x/{fileName[:-4]}.png", output_width=64)
    cairosvg.svg2png(url=fileName, write_to=f"32x/{fileName[:-4]}.png", output_width=32)

rootdir = Path('.')
file_list = [f for f in rootdir.glob('**/*.svg') if f.is_file()]

for f in file_list:
    convert2Png(f.__str__())
