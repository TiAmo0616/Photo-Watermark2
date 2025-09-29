# 贡献指南

感谢您对水印文件本地应用项目的关注！我们欢迎任何形式的贡献，包括但不限于功能开发、bug修复、文档完善等。

## 如何贡献

### 报告Bug

如果您在使用过程中发现任何问题，请通过GitHub Issues提交bug报告。请包含以下信息：

1. 您使用的操作系统版本
2. 您使用的Python版本（如果是从源码运行）
3. 详细的错误描述和重现步骤
4. 如果可能，请提供截图或错误日志

### 提交功能请求

如果您有好的想法或功能建议，请通过GitHub Issues提交功能请求。请详细描述：

1. 您希望实现的功能
2. 该功能的使用场景
3. 如果可能，提供界面设计草图或流程说明

### 提交代码

如果您希望提交代码贡献，请遵循以下步骤：

1. Fork本项目
2. 创建您的功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交您的更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启一个Pull Request

### 代码规范

- 遵循PEP 8代码规范
- 添加必要的注释和文档字符串
- 确保代码的可读性和可维护性
- 在提交前进行充分测试

## 开发环境设置

1. 克隆项目到本地
2. 安装依赖：`pip install -r requirements.txt`
3. 运行应用：`python code/watermark_app.py`

## 代码结构

- `code/` - 主要应用代码
- `README.md` - 项目说明文档
- `requirements.txt` - 依赖列表
- `setup.py` - 安装和打包配置

## 测试

在提交代码前，请确保：

1. 应用能够正常启动
2. 所有现有功能正常工作
3. 新增功能按预期工作

## 提交信息规范

请遵循Conventional Commits规范：

- `feat:` 新功能
- `fix:` 修复bug
- `docs:` 文档更新
- `style:` 代码格式调整（不影响代码运行）
- `refactor:` 代码重构
- `test:` 测试相关
- `chore:` 构建过程或辅助工具的变动

示例：
```
feat: 添加图片旋转功能
- 在文本水印中添加旋转角度调节
- 在图片水印中添加旋转角度调节
- 更新预览功能以支持旋转显示
```

感谢您的贡献！