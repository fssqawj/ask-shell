#!/usr/bin/env python3
"""Setup script for alpha-bot"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="alphabot-ai",
    version="0.4.0",
    author="fssqawj",
    author_email="fssqawj@163.com",
    description="用自然语言操控你的终端 - 让 AI 帮你生成并执行 Shell 命令",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/fssqawj/alpha-bot",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Shells",
    ],
    python_requires=">=3.7",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "alpha-bot=alpha_bot.cli:main",
            "ask=alpha_bot.cli:main",
        ],
    },
)
