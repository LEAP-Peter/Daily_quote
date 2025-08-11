from PIL import Image, ImageDraw, ImageFont
from textwrap import wrap
import os
import platform
from datetime import datetime

class QuoteGenerator:
    def __init__(self, background_image="quote_template_background.jpg", output_folder="outputs"):
        self.background_image = background_image
        self.output_folder = output_folder

        os.makedirs(self.output_folder, exist_ok=True)

        # 预检测字体可用性并提示
        self.arial_regular_path, self.arial_bold_italic_path = self._detect_arial_paths()
        self.notosans_path = os.path.join("fonts", "NotoSans-VariableFont.ttf")

        print("Initialized")
        print(f"background path：{self.background_image}")
        print(f"output folder：{self.output_folder}")

        # 提示：NotoSans（正文）
        if os.path.exists(self.notosans_path):
            print(f"[Font] NotoSans found: {self.notosans_path}")
        else:
            print("[Font] NotoSans NOT found -> will fallback to default font for quote text")

        # 提示：Arial（日期/作者）
        print("[Font] Arial Regular:",
              self.arial_regular_path if self.arial_regular_path else "NOT found -> fallback to default")
        print("[Font] Arial Bold Italic:",
              self.arial_bold_italic_path if self.arial_bold_italic_path else "NOT found -> fallback to default")

    def _detect_arial_paths(self):
        """跨平台查找 Arial Regular 与 Arial Bold Italic 的字体文件路径"""
        sys_platform = platform.system()
        candidates_regular = []
        candidates_bi = []

        if sys_platform == "Windows":
            # 常见 Windows 路径
            candidates_regular = [
                r"C:\Windows\Fonts\arial.ttf",
                r"C:\Windows\Fonts\Arial.ttf",
            ]
            candidates_bi = [
                r"C:\Windows\Fonts\arialbi.ttf",
                r"C:\Windows\Fonts\Arialbi.ttf",
                r"C:\Windows\Fonts\Arial Bold Italic.ttf",
            ]
        elif sys_platform == "Darwin":  # macOS
            # macOS 常见路径
            candidates_regular = [
                "/System/Library/Fonts/Supplemental/Arial.ttf",
                "/Library/Fonts/Arial.ttf",
            ]
            candidates_bi = [
                "/System/Library/Fonts/Supplemental/Arial Bold Italic.ttf",
                "/Library/Fonts/Arial Bold Italic.ttf",
            ]
        else:  # Linux 及其他
            # 有些发行版会提供 Arial 替代；尝试常见目录
            candidates_regular = [
                "/usr/share/fonts/truetype/msttcorefonts/Arial.ttf",
                "/usr/share/fonts/truetype/msttcorefonts/arial.ttf",
                "/usr/share/fonts/truetype/msttcorefonts/Arial-Regular.ttf",
                "/usr/share/fonts/truetype/msttcorefonts/Arial.ttf",
            ]
            candidates_bi = [
                "/usr/share/fonts/truetype/msttcorefonts/Arial_Bold_Italic.ttf",
                "/usr/share/fonts/truetype/msttcorefonts/arialbi.ttf",
                "/usr/share/fonts/truetype/msttcorefonts/Arial-Bold-Italic.ttf",
            ]

        def first_exists(paths):
            for p in paths:
                if os.path.exists(p):
                    return p
            return None

        return first_exists(candidates_regular), first_exists(candidates_bi)

    def _load_fonts(self):
        """加载所需字体并在失败时回退默认字体；只在 generate() 调用时真正加载。"""
        # 正文：NotoSans 45
        if os.path.exists(self.notosans_path):
            try:
                quote_font = ImageFont.truetype(self.notosans_path, 45)
            except Exception:
                print("[Font] Failed to load NotoSans -> fallback to default")
                quote_font = ImageFont.load_default()
        else:
            quote_font = ImageFont.load_default()

        # 作者：Arial Bold Italic 32
        if self.arial_bold_italic_path:
            try:
                author_font = ImageFont.truetype(self.arial_bold_italic_path, 32)
            except Exception:
                print("[Font] Failed to load Arial Bold Italic -> fallback to default")
                author_font = ImageFont.load_default()
        else:
            author_font = ImageFont.load_default()

        # 日期：Arial Regular 30
        if self.arial_regular_path:
            try:
                date_font = ImageFont.truetype(self.arial_regular_path, 30)
            except Exception:
                print("[Font] Failed to load Arial Regular -> fallback to default")
                date_font = ImageFont.load_default()
        else:
            date_font = ImageFont.load_default()

        return quote_font, author_font, date_font

    def generate(self, date, author, quote, output_format="jpeg"):
        if not os.path.exists(self.background_image):
            print("cannot find background image")
            return

        # 打开背景图
        image = Image.open(self.background_image).convert("RGB")
        draw = ImageDraw.Draw(image)
        W, H = image.size

        # 加载字体（带回退）
        quote_font, author_font, date_font = self._load_fonts()

        safe_date = date.replace(".", "-")
        date_text = f"{date}"
        author_text = f"---{author}"

        # 日期
        bbox = draw.textbbox((0, 0), date_text, font=date_font)
        w = bbox[2] - bbox[0]
        date_y = 350
        draw.text(((W - w) / 2, date_y), date_text, font=date_font, fill="black")

        # 换行处理（正文）
        max_line_length = 30
        wrapped_lines = wrap(quote, width=max_line_length)
        quote_wrapped = "\n".join(wrapped_lines)

        # 正文绘制
        bbox = draw.textbbox((0, 0), quote_wrapped, font=quote_font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        quote_x = (W - w) / 2
        quote_y = date_y + 100
        draw.multiline_text(
            (quote_x, quote_y),
            quote_wrapped,
            font=quote_font,
            fill="black",
            spacing=10,
            align="center"
        )

        # 作者名
        bbox = draw.textbbox((0, 0), author_text, font=author_font)
        w = bbox[2] - bbox[0]
        draw.text(((W - w) / 2, quote_y + 200), author_text, font=author_font, fill="black")

        # 保存
        output_path = os.path.join(self.output_folder, f"quote_{safe_date}.{output_format}")
        print(f"saving image to：{output_path}")
        image.save(output_path)
        print("image saved successfully")
