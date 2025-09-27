import os
from tkinter import Tk, Label, Entry, Button, Scale, HORIZONTAL, filedialog, Canvas
from PIL import Image, ImageDraw, ImageFont, ImageTk

class TextWatermarkApp:
    def __init__(self, root):
        self.root = root
        self.root.title("文本水印工具")

        # UI Elements
        self.label = Label(root, text="选择图片：")
        self.label.pack()

        self.select_button = Button(root, text="选择图片", command=self.select_image)
        self.select_button.pack()

        self.text_label = Label(root, text="水印文本：")
        self.text_label.pack()

        self.text_entry = Entry(root, width=30)
        self.text_entry.pack()

        self.opacity_label = Label(root, text="透明度：")
        self.opacity_label.pack()

        self.opacity_scale = Scale(root, from_=0, to=100, orient=HORIZONTAL)
        self.opacity_scale.set(50)
        self.opacity_scale.pack()

        self.preview_button = Button(root, text="预览水印", command=self.preview_watermark)
        self.preview_button.pack()

        self.save_button = Button(root, text="保存图片", command=self.save_image)
        self.save_button.pack()

        self.canvas = Canvas(root, width=400, height=400, bg="gray")
        self.canvas.pack()

        # Store image paths and objects
        self.image_path = None
        self.original_image = None
        self.watermarked_image = None

    def select_image(self):
        filetypes = [("图片文件", "*.jpg;*.jpeg;*.png;*.bmp;*.tiff")]
        self.image_path = filedialog.askopenfilename(title="选择图片", filetypes=filetypes)
        if self.image_path:
            self.original_image = Image.open(self.image_path)
            self.display_image(self.original_image)

    def display_image(self, image):
        image.thumbnail((400, 400))
        photo = ImageTk.PhotoImage(image)
        self.canvas.image = photo
        self.canvas.create_image(200, 200, image=photo)

    def preview_watermark(self):
        if not self.original_image:
            print("请先选择图片！")
            return

        text = self.text_entry.get()
        opacity = self.opacity_scale.get() / 100

        # Create a copy of the original image
        self.watermarked_image = self.original_image.copy()
        draw = ImageDraw.Draw(self.watermarked_image)

        # Define font and position
        font = ImageFont.load_default()
        text_width, text_height = draw.textsize(text, font=font)
        position = ((self.watermarked_image.width - text_width) // 2, (self.watermarked_image.height - text_height) // 2)

        # Add text with transparency
        text_layer = Image.new("RGBA", self.watermarked_image.size, (255, 255, 255, 0))
        text_draw = ImageDraw.Draw(text_layer)
        text_draw.text(position, text, font=font, fill=(255, 255, 255, int(255 * opacity)))
        self.watermarked_image = Image.alpha_composite(self.watermarked_image.convert("RGBA"), text_layer)

        self.display_image(self.watermarked_image)

    def save_image(self):
        if not self.watermarked_image:
            print("请先预览水印！")
            return

        save_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG 文件", "*.png"), ("JPEG 文件", "*.jpg")])
        if save_path:
            self.watermarked_image.convert("RGB").save(save_path)
            print("图片已保存！")

if __name__ == "__main__":
    root = Tk()
    app = TextWatermarkApp(root)
    root.mainloop()