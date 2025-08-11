from PIL import Image, ImageDraw, ImageFont
from textwrap import wrap
import os
from datetime import datetime


class QuoteGenerator:
    def __init__(self, background_image="quote_template_background.jpg", output_folder="outputs"):
        self.background_image = background_image
        self.output_folder = output_folder

        os.makedirs(self.output_folder, exist_ok=True)
        print(f"Initialized")
        print(f"background path：{self.background_image}")
        print(f"output folder：{self.output_folder}")

    def generate(self, date, author, quote, output_format="jpeg"):
        if not os.path.exists(self.background_image):
            print("cannot find background image")
            return

        # open background image
        image = Image.open(self.background_image).convert("RGB")
        draw = ImageDraw.Draw(image)
        W, H = image.size

        # load fonts
        font_path = os.path.join("fonts", "NotoSans-VariableFont.ttf")
        try:
            quote_font = ImageFont.truetype(font_path, 45)
            author_font = ImageFont.truetype(font_path, 45)
            date_font = ImageFont.truetype(font_path, 35)
        except:
            print("cannot load custom fonts, using default font")
            quote_font = ImageFont.load_default()
            author_font = ImageFont.load_default()
            date_font = ImageFont.load_default()

        safe_date = date.replace(".", "-")
        date_text = f"{date}"
        author_text = f"---{author}"

        # date
        bbox = draw.textbbox((0, 0), date_text, font=date_font)
        w = bbox[2] - bbox[0]
        date_y = 350
        draw.text(((W - w) / 2, date_y), date_text, font=date_font, fill="black")

        # change line
        max_line_length = 30
        wrapped_lines = wrap(quote, width=max_line_length)
        quote_wrapped = "\n".join(wrapped_lines)

        # quote
        bbox = draw.textbbox((0, 0), quote_wrapped, font=quote_font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        quote_x = (W - w) / 2
        quote_y = date_y + 100
        draw.multiline_text((quote_x, quote_y), quote_wrapped, font=quote_font, fill="black", spacing=10, align="center")

        # author
        bbox = draw.textbbox((0, 0), author_text, font=author_font)
        w = bbox[2] - bbox[0]
        draw.text(((W - w) / 2, quote_y + 200), author_text, font=author_font, fill="black")

        # save
        safe_date = date.replace(".", "-")
        output_path = os.path.join(self.output_folder, f"quote_{safe_date}.{output_format}")
        print(f"saving image to：{output_path}")
        image.save(output_path)
        print("image saved successfully")
