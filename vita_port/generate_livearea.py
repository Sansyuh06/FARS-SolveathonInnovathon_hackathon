import os
from PIL import Image, ImageDraw, ImageFont

out_dir = r"d:\fyeshi\project\rohit\vita_port\sce_sys"
livearea_dir = os.path.join(out_dir, "livearea", "contents")
os.makedirs(livearea_dir, exist_ok=True)

# 1. Generate icon0.png (128x128)
img_icon = Image.new("RGBA", (128, 128), (12, 16, 24, 255))
draw = ImageDraw.Draw(img_icon)

# Outer rounded border
draw.rectangle([2, 2, 125, 125], outline=(0, 229, 255, 255), width=2)
# Inner accent grid
draw.rectangle([8, 8, 119, 119], outline=(35, 45, 60, 255), width=1)
# Robot AMR glyph
draw.rectangle([34, 44, 94, 84], fill=(24, 32, 46, 255), outline=(0, 229, 255, 255), width=2)
# Lidar turret
draw.ellipse([54, 34, 74, 54], fill=(0, 229, 255, 255), outline=(255, 255, 255, 255), width=1)
# Wheels
draw.rectangle([28, 52, 34, 76], fill=(0, 255, 136, 255))
draw.rectangle([94, 52, 100, 76], fill=(0, 255, 136, 255))
# FARS Label
draw.text((64, 104), "FARS", fill=(255, 255, 255, 255), anchor="mm")

img_icon.save(os.path.join(out_dir, "icon0.png"))
print("Saved icon0.png (128x128)")

# 2. Generate bg.png (840x500)
img_bg = Image.new("RGBA", (840, 500), (10, 14, 20, 255))
draw_bg = ImageDraw.Draw(img_bg)

# Draw subtle grid lines
for x in range(0, 840, 40):
    draw_bg.line([(x, 0), (x, 500)], fill=(20, 28, 40, 255), width=1)
for y in range(0, 500, 40):
    draw_bg.line([(0, y), (840, y)], fill=(20, 28, 40, 255), width=1)

# Decorative CAD corner accents
draw_bg.line([(20, 20), (120, 20)], fill=(0, 229, 255, 255), width=3)
draw_bg.line([(20, 20), (20, 120)], fill=(0, 229, 255, 255), width=3)
draw_bg.line([(820, 480), (720, 480)], fill=(0, 229, 255, 255), width=3)
draw_bg.line([(820, 480), (820, 380)], fill=(0, 229, 255, 255), width=3)

# Watermark / Title
draw_bg.text((420, 220), "FARSVERSE POCKET", fill=(255, 255, 255, 220), anchor="mm")
draw_bg.text((420, 270), "AUTONOMOUS ROBOTICS DIGITAL TWIN", fill=(0, 229, 255, 200), anchor="mm")
draw_bg.text((420, 310), "PLAYSTATION VITA EDITION", fill=(148, 163, 184, 180), anchor="mm")

img_bg.save(os.path.join(livearea_dir, "bg.png"))
print("Saved bg.png (840x500)")

# 3. Generate startup.png (280x158)
img_start = Image.new("RGBA", (280, 158), (14, 18, 26, 255))
draw_start = ImageDraw.Draw(img_start)
draw_start.rectangle([4, 4, 275, 153], outline=(0, 229, 255, 255), width=2)
draw_start.rectangle([10, 10, 269, 147], fill=(22, 28, 40, 255))
draw_start.text((140, 65), "START", fill=(255, 255, 255, 255), anchor="mm")
draw_start.text((140, 100), "FARS POCKET", fill=(0, 229, 255, 255), anchor="mm")

img_start.save(os.path.join(livearea_dir, "startup.png"))
print("Saved startup.png (280x158)")

# 4. Generate template.xml
template_xml = """<?xml version="1.0" encoding="utf-8"?>
<livearea style="a1">
  <livearea-background>
    <image>bg.png</image>
  </livearea-background>
  <gate>
    <startup-image>startup.png</startup-image>
  </gate>
</livearea>
"""
with open(os.path.join(livearea_dir, "template.xml"), "w", encoding="utf-8") as f:
    f.write(template_xml)
print("Saved template.xml")
