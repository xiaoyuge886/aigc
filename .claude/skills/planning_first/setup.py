"""
Planning First Skill Setup Script
"""

from setuptools import setup, find_packages

with open("SKILL.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="planning-first-skill",
    version="3.0.0",
    author="AIGC Team",
    description="Planning First - 强制先规划后执行的思考指导框架",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/aigc/planning-first-skill",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.8",
    install_requires=[],
    package_data={
        "planning_first": [
            "prompts/*.md",
        ],
    },
    keywords="planning react coordination thinking claude-agent",
    project_urls={
        "Source": "https://github.com/aigc/planning-first-skill",
    },
)
