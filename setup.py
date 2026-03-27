from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="feishu-agent-send",
    version="1.1.0",
    author="OpenClaw Team",
    author_email="",
    description="飞书Agent通信工具 - 支持多Agent通过飞书通道通信",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/openclaw/feishu-agent-send",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[],
    entry_points={
        "console_scripts": [
            "feishu-agent-send=feishu_agent_send:main",
        ],
    },
)
