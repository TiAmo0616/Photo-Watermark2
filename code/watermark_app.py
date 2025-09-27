import os
from tkinter import Tk, Label, Button, Listbox, Entry, Scale, HORIZONTAL, filedialog, Canvas, StringVar
from PIL import Image, ImageDraw, ImageFont, ImageTk

class WatermarkApp:
    def __init__(self, root):
        self.root = root
        self.root.title("水印文件本地应用")

        # 图片导入部分
        self.import_label = Label(root, text="图片导入")
        self.import_label.pack()

        self.import_button = Button(root, text="导入图片", command=self.import_images)
        self.import_button.pack()

        self.folder_button = Button(root, text="导入文件夹", command=self.import_folder)
        self.folder_button.pack()

        self.image_listbox = Listbox(root, width=50, height=10)
        self.image_listbox.pack()
        self.image_listbox.bind("<<ListboxSelect>>", self.display_selected_image)

        # 水印设置部分
        self.watermark_label = Label(root, text="水印设置")
        self.watermark_label.pack()

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

        # 图片导出部分
        self.export_label = Label(root, text="图片导出")
        self.export_label.pack()

        self.export_folder_label = Label(root, text="导出文件夹：")
        self.export_folder_label.pack()

        self.export_folder_entry = Entry(root, width=50)
        self.export_folder_entry.pack()

        self.browse_button = Button(root, text="选择文件夹", command=self.select_export_folder)
        self.browse_button.pack()

        self.prefix_label = Label(root, text="文件名前缀：")
        self.prefix_label.pack()

        self.prefix_var = StringVar()
        self.prefix_entry = Entry(root, textvariable=self.prefix_var, width=50)
        self.prefix_entry.pack()

        self.suffix_label = Label(root, text="文件名后缀：")
        self.suffix_label.pack()

        self.suffix_var = StringVar()
        self.suffix_entry = Entry(root, textvariable=self.suffix_var, width=50)
        self.suffix_entry.pack()

        self.export_button = Button(root, text="导出图片", command=self.export_images)
        self.export_button.pack()

        # 图片预览部分
        self.canvas = Canvas(root, width=400, height=400, bg="gray")
        self.canvas.pack()

        # 数据存储
        self.image_paths = []
        self.current_image = None
        self.watermarked_image = None

    def import_images(self):
        filetypes = [("图片文件", "*.jpg;*.jpeg;*.png;*.bmp;*.tiff")]
        files = filedialog.askopenfilenames(title="选择图片", filetypes=filetypes)
        for file in files:
            if file not in self.image_paths:
                self.image_paths.append(file)
                self.image_listbox.insert("end", os.path.basename(file))

    def import_folder(self):
        folder = filedialog.askdirectory(title="选择文件夹")
        if folder:
            for root, _, files in os.walk(folder):
                for file in files:
                    if file.lower().endswith((".jpg", ".jpeg", ".png", ".bmp", ".tiff")):
                        full_path = os.path.join(root, file)
                        if full_path not in self.image_paths:
                            self.image_paths.append(full_path)
                            self.image_listbox.insert("end", os.path.basename(full_path))

    def display_selected_image(self, event):
        selected_index = self.image_listbox.curselection()
        if selected_index:
            selected_image_path = self.image_paths[selected_index[0]]
            self.current_image = Image.open(selected_image_path)
            self.display_image(self.current_image)

    def display_image(self, image):
        image.thumbnail((400, 400))
        photo = ImageTk.PhotoImage(image)
        self.canvas.image = photo
        self.canvas.create_image(200, 200, image=photo)

    def preview_watermark(self):
        if not self.current_image:
            print("请先选择图片！")
            return

        text = self.text_entry.get()
        opacity = self.opacity_scale.get() / 100

        # 创建水印
        self.watermarked_image = self.current_image.copy()
        draw = ImageDraw.Draw(self.watermarked_image)
        font = ImageFont.load_default()
        text_width, text_height = draw.textsize(text, font=font)
        position = ((self.watermarked_image.width - text_width) // 2, (self.watermarked_image.height - text_height) // 2)

        text_layer = Image.new("RGBA", self.watermarked_image.size, (255, 255, 255, 0))
        text_draw = ImageDraw.Draw(text_layer)
        text_draw.text(position, text, font=font, fill=(255, 255, 255, int(255 * opacity)))
        self.watermarked_image = Image.alpha_composite(self.watermarked_image.convert("RGBA"), text_layer)

        self.display_image(self.watermarked_image)

    def select_export_folder(self):
        folder = filedialog.askdirectory(title="选择导出文件夹")
        if folder:
            self.export_folder_entry.delete(0, "end")
            self.export_folder_entry.insert(0, folder)

    def export_images(self):
        if not self.watermarked_image:
            print("请先预览水印！")
            return

        export_folder = self.export_folder_entry.get()
        prefix = self.prefix_var.get()
        suffix = self.suffix_var.get()

        if not export_folder:
            print("请先选择导出文件夹！")
            return

        for image_path in self.image_paths:
            image = Image.open(image_path)
            base_name = os.path.basename(image_path)
            name, ext = os.path.splitext(base_name)
            new_name = f"{prefix}{name}{suffix}{ext}"
            export_path = os.path.join(export_folder, new_name)
            image.save(export_path)

        print("图片导出完成！")

if __name__ == "__main__":
    root = Tk()
    app = WatermarkApp(root)
    root.mainloop()