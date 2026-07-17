from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
out_dir = ROOT / "paper" / "report_verification"
out_dir.mkdir(exist_ok=True)

previews = []
page_paths = sorted(out_dir.glob("page-*.png"))
print(f"pages={len(page_paths)}")
for index, image_path in enumerate(page_paths):
    image = Image.open(image_path).convert("RGB")
    image.thumbnail((260, 368))
    canvas = Image.new("RGB", (280, 400), "white")
    canvas.paste(image, ((280 - image.width) // 2, 10))
    ImageDraw.Draw(canvas).text((10, 380), f"Page {index + 1}", fill="black")
    previews.append(canvas)

columns = 4
rows = (len(previews) + columns - 1) // columns
sheet = Image.new("RGB", (columns * 280, rows * 400), (220, 224, 228))
for index, image in enumerate(previews):
    sheet.paste(image, ((index % columns) * 280, (index // columns) * 400))
sheet.save(out_dir / "contact-sheet.png")
print("contact sheet generated")
