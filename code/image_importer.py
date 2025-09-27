import os
from tkinter import Tk, filedialog, Listbox, Button, Label, PhotoImage
from PIL import Image, ImageTk

class ImageImporterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("图片导入工具")

        # UI Elements
        self.label = Label(root, text="已导入图片：")
        self.label.pack()

        self.listbox = Listbox(root, width=50, height=15)
        self.listbox.pack()

        self.import_button = Button(root, text="导入图片", command=self.import_images)
        self.import_button.pack()

        self.folder_button = Button(root, text="导入文件夹", command=self.import_folder)
        self.folder_button.pack()

        # self.image_preview = Label(root, text="预览区域", width=50, height=15)
        # self.image_preview.pack()
        self.image_preview = Label(root, text="预览区域", bd=1, relief="sunken")
        self.image_preview.pack()
        # 固定像素尺寸，足够放下 200×200 的缩略图
        self.image_preview.config(width=300, height=300)

        # Store imported images
        self.image_paths = []

        # ---------- fix bug ----------
        # 1. 先放一张合法尺寸的灰色占位图，保证第一次就不会是 0×0
        dummy = Image.new("RGBA", (300, 300), (240, 240, 240, 255))
        self.dummy_photo = ImageTk.PhotoImage(dummy)
        self.image_preview.config(image=self.dummy_photo)

        # 2. 强制窗口最小尺寸，防止以后被缩成 1×1
        root.update_idletasks()
        root.minsize(root.winfo_width(), root.winfo_height())

    def import_images(self):
        filetypes = [("图片文件", "*.jpg;*.jpeg;*.png;*.bmp;*.tiff")]
        files = filedialog.askopenfilenames(title="选择图片", filetypes=filetypes)
        for file in files:
            if file not in self.image_paths:
                self.image_paths.append(file)
                self.listbox.insert("end", os.path.basename(file))
        self.listbox.bind("<<ListboxSelect>>", self.show_preview)

    def import_folder(self):
        folder = filedialog.askdirectory(title="选择文件夹")
        if folder:
            for root, _, files in os.walk(folder):
                for file in files:
                    if file.lower().endswith((".jpg", ".jpeg", ".png", ".bmp", ".tiff")):
                        full_path = os.path.join(root, file)
                        if full_path not in self.image_paths:
                            self.image_paths.append(full_path)
                            self.listbox.insert("end", os.path.basename(full_path))
        self.listbox.bind("<<ListboxSelect>>", self.show_preview)

    def show_preview(self, event):
        selected_index = self.listbox.curselection()
        if selected_index:
            selected_image_path = self.image_paths[selected_index[0]]
            image = Image.open(selected_image_path)
            image.thumbnail((200, 200))
            photo = ImageTk.PhotoImage(image)
            self.image_preview.config(image=photo, text="")
            self.image_preview.image = photo

if __name__ == "__main__":
    root = Tk()
    app = ImageImporterApp(root)
    root.mainloop()