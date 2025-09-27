self.image_preview = Label(root, text="预览区域", bd=1, relief="sunken")
        self.image_preview.pack()
        # 固定像素尺寸，足够放下 200×200 的缩略图
        self.image_preview.config(width=300, height=300)