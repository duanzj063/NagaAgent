#!/usr/bin/env python3
"""
Live2D模块安装配置
"""

from setuptools import setup, find_packages

setup(
    name="live2d-naga",
    version="1.0.0",
    description="Live2D数字人集成模块 for NagaAgent",
    author="NagaAgent Team",
    packages=find_packages(),
    install_requires=[
        "numpy",
        "aiohttp",
        "pydantic",
        "pyopengl",
        "pyqt5",
    ],
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)