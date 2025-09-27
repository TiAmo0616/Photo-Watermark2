import os
import json
from tkinter import Tk, Label, Button, Listbox, Entry, Scale, HORIZONTAL, filedialog, Canvas, StringVar, messagebox
from PIL import Image, ImageDraw, ImageFont, ImageTk
from tkinterdnd2 import DND_FILES, TkinterDnD
from tkinter import Canvas, Scrollbar, Frame,ttk,simpledialog

def make_scrollable(parent):
    """返回一个可滚动的 frame，所有控件都放这里"""
    canvas = Canvas(parent, highlightthickness=0)
    vbar = Scrollbar(parent, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=vbar.set)

    vbar.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)

    frame = Frame(canvas)
    canvas.create_window((0, 0), window=frame, anchor="nw")

    # 让框架大小随内容自动更新
    def on_configure(_):
        canvas.configure(scrollregion=canvas.bbox("all"))
    frame.bind("<Configure>", on_configure)

    # 鼠标滚轮支持（Windows & Linux）
    def on_wheel(event):
        canvas.yview_scroll(-1 * (event.delta // 120), "units")
    canvas.bind_all("<MouseWheel>", on_wheel)

    return frame

class WatermarkApp:
    def __init__(self, root):
        self.root = root  # 使用传入的 root 参数
        self.root.title("水印文件本地应用")

        # 1. 生成可滚动框架
        self.scrollable_frame = make_scrollable(root)


        # 图片导入部分
        self.import_label = Label(self.scrollable_frame, text="图片导入")
        self.import_label.pack()

        self.import_button = Button(self.scrollable_frame, text="导入图片", command=self.import_images)
        self.import_button.pack()

        self.folder_button = Button(self.scrollable_frame, text="导入文件夹", command=self.import_folder)
        self.folder_button.pack()

        self.image_listbox = Listbox(self.scrollable_frame, width=50, height=10)
        self.image_listbox.pack()
        self.image_listbox.bind("<<ListboxSelect>>", self.display_selected_image)

        # 水印设置部分
        self.watermark_label = Label(self.scrollable_frame, text="水印设置")
        self.watermark_label.pack()

        self.text_label = Label(self.scrollable_frame, text="水印文本：")
        self.text_label.pack()

        self.text_entry = Entry(self.scrollable_frame, width=30)
        self.text_entry.pack()
        self.text_entry.bind("<KeyRelease>", lambda e: self.preview_watermark())

        self.opacity_label = Label(self.scrollable_frame, text="透明度：")
        self.opacity_label.pack()

        #self.opacity_scale = Scale(self.scrollable_frame, from_=0, to=100, orient=HORIZONTAL)
        self.opacity_scale = Scale(self.scrollable_frame, from_=0, to=100, orient=HORIZONTAL,
                           command=lambda v: self.preview_watermark())
        self.opacity_scale.set(50)
        self.opacity_scale.pack()

        # self.preview_button = Button(self.scrollable_frame, text="预览水印", command=self.preview_watermark)
        # self.preview_button.pack()

        # 图片导出部分
        self.export_label = Label(self.scrollable_frame, text="图片导出")
        self.export_label.pack()

        self.export_folder_label = Label(self.scrollable_frame, text="导出文件夹：")
        self.export_folder_label.pack()

        self.export_folder_entry = Entry(self.scrollable_frame, width=50)
        self.export_folder_entry.pack()

        self.browse_button = Button(self.scrollable_frame, text="选择文件夹", command=self.select_export_folder)
        self.browse_button.pack()

        self.prefix_label = Label(self.scrollable_frame, text="文件名前缀：")
        self.prefix_label.pack()

        self.prefix_var = StringVar()
        self.prefix_entry = Entry(self.scrollable_frame, textvariable=self.prefix_var, width=50)
        self.prefix_entry.pack()

        self.suffix_label = Label(self.scrollable_frame, text="文件名后缀：")
        self.suffix_label.pack()

        self.suffix_var = StringVar()
        self.suffix_entry = Entry(self.scrollable_frame, textvariable=self.suffix_var, width=50)
        self.suffix_entry.pack()

        # 添加输出格式选择
        self.format_label = Label(self.scrollable_frame, text="输出格式：")
        self.format_label.pack()

        self.format_var = StringVar(value="JPEG")
        self.jpeg_radio = Button(self.scrollable_frame, text="JPEG", command=lambda: self.set_format("JPEG"))
        self.jpeg_radio.pack()

        self.png_radio = Button(self.scrollable_frame, text="PNG", command=lambda: self.set_format("PNG"))
        self.png_radio.pack()

        self.export_button = Button(self.scrollable_frame, text="导出图片", command=self.export_images)
        self.export_button.pack()

        # 图片预览部分
        self.canvas = Canvas(self.scrollable_frame, width=400, height=400, bg="gray")
        self.canvas.pack()

        # 数据存储
        self.image_paths = []
        self.current_image = None
        self.watermarked_image = None

        # 水印位置
        self.watermark_position = (0.5, 0.5)

        # 添加拖拽功能
        # 把拖拽目标从 root 换成 listbox
        self.image_listbox.drop_target_register(DND_FILES)
        self.image_listbox.dnd_bind('<<Drop>>', self.drop)

        # 水印布局部分
        self.layout_label = Label(self.scrollable_frame, text="水印布局")
        self.layout_label.pack()

        self.layout_buttons = {
            "左上": (0, 0), "上中": (0.5, 0), "右上": (1, 0),
            "左中": (0, 0.5), "中心": (0.5, 0.5), "右中": (1, 0.5),
            "左下": (0, 1), "下中": (0.5, 1), "右下": (1, 1)
        }

        for label, position in self.layout_buttons.items():
            Button(self.scrollable_frame, text=label, command=lambda pos=position: self.set_watermark_position(pos)).pack()

        self.canvas.bind("<Button-1>", self.on_watermark_press)
        self.canvas.bind("<B1-Motion>", self.on_watermark_move)
        self.canvas.bind("<ButtonRelease-1>", self.on_watermark_release)

       
        self.drag_data = None
        self.watermark_id = None

        self.tpl_combo = ttk.Combobox(self.scrollable_frame, state="readonly", width=20)
        self.tpl_combo.pack(pady=5)
        self.tpl_combo.bind("<<ComboboxSelected>>", self.on_template_selected)

        # 模板管理部分
        self.template_label = Label(self.scrollable_frame, text="水印模板管理")
        self.template_label.pack()

        self.save_template_button = Button(self.scrollable_frame, text="保存模板", command=self.save_template)
        self.save_template_button.pack()

        # self.load_template_button = Button(self.scrollable_frame, text="加载模板", command=self.load_all_templates)
        # self.load_template_button.pack()

        self.delete_template_button = Button(self.scrollable_frame, text="删除模板", command=self.delete_template)
        self.delete_template_button.pack()

        # 默认模板加载
        self.template_file = "templates.json"   # 固定文件名
        self.templates = []                     # 所有模板
        self.curr_tpl_idx = 0                   # 当前使用模板
        self.load_all_templates()               # 启动即加载

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
            # 切换图片后自动重绘当前水印
            self.preview_watermark()

    def display_image(self, image):
        image.thumbnail((400, 400))
        photo = ImageTk.PhotoImage(image)
        self.canvas.image = photo
        self.canvas.create_image(200, 200, image=photo)

    def set_watermark_position(self, position):
        self.watermark_position = position
        self.preview_watermark()

    def sync_combo(self):
        names = [t["name"] for t in self.templates]
        self.tpl_combo["values"] = names
        if names:
            self.tpl_combo.current(self.curr_tpl_idx)

    def on_template_selected(self, event):
        idx = self.tpl_combo.current()
        if idx >= 0:
            self.apply_template(idx)

    def apply_template(self, idx):
        tpl = self.templates[idx]
        self.text_entry.delete(0, "end")
        self.text_entry.insert(0, tpl["text"])
        self.opacity_scale.set(tpl["opacity"])
        self.watermark_position = tpl["position"]
        self.preview_watermark()
        self.curr_tpl_idx = idx

    def save_template(self):
        name = simpledialog.askstring("模板名称", "请输入模板名称：")
        if not name: return
        tpl = {
            "name": name,
            "text": self.text_entry.get(),
            "opacity": self.opacity_scale.get(),
            "position": self.watermark_position,
            "font": "arial.ttf",
            "color": "#FFFFFF"
        }
        self.templates.append(tpl)
        self.curr_tpl_idx = len(self.templates) - 1
        with open(self.template_file, "w") as f:
            json.dump(self.templates, f, indent=2)
        self.sync_combo()
        messagebox.showinfo("完成", f"模板“{name}”已保存！")

    def load_all_templates(self):
        try:
            with open(self.template_file, "r") as f:
                self.templates = json.load(f)
        except FileNotFoundError:
            self.templates = []   # 第一次运行文件不存在就空列表
        self.sync_combo()
        if self.templates:
            self.apply_template(0)  # 自动应用第一个

    def delete_template(self):
        if not self.templates: return
        name = self.templates[self.curr_tpl_idx]["name"]
        if messagebox.askyesno("确认", f"删除模板“{name}”？"):
            del self.templates[self.curr_tpl_idx]
            self.curr_tpl_idx = max(0, self.curr_tpl_idx - 1)
            with open(self.template_file, "w") as f:
                json.dump(self.templates, f, indent=2)
            self.sync_combo()
            # self.load_all_templates()
            if self.templates:
                self.apply_template(self.curr_tpl_idx)
            else:
                self.tpl_combo.set("")  # 完全清空显示

    
    def on_template_selected(self, event):
        idx = self.tpl_combo.current()
        if idx >= 0:
            self.apply_template(idx)

    def apply_template(self, idx):
        tpl = self.templates[idx]
        self.text_entry.delete(0, "end")
        self.text_entry.insert(0, tpl["text"])
        self.opacity_scale.set(tpl["opacity"])
        self.watermark_position = tpl["position"]
        self.preview_watermark()
        self.curr_tpl_idx = idx

    def preview_watermark(self):
        if not self.current_image:
            #messagebox.showwarning("警告", "请先选择图片！")
            return

        text   = self.text_entry.get()
        opacity = self.opacity_scale.get() / 100

        # 复制底图
        self.watermarked_image = self.current_image.copy()
        draw = ImageDraw.Draw(self.watermarked_image)
        font = ImageFont.load_default()

        # 用 textbbox 拿到文字框尺寸（兼容默认字体）
        left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
        tw, th = right - left, bottom - top

        # 基础中心坐标
        cx = self.watermarked_image.width * self.watermark_position[0]
        cy = self.watermarked_image.height * self.watermark_position[1]

        # 边缘安全偏移（2%）
        margin_x = self.watermarked_image.width  * 0.02
        margin_y = self.watermarked_image.height * 0.02

        # 根据九宫格决定偏移方向
        if self.watermark_position[0] == 0:          # 左
            cx = margin_x + tw / 2
        elif self.watermark_position[0] == 1:        # 右
            cx = self.watermarked_image.width - margin_x - tw / 2

        if self.watermark_position[1] == 0:          # 上
            cy = margin_y + th
        elif self.watermark_position[1] == 1:        # 下
            cy = self.watermarked_image.height - margin_y - th / 2 + top

        # 中心列/行保持原算法
        x = int(cx - tw / 2)
        y = int(cy - th / 2 - top)

        # 生成透明文字层
        text_layer = Image.new("RGBA", self.watermarked_image.size, (255, 255, 255, 0))
        text_draw = ImageDraw.Draw(text_layer)
        text_draw.text((x, y), text, font=font, fill=(255, 255, 255, int(255 * opacity)))

        # 合成并显示
        self.watermarked_image = Image.alpha_composite(self.watermarked_image.convert("RGBA"), text_layer)
        self.display_image(self.watermarked_image)

    def set_format(self, format):
        self.format_var.set(format)

    def select_export_folder(self):
        folder = filedialog.askdirectory(title="选择导出文件夹")
        if folder:
            self.export_folder_entry.delete(0, "end")
            self.export_folder_entry.insert(0, folder)

    def export_images(self):
        export_folder = self.export_folder_entry.get()
        prefix = self.prefix_var.get()
        suffix = self.suffix_var.get()
        output_format = self.format_var.get()

        if not export_folder:
            messagebox.showwarning("警告", "请先选择导出文件夹！")
            return

        if not self.image_paths:
            messagebox.showwarning("警告", "没有图片可导出！")
            return

        # 检查导出文件夹是否与原始图片所在文件夹相同
        for image_path in self.image_paths:
            if os.path.dirname(image_path) == export_folder:
                messagebox.showerror("错误", "导出文件夹不能与原始图片所在文件夹相同！")
                return

        text = self.text_entry.get()
        opacity = self.opacity_scale.get() / 100

        for image_path in self.image_paths:
            # 打开原始图片
            image = Image.open(image_path)

            # 创建水印
            # 创建水印（统一用 image 原始尺寸）
            watermarked_image = image.copy()
            draw = ImageDraw.Draw(watermarked_image)
            font = ImageFont.load_default()

            # 文字框尺寸
            left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
            tw, th = right - left, bottom - top

            # 基础中心
            cx = image.width * self.watermark_position[0]
            cy = image.height * self.watermark_position[1]

            # 边缘安全边距 2%
            margin_x = image.width * 0.02
            margin_y = image.height * 0.02

            # 横向边缘
            if self.watermark_position[0] == 0:          # 左
                cx = margin_x + tw / 2
            elif self.watermark_position[0] == 1:        # 右
                cx = image.width - margin_x - tw / 2

            # 纵向边缘
            if self.watermark_position[1] == 0:          # 上
                cy = margin_y + th - top          # -top 把 baseline 下移，避免升部被裁
            elif self.watermark_position[1] == 1:        # 下
                cy = image.height - margin_y - th / 2 - top

            # 最终左上角
            x = int(cx - tw / 2)
            y = int(cy - th / 2 - top)

            # 生成文字层并合成
            text_layer = Image.new("RGBA", watermarked_image.size, (255, 255, 255, 0))
            text_draw = ImageDraw.Draw(text_layer)
            text_draw.text((x, y), text, font=font, fill=(255, 255, 255, int(255 * opacity)))
            watermarked_image = Image.alpha_composite(watermarked_image.convert("RGBA"), text_layer)
                        

            # 保存水印图片
            base_name = os.path.basename(image_path)
            name, ext = os.path.splitext(base_name)
            new_name = f"{prefix}{name}{suffix}.{output_format.lower()}"
            export_path = os.path.join(export_folder, new_name)
            watermarked_image.convert("RGB").save(export_path, format=output_format)

        messagebox.showinfo("完成", "图片导出完成！")

    def drop(self, event):
        # 获取拖拽的文件路径
        file_path = event.data.strip()
        if os.path.isfile(file_path):
            if file_path.lower().endswith((".jpg", ".jpeg", ".png", ".bmp", ".tiff")):
                self.image_paths.append(file_path)
                self.image_listbox.insert("end", os.path.basename(file_path))
                print(f"已拖拽导入图片: {file_path}")
        return "break"
    
    def on_watermark_press(self, event):
        # 记录鼠标按下时的位置
        self.drag_data = (event.x, event.y)

    def on_watermark_move(self, event):
        if self.drag_data and self.watermarked_image:
            # 计算鼠标移动的偏移量
            dx = event.x - self.drag_data[0]
            dy = event.y - self.drag_data[1]

            # 更新水印位置
            self.watermark_position = (
                self.watermark_position[0] + dx / self.canvas.winfo_width(),
                self.watermark_position[1] + dy / self.canvas.winfo_height()
            )

            # 重新预览水印
            self.preview_watermark()

            # 更新拖拽数据
            self.drag_data = (event.x, event.y)

    def on_watermark_release(self, event):
        # 清除拖拽数据
        self.drag_data = None

if __name__ == "__main__":
    root = TkinterDnD.Tk()  
    app = WatermarkApp(root)
    root.mainloop()