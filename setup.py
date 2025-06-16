"""
Setup script for gemini-ask package
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="gemini-ask",
    version="0.0.1",
    author="Ricardo de Azambuja",
    description="Ask questions to Google Gemini from your command line",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ricardodeazambuja/gemini-ask",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Communications :: Chat",
        "Topic :: Internet :: WWW/HTTP :: Browsers",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: System :: Shells",
        "Topic :: Utilities",
    ],
    python_requires=">=3.7",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=6.0",
            "black>=22.0",
            "flake8>=4.0",
            "mypy>=0.900",
        ],
    },
    entry_points={
        "console_scripts": [
            "gemini-ask=gemini_ask.cli:main",
        ],
    },
    keywords="gemini, ai, cli, command-line, chat, automation, google",
    project_urls={
        "Bug Reports": "https://github.com/ricardodeazambuja/gemini-ask/issues",
        "Source": "https://github.com/ricardodeazambuja/gemini-ask",
        "Documentation": "https://github.com/ricardodeazambuja/gemini-ask#readme",
    },
)