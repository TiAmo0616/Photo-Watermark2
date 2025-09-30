from setuptools import setup, find_packages
import os

# 读取README.md作为长描述
def read_long_description():
    here = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(here, "README.md"), encoding="utf-8") as fh:
        long_description = fh.read()
    return long_description

setup(
    name="photo-watermark2",
    version="2.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="一款运行于 Windows 平台的水印文件本地应用",
    long_description=read_long_description(),
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/Photo-Watermark2",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.7",
    install_requires=[
        "Pillow>=9.0.0",
        "matplotlib>=3.5.0",
        "tkinterdnd2>=0.3.0",
    ],
    entry_points={
        "console_scripts": [
            "photo-watermark=code.watermark_app:main",
        ],
    },
    package_data={
        "": ["*.md", "LICENSE"],
    },
    include_package_data=True,
)