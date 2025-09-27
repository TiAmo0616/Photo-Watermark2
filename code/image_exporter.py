import os
from tkinter import Tk, filedialog, Listbox, Button, Label, PhotoImage, Entry, StringVar
from PIL import Image, ImageTk

class ImageExporterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("图片导出工具")

        # UI Elements
        self.label = Label(root, text="已导入图片：")
        self.label.pack()

        self.listbox = Listbox(root, width=50, height=15)
        self.listbox.pack()

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

        # Store imported images
        self.image_paths = []

    def select_export_folder(self):
        folder = filedialog.askdirectory(title="选择导出文件夹")
        if folder:
            self.export_folder_entry.delete(0, "end")
            self.export_folder_entry.insert(0, folder)

    def export_images(self):
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
    app = ImageExporterApp(root)
    root.mainloop()