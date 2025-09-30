import base64
import copy
import io
import os
import json
from tkinter import Radiobutton, Tk, Label, Button, Listbox, Entry, Scale, HORIZONTAL, filedialog, Canvas, StringVar, messagebox
import tkinter as tk
from PIL import Image, ImageDraw, ImageFont, ImageTk, ImageOps
import numpy as np
from tkinterdnd2 import DND_FILES, TkinterDnD
from tkinter import Canvas, Scrollbar, Frame,ttk,simpledialog,Checkbutton,IntVar,OptionMenu,colorchooser
import matplotlib.font_manager

def make_scrollable(parent):
    """返回一个可滚动的 frame，所有控件都放这里"""
    canvas = Canvas(parent, highlightthickness=0, bg="#f8fafc")
    vbar = Scrollbar(parent, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=vbar.set)

    vbar.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)

    frame = Frame(canvas, bg="#f8fafc")
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
    PREVIEW_MAX_W = 540          # 预览区最大宽度
    PREVIEW_MAX_H = 690          # 预览区最大高度
    # -------------------- 主入口 --------------------
    def __init__(self, root):
        self.root = root
        self.root.title("水印文件本地应用")
        self.root.geometry("1200x800")
        self.root.configure(bg="#f1f5f9")


        # 创建左右分栏
        self.paned_window = tk.PanedWindow(root, orient=tk.HORIZONTAL, bg="#e2e8f0", sashwidth=3)
        self.paned_window.pack(fill=tk.BOTH, expand=1)

        # 左侧
        self.settings_frame = tk.Frame(self.paned_window, width=640, height=900, bg="#f8fafc", relief="raised", bd=1)
        self.paned_window.add(self.settings_frame)

        # 右侧
        self.preview_frame = tk.Frame(self.paned_window, width=640, height=900, bg="#f1f5f9")
        self.paned_window.add(self.preview_frame)

        # 设置初始大小比例为1:1
        self.paned_window.sash_place(0, 600, 0)

        # 防止 Frame 被压缩
        self.settings_frame.pack_propagate(False)
        self.preview_frame.pack_propagate(False)

        # 左侧滚动区域
        self.scrollable_frame = make_scrollable(self.settings_frame)  # 通用滚动区域

        # 1. 数据初始化（变量先全部立好）
        self._init_data()

        # 2. 界面区域搭建
        self._build_image_import()
        self._build_text_watermark()
        self._build_image_watermark()
        self._build_layout()
        self._build_template()
        self._build_export()
        self._build_preview()  # 将预览区域移到右侧

        # 3. 业务事件绑定
        self._bind_events()

        # 4. 启动后动作
        self.load_all_templates()   # 模板自动加载

        # -------------------- 1. 变量仓库 --------------------
    def _init_data(self):
        self.image_paths = []
        self.current_image = None
        self.watermarked_image = None

        # 文本水印
        self.watermark_position = (0.5, 0.5)
        # 图片水印
        self.image_watermark_pos = (0.5, 0.5)
        self.watermark_image = None
        self.watermark_scale = 1.0
        self.watermark_opacity = 1.0

        # 模板
        self.template_file = "templates.json"
        self.templates = []

        #
        self.curr_tpl_idx = 0
        self.selected_watermark = "text"  # 当前选中的水印类型，"text" 或 "image"

        # 拖拽标志
        self.drag_target = None

         # 9 宫格位置表
        self.layout_buttons = {
            "左上": (0, 0), "上中": (0.5, 0), "右上": (1, 0),
            "左中": (0, 0.5), "中心": (0.5, 0.5), "右中": (1, 0.5),
            "左下": (0, 1), "下中": (0.5, 1), "右下": (1, 1)
        }

        self.cur_operate = StringVar(value="text")   # 当前操作模式：text / image

        self.text_rotate  = tk.DoubleVar(value=0.0)
        self.image_rotate = tk.DoubleVar(value=0.0)

        # 文件名前缀和后缀
        self.prefix_var = StringVar(value="")
        self.suffix_var = StringVar(value="")
        
        # 导出格式
        self.format_var = StringVar(value="JPEG")

    # -------------------- 2. 图片导入 --------------------
    def _build_image_import(self):
        section_frame = ttk.LabelFrame(self.scrollable_frame, text="图片导入", padding=(15, 10), style="Custom.TLabelframe")
        section_frame.pack(fill="x", pady=15, padx=20)

        # 创建按钮框架
        button_frame = tk.Frame(section_frame, bg="#f8fafc")
        button_frame.pack(fill="x", pady=10)

        self.import_button = ttk.Button(button_frame, text="导入图片", command=self.import_images, style="Accent.TButton")
        self.import_button.pack(side="left", padx=5)

        self.folder_button = ttk.Button(button_frame, text="导入文件夹", command=self.import_folder, style="Accent.TButton")
        self.folder_button.pack(side="left", padx=5)

        # 创建一个框架来包含Listbox和滚动条
        listbox_frame = tk.Frame(section_frame, bg="#f8fafc")
        listbox_frame.pack(pady=10)

        # 创建Listbox和滚动条
        self.image_listbox = Listbox(listbox_frame, width=50, height=10, relief="solid", borderwidth=1, 
                                     bg="white", fg="#1e293b", font=("Arial", 10),
                                     selectbackground="#3b82f6", selectforeground="white")
        
        # 创建垂直滚动条
        listbox_scrollbar = Scrollbar(listbox_frame, orient="vertical", command=self.image_listbox.yview)
        self.image_listbox.configure(yscrollcommand=listbox_scrollbar.set)
        
        # 布局Listbox和滚动条
        self.image_listbox.pack(side="left", fill="both", expand=True)
        listbox_scrollbar.pack(side="right", fill="y")

        self.image_listbox.bind("<<ListboxSelect>>", self.display_selected_image)

        self.image_listbox.drop_target_register(DND_FILES)
        self.image_listbox.dnd_bind('<<Drop>>', self.drop)

        operate_frame = ttk.Frame(section_frame)
        operate_frame.pack(pady=10)
        ttk.Radiobutton(operate_frame, text="操作文本水印", variable=self.cur_operate,
                        value="text", command=self._on_operate_change, style="TRadiobutton").pack(side="left", padx=15)
        ttk.Radiobutton(operate_frame, text="操作图片水印", variable=self.cur_operate,
                        value="image", command=self._on_operate_change, style="TRadiobutton").pack(side="left", padx=15)

    # -------------------- 3. 文本水印 --------------------
    def _build_text_watermark(self):
         
        # 创建一个容器框架来容纳文本和图片水印设置
        watermarks_frame = ttk.Frame(self.scrollable_frame)
        watermarks_frame.pack(fill="x", pady=15, padx=20)

        # 文本水印设置 (改为在左侧显示)
        section_frame = ttk.LabelFrame(watermarks_frame, text="文本水印设置", padding=(15, 10), style="Custom.TLabelframe")
        section_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))

        self.text_label = ttk.Label(section_frame, text="水印文本：")
        self.text_label.pack(anchor="w", pady=(0, 5))

        self.text_entry = ttk.Entry(section_frame, width=30, font=("Arial", 11))
        self.text_entry.pack(pady=5)
        self.text_entry.bind("<KeyRelease>", lambda e: self.preview_watermark())

        self.opacity_label = ttk.Label(section_frame, text="透明度：")
        self.opacity_label.pack(anchor="w", pady=(10, 5))

        self.opacity_scale = ttk.Scale(section_frame, from_=0, to=100, orient=HORIZONTAL,
                                        command=lambda v: self.preview_watermark())
        self.opacity_scale.set(50)
        self.opacity_scale.pack(fill="x", pady=5)

        self.font_label = ttk.Label(section_frame, text="字体：")
        self.font_label.pack(anchor="w", pady=(10, 5))

        self.font_var = StringVar(value=self.get_system_fonts()[0])
        self.font_option = ttk.Combobox(section_frame, textvariable=self.font_var,
                                         values=self.get_system_fonts(), state="readonly", font=("Arial", 10))
        self.font_option.pack(pady=5)
        self.font_option.bind("<<ComboboxSelected>>", lambda _: self.preview_watermark())

        self.font_size_label = ttk.Label(section_frame, text="字号：")
        self.font_size_label.pack(anchor="w", pady=(10, 5))

        self.font_size_var = StringVar(value="20")
        self.font_size_entry = ttk.Entry(section_frame, textvariable=self.font_size_var, width=8, font=("Arial", 11))
        self.font_size_entry.pack(pady=5)
        self.font_size_entry.bind("<KeyRelease>", lambda e: self.preview_watermark())


        # 样式
        style_frame = tk.Frame(section_frame, bg="#f8fafc")
        style_frame.pack(anchor="w", pady=10)
        
        self.bold_var = IntVar()
        self.bold_checkbox = Checkbutton(style_frame, text="粗体", variable=self.bold_var, command=self.preview_watermark, 
                                         bg="#f8fafc", activebackground="#e2e8f0", fg="#1e293b", selectcolor="white")
        self.bold_checkbox.pack(side="left", padx=(0, 15))

        self.italic_var = IntVar()
        self.italic_checkbox = Checkbutton(style_frame, text="斜体", variable=self.italic_var, command=self.preview_watermark,
                                           bg="#f8fafc", activebackground="#e2e8f0", fg="#1e293b", selectcolor="white")
        self.italic_checkbox.pack(side="left")

        # 颜色
        color_frame = tk.Frame(section_frame, bg="#f8fafc")
        color_frame.pack(anchor="w", pady=10)
        
        self.color_button = ttk.Button(color_frame, text="选择字体颜色", command=self.choose_color)
        self.color_button.pack(side="left", padx=(0, 10))
        
        self.color_label = ttk.Label(color_frame, text="字体颜色：#FFFFFF")
        self.color_label.pack(side="left")

        # 特效
        effect_frame = tk.Frame(section_frame, bg="#f8fafc")
        effect_frame.pack(anchor="w", pady=10)
        
        self.shadow_var = IntVar()
        self.shadow_checkbox = Checkbutton(effect_frame, text="添加阴影", variable=self.shadow_var, command=self.preview_watermark,
                                           bg="#f8fafc", activebackground="#e2e8f0", fg="#1e293b", selectcolor="white")
        self.shadow_checkbox.pack(side="left", padx=(0, 15))

        self.stroke_var = IntVar()
        self.stroke_checkbox = Checkbutton(effect_frame, text="添加描边", variable=self.stroke_var, command=self.preview_watermark,
                                           bg="#f8fafc", activebackground="#e2e8f0", fg="#1e293b", selectcolor="white")
        self.stroke_checkbox.pack(side="left")

         # ====== 新增：文本旋转 ======
        rot_frame = tk.Frame(section_frame, bg="#f8fafc")
        rot_frame.pack(anchor="w", pady=10)
        tk.Label(rot_frame, text="旋转角度：", bg="#f8fafc", fg="#1e293b").pack(side=tk.LEFT)
        self.text_rot_spin = ttk.Spinbox(
            rot_frame,
            from_=-360, to=360, increment=0.1,
            textvariable=self.text_rotate,
            width=8,
            command=self.preview_watermark
        )
        self.text_rot_spin.pack(side=tk.LEFT, padx=(5, 0))
        self.text_rotate.trace_add("write", lambda *_: self.preview_watermark())
        # =================================

    # -------------------- 4. 图片水印 --------------------
    def _build_image_watermark(self):
        # 图片水印设置 (改为在右侧显示)
        watermarks_frame = self.scrollable_frame.winfo_children()[-1]  # 获取刚刚创建的容器框架
        section_frame = ttk.LabelFrame(watermarks_frame, text="图片水印设置", padding=(15, 10), style="Custom.TLabelframe")
        section_frame.pack(side="right", fill="both", expand=True, padx=(10, 0))

        self.import_watermark_button = ttk.Button(section_frame, text="导入图片水印", command=self.import_watermark_image, style="Accent.TButton")
        self.import_watermark_button.pack(pady=10)

        self.scale_label = ttk.Label(section_frame, text="水印缩放：")
        self.scale_label.pack(anchor="w", pady=(10, 5))

        self.scale_slider = Scale(section_frame, from_=0.01, to=2.0, orient=HORIZONTAL, resolution=0.1, command=lambda v: self.scale_watermark_image(float(v)),
                                  bg="#f8fafc", activebackground="#3b82f6", troughcolor="#cbd5e1", highlightthickness=0, length=200)
        self.scale_slider.set(1.0)
        self.scale_slider.pack(fill="x", pady=5)

        self.opacity_label = Label(section_frame, text="水印透明度：", bg="#f8fafc", fg="#1e293b")
        self.opacity_label.pack(anchor="w", pady=(10, 5))

        self.opacity_slider = Scale(section_frame, from_=0, to=100, orient=HORIZONTAL, 
                               command=lambda v: self.set_watermark_opacity(int(v)/100.0 ),
                               bg="#f8fafc", activebackground="#3b82f6", troughcolor="#cbd5e1", highlightthickness=0, length=200)
        self.opacity_slider.set(100)  
        self.opacity_slider.pack(fill="x", pady=5)

        # ====== 新增：图片旋转 ====== 
        rot_frame = tk.Frame(section_frame, bg="#f8fafc")
        rot_frame.pack(anchor="w", pady=10)
        tk.Label(rot_frame, text="旋转角度：", bg="#f8fafc", fg="#1e293b").pack(side=tk.LEFT)
        self.image_rot_spin = ttk.Spinbox(
            rot_frame,
            from_=-360, to=360, increment=0.1,
            textvariable=self.image_rotate,
            width=8,
            command=self.preview_watermark
        )
        self.image_rot_spin.pack(side=tk.LEFT, padx=(5, 0))
        self.image_rotate.trace_add("write", lambda *_: self.preview_watermark())
        # =================================


    # -------------------- 5. 导出 --------------------
    def _build_export(self):
        section_frame = ttk.LabelFrame(self.scrollable_frame, text="图片导出", padding=(15, 10), style="Custom.TLabelframe")
        section_frame.pack(fill="x", pady=15, padx=20)

        self.export_folder_label = ttk.Label(section_frame, text="导出文件夹：")
        self.export_folder_label.pack(anchor="w", pady=(0, 5))

        self.export_folder_entry = ttk.Entry(section_frame, width=50, font=("Arial", 11))
        self.export_folder_entry.pack(pady=5)

        self.browse_button = ttk.Button(section_frame, text="选择文件夹", command=self.select_export_folder)
        self.browse_button.pack(pady=10)

        # 添加格式选择
        self.format_label = ttk.Label(section_frame, text="导出格式：")
        self.format_label.pack(anchor="w", pady=(10, 5))

        format_frame = ttk.Frame(section_frame)
        format_frame.pack(anchor="w", pady=5)

        ttk.Radiobutton(format_frame, text="JPEG", variable=self.format_var, value="JPEG").pack(side="left", padx=(0, 15))
        ttk.Radiobutton(format_frame, text="PNG", variable=self.format_var, value="PNG").pack(side="left")

        self.prefix_label = ttk.Label(section_frame, text="文件名前缀：")
        self.prefix_label.pack(anchor="w", pady=(10, 5))

        self.prefix_entry = ttk.Entry(section_frame, textvariable=self.prefix_var, width=50, font=("Arial", 11))
        self.prefix_entry.pack(pady=5)

        self.suffix_label = ttk.Label(section_frame, text="文件名后缀：")
        self.suffix_label.pack(anchor="w", pady=(10, 5))

        self.suffix_entry = ttk.Entry(section_frame, textvariable=self.suffix_var, width=50, font=("Arial", 11))
        self.suffix_entry.pack(pady=5)

        self.export_button = ttk.Button(section_frame, text="导出图片", command=self.export_images, style="Export.TButton")
        self.export_button.pack(pady=15)

    # -------------------- 6. 预览 --------------------
    def _build_preview(self):
        # 在右侧界面创建预览区域
       
        self.preview_canvas= Canvas(
            self.preview_frame,           # ← 关键：放在右侧容器
            width=420, height=420,
            bg="#ffffff",
            highlightthickness=2, 
            highlightbackground="#94a3b8"
        )
        self.preview_canvas.pack(fill="both", expand=True, padx=20, pady=20)

        # 添加标题标签
        preview_title = tk.Label(self.preview_frame, text="图片预览", bg="#f1f5f9", font=("Arial", 14, "bold"), fg="#1e293b")
        preview_title.pack()

    # -------------------- 7. 布局 --------------------
    def _build_layout(self):
        layout_frame = ttk.LabelFrame(self.scrollable_frame, text="水印布局", padding=(15, 10), style="Custom.TLabelframe")
        layout_frame.pack(fill="x", pady=15, padx=20)
        
        button_frame = ttk.Frame(layout_frame)
        button_frame.pack()
        
        for label, position in self.layout_buttons.items():
            btn = Button(button_frame, text=label, command=lambda pos=position: self.set_watermark_position(pos),
                         bg="#e2e8f0", activebackground="#94a3b8", relief="raised", bd=1, 
                         fg="#1e293b", font=("Arial", 9))
            btn.pack(side=tk.LEFT, padx=3, pady=5)
            # 添加悬停效果
            btn.bind("<Enter>", lambda e: e.widget.config(bg="#cbd5e1"))
            btn.bind("<Leave>", lambda e: e.widget.config(bg="#e2e8f0"))

    # -------------------- 8. 模板 --------------------
    def _build_template(self):
        
        template_frame = ttk.LabelFrame(self.scrollable_frame, text="水印模板管理", padding=(15, 10), style="Custom.TLabelframe")
        template_frame.pack(fill="x", pady=15, padx=20)

        tpl_select_frame = ttk.Frame(template_frame)
        tpl_select_frame.pack(fill="x", pady=10)
        
        ttk.Label(tpl_select_frame, text="模板加载：").pack(side="left")
        self.tpl_combo = ttk.Combobox(tpl_select_frame, state="readonly", width=25, font=("Arial", 10))
        self.tpl_combo.pack(side="left", padx=10)
        self.tpl_combo.bind("<<ComboboxSelected>>", self.on_template_selected)

        button_frame = tk.Frame(template_frame, bg="#f8fafc")
        button_frame.pack(fill="x", pady=10)

        self.save_template_button = Button(button_frame, text="保存模板", command=self.save_template,
                                           bg="#10b981", fg="white", activebackground="#059669", 
                                           relief="flat", font=("Arial", 10, "bold"),
                                           padx=10, pady=5)
        self.save_template_button.pack(side=tk.LEFT, padx=5)

        self.delete_template_button = Button(button_frame, text="删除模板", command=self.delete_template,
                                             bg="#ef4444", fg="white", activebackground="#dc2626", 
                                             relief="flat", font=("Arial", 10, "bold"),
                                             padx=10, pady=5)
        self.delete_template_button.pack(side=tk.LEFT, padx=5)

    # -------------------- 9. 事件绑定 --------------------
    def _bind_events(self):
        self.image_listbox.bind("<<ListboxSelect>>", self.display_selected_image)
        self.image_listbox.drop_target_register(DND_FILES)
        self.image_listbox.dnd_bind('<<Drop>>', self.drop)

        self.preview_canvas.bind("<Button-1>", self.on_watermark_press)
        self.preview_canvas.bind("<B1-Motion>", self.on_watermark_move)
        self.preview_canvas.bind("<ButtonRelease-1>", self.on_watermark_release)

    def get_system_fonts(self):
        fonts = matplotlib.font_manager.findSystemFonts(fontpaths=None, fontext='ttf')
        font_names = [os.path.basename(font).split('.')[0] for font in fonts]
        return sorted(set(font_names))

    def choose_color(self):
        color = colorchooser.askcolor()[1]
        if color:
            self.color_label.config(text=f"字体颜色：{color}")
            self.preview_watermark()

    def get_font_path(self, font_name, bold, italic):
        # 动态查找系统字体路径
        font_files = matplotlib.font_manager.findSystemFonts(fontpaths=None, fontext='ttf')
        font_paths = {os.path.basename(font).split('.')[0]: font for font in font_files}

        # 首先尝试查找专门的粗体/斜体字体文件
        font_file_name = font_name
        if bold and italic:
            # 尝试多种可能的粗体斜体命名方式
            candidates = [
                f"{font_name}-bold-italic",
                f"{font_name}-bolditalic",
                f"{font_name}-BoldItalic",
                f"{font_name}BI",
                f"{font_name}-BI"
            ]
            for candidate in candidates:
                if candidate in font_paths:
                    return font_paths[candidate],1
        elif bold:
            # 尝试多种可能的粗体命名方式
            candidates = [
                f"{font_name}-bold",
                f"{font_name}-Bold",
                f"{font_name}B",
                f"{font_name}-B",
                f"{font_name}b"
            ]
            for candidate in candidates:
                if candidate in font_paths:
                    return font_paths[candidate],1
        elif italic:
            # 尝试多种可能的斜体命名方式
            candidates = [
                f"{font_name}-italic",
                f"{font_name}-Italic",
                f"{font_name}I",
                f"{font_name}-I",
                f"{font_name}i"
            ]
            for candidate in candidates:
                if candidate in font_paths:
                    return font_paths[candidate],1

        # 如果没有找到专门的样式字体文件，返回基础字体
        # PIL/Pillow 会在绘制时处理粗体和斜体样式
        return font_paths.get(font_name),0

    def get_font(self, font_name, font_size, bold=False, italic=False):
        """
        获取字体，支持粗体和斜体
        """
        # 分别检查粗体和斜体字体文件是否存在
        bold_font_path, bold_found = self.get_font_path(font_name, bold, False) if bold else (None, 0)
        italic_font_path, italic_found = self.get_font_path(font_name, False, italic) if italic else (None, 0)
        bold_italic_font_path, bold_italic_found = self.get_font_path(font_name, bold, italic) if (bold and italic) else (None, 0)
        
        # 根据不同的组合情况选择字体文件
        font_path = None
        style_found = 0
        
        if bold and italic and bold_italic_found:
            font_path = bold_italic_font_path
            style_found = 1
        elif bold and italic and bold_found and italic_found:
            # 有单独的粗体和斜体文件，但没有粗斜体文件
            font_path = bold_font_path  # 使用粗体文件
            style_found = 1
        elif bold and italic and bold_found:
            font_path = bold_font_path
            style_found = 1
        elif bold and italic and italic_found:
            font_path = italic_font_path
            style_found = 1
        elif bold and bold_found:
            font_path = bold_font_path
            style_found = 1
        elif italic and italic_found:
            font_path = italic_font_path
            style_found = 1
        else:
            # 没有找到特殊样式字体，使用基础字体
            font_path, style_found = self.get_font_path(font_name, False, False)
        
        if font_path:
            try:
                # 只有在找不到特定样式字体时才取消勾选
                if bold and not (bold_found or bold_italic_found):
                    messagebox.showwarning("提示", "该字体暂不支持加粗！")
                    self.bold_var.set(0)
                if italic and not (italic_found or bold_italic_found):
                    messagebox.showwarning("提示", "该字体暂不支持斜体！")
                    self.italic_var.set(0)
                    
                # 使用指定的字体文件
                font = ImageFont.truetype(font_path, font_size)
                return font
            except Exception as e:
                print(f"加载字体失败: {e}")
        
        # 如果特定字体加载失败，尝试使用默认字体并设置样式
        try:
            # 尝试使用默认字体
            font = ImageFont.load_default()
            return font
        except:
            # 最后的备选方案
            return ImageFont.load_default()

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
        max_w = self.PREVIEW_MAX_W
        max_h = self.PREVIEW_MAX_H
        scale = min(max_w / image.width, max_h / image.height)
        if scale < 1.0:
            image = image.resize((int(image.width * scale),
                                int(image.height * scale)), Image.LANCZOS)

        # 居中偏移
        self.offset_x = (max_w - image.width) // 2
        self.offset_y = (max_h - image.height) // 2

        photo = ImageTk.PhotoImage(image)
        self.preview_canvas.delete("all")
        self.preview_canvas.create_image(self.offset_x, self.offset_y,
                                        anchor='nw', image=photo)
        self.preview_canvas.image = photo          # 防回收

        # 边框（可选）
        

    def set_watermark_position(self, position):
        if self.cur_operate.get() == "text":
            self.watermark_position = position
        else:
            self.image_watermark_pos = position
        self.preview_watermark()


    def sync_combo(self):
        names = [t["name"] for t in self.templates]
        # 添加"无模板"选项
        self.tpl_combo["values"] = ["无模板"] + names
        if names:
            self.tpl_combo.current(self.curr_tpl_idx + 1)  # +1 because of "无模板" option
        else:
            self.tpl_combo.current(0)

    def on_template_selected(self, event):
        idx = self.tpl_combo.current()
        if idx == 0:  # 选择了"无模板"
            self.clear_all_settings()
        elif idx > 0:  # 选择了具体模板
            self.apply_template(idx - 1)  # -1 to account for "无模板" option

    def apply_template(self, idx):
        tpl = self.templates[idx]

        # 文字部分
        self.text_entry.delete(0, "end")
        self.text_entry.insert(0, tpl.get("text", ""))
        self.opacity_scale.set(tpl.get("opacity", 50))
        self.watermark_position = tuple(tpl.get("position", (0.5, 0.5)))
        self.font_var.set(tpl.get("font", "arial"))
        self.font_size_var.set(str(tpl.get("font_size", 20)))
        self.bold_var.set(int(tpl.get("bold", 0)))
        self.italic_var.set(int(tpl.get("italic", 0)))
        color = tpl.get("color", "#FFFFFF")
        self.color_label.config(text=f"字体颜色：{color}")
        self.shadow_var.set(int(tpl.get("shadow", 0)))
        self.stroke_var.set(int(tpl.get("stroke", 0)))

        # 图片部分（若无则给默认值）
        # 图片水印内嵌数据
        img_data = tpl.get('image_data')
        if img_data:
            buf = io.BytesIO(base64.b64decode(img_data))
            self.watermark_image = Image.open(buf).convert("RGBA")
            # 同步原始尺寸
            self.watermark_original_width  = self.watermark_image.width
            self.watermark_original_height = self.watermark_image.height
        else:
            self.watermark_image = None
        self.watermark_scale = tpl.get("image_scale", 1.0)
        self.watermark_opacity = tpl.get("image_opacity", 1.0)
        self.image_watermark_pos = tuple(tpl.get("image_pos", (0.5, 0.5)))

        # 同步滑块
        self.scale_slider.set(self.watermark_scale)
        self.opacity_slider.set(self.watermark_opacity * 100)

        self.text_rotate.set(tpl.get("text_rotate", 0.0))
        self.image_rotate.set(tpl.get("image_rotate", 0.0))

        self.curr_tpl_idx = idx
        self.preview_watermark()

    
    def save_template(self):
        name = simpledialog.askstring("模板名称", "请输入模板名称：")
        if not name:
            return
        tpl = {
            "name": name,
            "text": self.text_entry.get(),
            "opacity": self.opacity_scale.get(),
            "position": self.watermark_position,
            "font": self.font_var.get(),
            "font_size": int(self.font_size_var.get()),
            "bold": bool(self.bold_var.get()),
            "italic": bool(self.italic_var.get()),
            "color": self.color_label.cget("text").split("：")[1],
            "shadow": bool(self.shadow_var.get()),
            "stroke": bool(self.stroke_var.get()),
            "image_scale": self.watermark_scale,
            "image_opacity": self.watermark_opacity,
            "image_pos": self.image_watermark_pos,
            "text_rotate": self.text_rotate.get(),      # 新增
            "image_rotate": self.image_rotate.get(),     # 新增
            "type": "full"          # 标记为新格式，方便以后扩展
        }
        # 如果当前有水印图，就内嵌
        if self.watermark_image:
            buf = io.BytesIO()
            self.watermark_image.save(buf, format='PNG')
            buf.seek(0)
            tpl['image_data'] = base64.b64encode(buf.read()).decode('utf-8')
        else:
            tpl['image_data'] = None
            
        self.templates.append(copy.deepcopy(tpl))
        self.curr_tpl_idx = len(self.templates) - 1
        with open(self.template_file, "w", encoding='utf-8') as f:
            json.dump(self.templates, f, indent=2, ensure_ascii=False)
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

    def clear_all_settings(self):
        """清空所有水印设置"""
        # 清空文本水印设置
        self.text_entry.delete(0, "end")
        self.opacity_scale.set(50)
        self.watermark_position = (0.5, 0.5)
        self.font_var.set(self.get_system_fonts()[0] if self.get_system_fonts() else "arial")
        self.font_size_var.set("20")
        self.bold_var.set(0)
        self.italic_var.set(0)
        self.color_label.config(text="字体颜色：#FFFFFF")
        self.shadow_var.set(0)
        self.stroke_var.set(0)
        self.text_rotate.set(0.0)
        
        # 清空图片水印设置
        self.watermark_image = None
        self.watermark_scale = 1.0
        self.watermark_opacity = 1.0
        self.image_watermark_pos = (0.5, 0.5)
        self.image_rotate.set(0.0)
        
        # 重置滑块
        self.scale_slider.set(1.0)
        self.opacity_slider.set(100)
        
        # 更新预览
        self.preview_watermark()

    def preview_watermark(self):
        if not self.current_image:
            return

        # 复制底图
        self.watermarked_image = self.current_image.copy()

        scale = min(self.PREVIEW_MAX_W / self.watermarked_image.width,
                    self.PREVIEW_MAX_H / self.watermarked_image.height)
        self.preview_scale = scale   


        # 如果有文字水印
        if self.text_entry.get():
            text = self.text_entry.get()
            opacity = self.opacity_scale.get() / 100
            font_name = self.font_var.get()
            font_size = int(self.font_size_var.get())
            bold = self.bold_var.get()
            italic = self.italic_var.get()
            color = self.color_label.cget("text").split("：")[1]
            shadow = self.shadow_var.get()
            stroke = self.stroke_var.get()
            angle = self.text_rotate.get()

            # 获取字体
            try:
                font = self.get_font(font_name, font_size, bold, italic)
            except Exception as e:
                messagebox.showerror("错误", f"无法加载字体: {str(e)}")
                return

            # draw = ImageDraw.Draw(self.watermarked_image)
            temp = Image.new("RGBA", self.watermarked_image.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(temp)
            left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
            tw, th = right - left, bottom - top

            cx = self.watermarked_image.width * self.watermark_position[0]
            cy = self.watermarked_image.height * self.watermark_position[1]

            margin_x = self.watermarked_image.width * 0.02
            margin_y = self.watermarked_image.height * 0.02

            if self.watermark_position[0] == 0:  # 左
                cx = margin_x + tw / 2
            elif self.watermark_position[0] == 1:  # 右
                cx = self.watermarked_image.width - margin_x - tw / 2

            if self.watermark_position[1] == 0:  # 上
                cy = margin_y + th - top
            elif self.watermark_position[1] == 1:  # 下
                cy = self.watermarked_image.height - margin_y - th / 2 - top

            x = int(cx - tw / 2)
            y = int(cy - th / 2 - top)

                        # 0. 先准备空白层
            text_layer = Image.new("RGBA", self.watermarked_image.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(text_layer)          # 用 text_layer 画！

            # 1. 阴影 / 描边 / 正文（全部画在 text_layer）
            if shadow:
                shadow_color = (0, 0, 0, int(255 * 0.5))
                draw.text((x + 2, y + 2), text, font=font, fill=shadow_color)
            if stroke:
                stroke_color = (0, 0, 0, int(255 * 0.5))
                for dx, dy in [(-2, -2), (-2, 2), (2, -2), (2, 2)]:
                    draw.text((x + dx, y + dy), text, font=font, fill=stroke_color)
            draw.text((x, y), text,
                      font=font,
                      fill=(int(color[1:3], 16),
                            int(color[3:5], 16),
                            int(color[5:7], 16),
                            int(255 * opacity)))

            # 2. 旋转
            if angle != 0:
                rot_center = (x + tw // 2, y + th // 2)
                text_layer = text_layer.rotate(angle, center=rot_center, expand=0)

            # 3. 合成
            self.watermarked_image = Image.alpha_composite(
                self.watermarked_image.convert("RGBA"), text_layer)
            
            
            self.text_bbox = (
                int(x * scale) + self.offset_x,
                int(y * scale) + self.offset_y,
                int((x + tw) * scale) + self.offset_x,
                int((y + th) * scale) + self.offset_y
            )

        
        # ---------- 图片水印 ----------
              
        if self.watermark_image:
            angle = self.image_rotate.get()          # 新增：获取旋转角度

            # 1. 缩放
            new_width = int(self.watermark_original_width * self.watermark_scale)
            new_height = int(self.watermark_original_height * self.watermark_scale)
            
            # 确保尺寸大于0
            if new_width > 0 and new_height > 0:
                watermark = self.watermark_image.resize((new_width, new_height), Image.LANCZOS)

                # 2. 透明度
                transparent_layer = Image.new("RGBA", watermark.size, (255, 255, 255, 0))
                watermark = Image.blend(transparent_layer, watermark, self.watermark_opacity)

                # 3. 旋转（expand=1 保证四角完整）
                if angle != 0:
                    watermark = watermark.rotate(angle, expand=1)

                # 4. 位置计算（用旋转后的尺寸）
                cx = self.watermarked_image.width * self.image_watermark_pos[0]
                cy = self.watermarked_image.height * self.image_watermark_pos[1]
                margin_x = self.watermarked_image.width * 0.02
                margin_y = self.watermarked_image.height * 0.02

                if self.image_watermark_pos[0] == 0:
                    cx = margin_x + watermark.width / 2
                elif self.image_watermark_pos[0] == 1:
                    cx = self.watermarked_image.width - margin_x - watermark.width / 2

                if self.image_watermark_pos[1] == 0:
                    cy = margin_y + watermark.height / 2
                elif self.image_watermark_pos[1] == 1:
                    cy = self.watermarked_image.height - margin_y - watermark.height / 2

                x = int(cx - watermark.width / 2)
                y = int(cy - watermark.height / 2)

                # 5. 粘贴
                self.watermarked_image.paste(watermark, (x, y), watermark)

                # 6. 记录预览命中框（缩放+偏移）
                w, h = watermark.size
                self.image_bbox = (
                    int(x * self.preview_scale) + self.offset_x,
                    int(y * self.preview_scale) + self.offset_y,
                    int((x + w) * self.preview_scale) + self.offset_x,
                    int((y + h) * self.preview_scale) + self.offset_y
                )
            else:
                # 如果尺寸无效，则不显示水印
                if hasattr(self, 'image_bbox'):
                    delattr(self, 'image_bbox')
        self.display_image(self.watermarked_image)

            
    # def display_image(self, image):
    #     max_width = 400
    #     max_height = 400
    #     if image.width > max_width or image.height > max_height:
    #         scale = min(max_width / image.width, max_height / image.height)
    #         image = image.resize((int(image.width * scale), int(image.height * scale)), Image.ANTIALIAS)
    #     else:
    #         scale = 1.0

    #     # 居中偏移量
    #     self.offset_x = (400 - image.width) // 2
    #     self.offset_y = (400 - image.height) // 2

    #     photo = ImageTk.PhotoImage(image)
    #     self.preview_canvas.image = photo  # 保持引用防止被垃圾回收
    #     self.preview_canvas.delete("all")  # 清除之前的图像
    #     # 用偏移量放置
    #     self.preview_canvas.create_image(200, 200, image=photo)
        
    #     # 添加边框
    #     self.preview_canvas.create_rectangle(1, 1, 399, 399, outline="#94a3b8", width=2)

    def set_format(self, format):
        self.format_var.set(format)

    def select_export_folder(self):
        folder = filedialog.askdirectory(title="选择导出文件夹")
        if folder:
            self.export_folder_entry.delete(0, "end")
            self.export_folder_entry.insert(0, folder)

    def import_watermark_image(self):
        filetypes = [("图片文件", "*.png;*.jpg;*.jpeg;*.bmp;*.tiff")]
        watermark_path = filedialog.askopenfilename(title="选择水印图片", filetypes=filetypes)
        if watermark_path:
            self.watermark_image_path = watermark_path
            self.watermark_image = Image.open(watermark_path).convert("RGBA")
            
            # 自动调整水印大小，使其不超过原始图片的尺寸
            max_watermark_size = min(self.current_image.width, self.current_image.height) * 0.5  # 水印最大尺寸为原始图片尺寸的20%
            watermark_width, watermark_height = self.watermark_image.size
            scale_factor = min(max_watermark_size / watermark_width, max_watermark_size / watermark_height)
            self.watermark_image = self.watermark_image.resize((int(watermark_width * scale_factor), int(watermark_height * scale_factor)), Image.ANTIALIAS)
            
            self.watermark_original_width = self.watermark_image.width
            self.watermark_original_height = self.watermark_image.height
            self.watermark_scale = 1.0  # 重置缩放比例
            self.watermark_opacity = 1.0  # 重置透明度
            self.preview_watermark()
            messagebox.showinfo("成功", "水印图片已成功加载！")

    def scale_watermark_image(self, scale):
        if self.watermark_image:
            self.watermark_scale = float(scale)
            self.preview_watermark()

    def set_watermark_opacity(self, opacity):
        if self.watermark_image:
            self.watermark_opacity = float(opacity) 
            self.preview_watermark()
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
        # 导出目录不能和源目录相同
        if any(os.path.dirname(f) == export_folder for f in self.image_paths):
            messagebox.showerror("错误", "导出文件夹不能与原始图片所在文件夹相同！")
            return

        # -------------- 文字水印参数 --------------
        text = self.text_entry.get()
        opacity = self.opacity_scale.get() / 100
        font_name = self.font_var.get()
        font_size = int(self.font_size_var.get())
        bold = self.bold_var.get()
        italic = self.italic_var.get()
        color = self.color_label.cget("text").split("：")[1]
        shadow = self.shadow_var.get()
        stroke = self.stroke_var.get()
        text_angle = self.text_rotate.get()          # 新增：文字旋转角度

        try:
            font = self.get_font(font_name, font_size, bold, italic)
        except Exception as e:
            messagebox.showerror("错误", f"无法加载字体: {str(e)}")
            return

        # -------------- 图片水印参数 --------------
        has_image_wm = bool(self.watermark_image)
        if has_image_wm:
            wm_scale = self.watermark_scale
            wm_opacity = self.watermark_opacity
            wm_pos = self.image_watermark_pos
            image_angle = self.image_rotate.get()    # 新增：图片旋转角度

        for img_path in self.image_paths:
            img = Image.open(img_path).convert("RGBA")
            canvas = Image.new("RGBA", img.size, (0, 0, 0, 0))

            # 1. 绘制文字水印
            if text:
                # 先画在独立图层上
                text_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
                draw = ImageDraw.Draw(text_layer)

                left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
                tw, th = right - left, bottom - top

                cx = img.width * self.watermark_position[0]
                cy = img.height * self.watermark_position[1]
                margin_x, margin_y = img.width * 0.02, img.height * 0.02

                if self.watermark_position[0] == 0:
                    cx = margin_x + tw / 2
                elif self.watermark_position[0] == 1:
                    cx = img.width - margin_x - tw / 2
                if self.watermark_position[1] == 0:
                    cy = margin_y + th - top
                elif self.watermark_position[1] == 1:
                    cy = img.height - margin_y - th / 2 - top

                x = int(cx - tw / 2)
                y = int(cy - th / 2 - top)

                # 阴影 / 描边 / 正文
                if shadow:
                    shadow_color = (0, 0, 0, int(255 * 0.5))
                    draw.text((x + 2, y + 2), text, font=font, fill=shadow_color)
                if stroke:
                    stroke_color = (0, 0, 0, int(255 * 0.5))
                    for dx, dy in [(-2, -2), (-2, 2), (2, -2), (2, 2)]:
                        draw.text((x + dx, y + dy), text, font=font, fill=stroke_color)
                draw.text((x, y), text,
                          font=font,
                          fill=(int(color[1:3], 16),
                                int(color[3:5], 16),
                                int(color[5:7], 16),
                                int(255 * opacity)))

                # 旋转文字图层
                if text_angle != 0:
                    rot_center = (x + tw // 2, y + th // 2)
                    text_layer = text_layer.rotate(text_angle, center=rot_center, expand=0)

                canvas = Image.alpha_composite(canvas, text_layer)

            # 2. 绘制图片水印
            if has_image_wm:
                wm = self.watermark_image.resize(
                    (int(self.watermark_original_width * wm_scale),
                     int(self.watermark_original_height * wm_scale)),
                    Image.LANCZOS)
                wm = Image.blend(Image.new("RGBA", wm.size, (255, 255, 255, 0)), wm, wm_opacity)

                # 旋转
                if image_angle != 0:
                    wm = wm.rotate(image_angle, expand=1)

                # 位置计算（旋转后的尺寸）
                cx = img.width * wm_pos[0]
                cy = img.height * wm_pos[1]
                margin_x, margin_y = img.width * 0.02, img.height * 0.02

                if wm_pos[0] == 0:
                    cx = margin_x + wm.width / 2
                elif wm_pos[0] == 1:
                    cx = img.width - margin_x - wm.width / 2
                if wm_pos[1] == 0:
                    cy = margin_y + wm.height / 2
                elif wm_pos[1] == 1:
                    cy = img.height - margin_y - wm.height / 2

                x = int(cx - wm.width / 2)
                y = int(cy - wm.height / 2)
                canvas.paste(wm, (x, y), wm)

            # 3. 合成底图
            out = Image.alpha_composite(img, canvas).convert("RGB")
            base_name = os.path.basename(img_path)
            name, _ = os.path.splitext(base_name)
            save_path = os.path.join(export_folder, f"{prefix}{name}{suffix}.{output_format.lower()}")
            out.save(save_path, format=output_format)

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
    
    # def on_watermark_press(self, event):
    #     # 记录鼠标按下时的位置
    #     self.drag_data = (event.x, event.y)

    def on_watermark_press(self, event):
        # ① 先记录起点，否则 on_watermark_move 里没有 drag_data
        self.drag_data = (event.x, event.y)

        # ② 仅做"点中水印"高亮提示，不再提前 return
        click_x, click_y = event.x, event.y
        if self.cur_operate.get() == "text" and hasattr(self, 'text_bbox'):
            x1, y1, x2, y2 = self.text_bbox
            
            print('点击:', (event.x, event.y), '文本区域:', self.text_bbox)
            print(f"点击位置: ({click_x}, {click_y}), 文本水印区域: ({x1}, {y1}, {x2}, {y2})")
            if x1 <= click_x <= x2 and y1 <= click_y <= y2:
                print("已点中文本水印区域")
            else:
                print("未点中文本区域，仍可拖拽")
        elif self.cur_operate.get() == "image" and hasattr(self, 'image_bbox'):
            x1, y1, x2, y2 = self.image_bbox
            if x1 <= click_x <= x2 and y1 <= click_y <= y2:
                print("已点中图片水印区域")
            else:
                print("未点中图片区域，仍可拖拽")

            # 如果没有点中任何水印，默认选文本
            self.selected_watermark = "text"
            print("未点中水印，默认选文本水印")

    def on_watermark_move(self, event):
        if self.drag_data and self.watermarked_image:
            dx = event.x - self.drag_data[0]
            dy = event.y - self.drag_data[1]

            # 只移动当前选中的水印
            if self.cur_operate.get() == "text":
                self.watermark_position = (
                    max(0, min(1, self.watermark_position[0] + dx / self.preview_canvas.winfo_width())),
                    max(0, min(1, self.watermark_position[1] + dy / self.preview_canvas.winfo_height()))
                )
            else:  # 图片水印
                self.image_watermark_pos = (
                    max(0, min(1, self.image_watermark_pos[0] + dx / self.preview_canvas.winfo_width())),
                    max(0, min(1, self.image_watermark_pos[1] + dy / self.preview_canvas.winfo_height()))
                )

            self.preview_watermark()
            self.drag_data = (event.x, event.y)

    def on_watermark_release(self, event):
        # 清除拖拽数据
        self.drag_data = None

    def select_image_watermark(self):
        filetypes = [("图片文件", "*.png;*.jpg;*.jpeg;*.bmp;*.tiff")]
        file_path = filedialog.askopenfilename(title="选择图片水印", filetypes=filetypes)
        if file_path:
            self.image_watermark = Image.open(file_path).convert("RGBA")
            self.preview_watermark()


    def _on_operate_change(self):
        # 切换模式后即时刷新预览（可高亮边框等后续扩展）
        self.preview_watermark()

if __name__ == "__main__":
    root = TkinterDnD.Tk()  
    # 设置样式
    style = ttk.Style()
    style.configure("Custom.TLabelframe", background="#f8fafc", foreground="#1e293b", 
                    font=("Arial", 11, "bold"), relief="groove", borderwidth=2)
    style.configure("Accent.TButton", background="#3b82f6", foreground="white", 
                    font=("Arial", 10, "bold"))
    style.map("Accent.TButton", background=[("active", "#2563eb")])
    style.configure("Export.TButton", background="#8b5cf6", foreground="white", 
                    font=("Arial", 10, "bold"))
    style.map("Export.TButton", background=[("active", "#7c3aed")])
    style.configure("TRadiobutton", background="#f8fafc", foreground="#1e293b")
    
    # 设置按钮样式
    root.option_add("*Button.Font", "Arial 10")
    root.option_add("*Button.Background", "#e2e8f0")
    root.option_add("*Button.Foreground", "#1e293b")
    root.option_add("*Button.Relief", "raised")
    root.option_add("*Button.BorderWidth", 1)
    
    app = WatermarkApp(root)
    root.mainloop()

def main():
    """程序入口函数"""
    root = TkinterDnD.Tk()  
    # 设置样式
    style = ttk.Style()
    style.configure("Custom.TLabelframe", background="#f8fafc", foreground="#1e293b", 
                    font=("Arial", 11, "bold"), relief="groove", borderwidth=2)
    style.configure("Accent.TButton", background="#3b82f6", foreground="white", 
                    font=("Arial", 10, "bold"))
    style.map("Accent.TButton", background=[("active", "#2563eb")])
    style.configure("Export.TButton", background="#8b5cf6", foreground="white", 
                    font=("Arial", 10, "bold"))
    style.map("Export.TButton", background=[("active", "#7c3aed")])
    style.configure("TRadiobutton", background="#f8fafc", foreground="#1e293b")
    
    # 设置按钮样式
    root.option_add("*Button.Font", "Arial 10")
    root.option_add("*Button.Background", "#e2e8f0")
    root.option_add("*Button.Foreground", "#1e293b")
    root.option_add("*Button.Relief", "raised")
    root.option_add("*Button.BorderWidth", 1)
    
    app = WatermarkApp(root)
    root.mainloop()
