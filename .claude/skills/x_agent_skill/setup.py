"""
JoyAgent - Intelligent Analysis Assistant Setup Script
"""

from setuptools import setup, find_packages
import os

# Read the README file
with open("SKILL.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="joyagent-skill",
    version="1.0.0",
    author="JoyAgent Team",
    author_email="team@joyagent.ai",
    description="Intelligent analysis assistant with SOP-driven planning and multi-tool coordination",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/joyagent/joyagent-skill",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=1.0.0",
        ],
        "visualization": [
            "matplotlib>=3.5.0",
            "seaborn>=0.11.0",
            "plotly>=5.0.0",
        ],
        "ml": [
            "scikit-learn>=1.0.0",
            "pandas>=1.3.0",
            "numpy>=1.20.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "xagent=xagent_skill.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "xagent_skill": [
            "prompt/*.yaml",
            "templates/*.j2",
            "examples/*.py",
        ],
    },
    keywords="analysis business-intelligence data-science prompt-engineering sop multi-agent",
    project_urls={
        "Bug Reports": "https://github.com/xagent/xagent-skill/issues",
        "Source": "https://github.com/xagent/xagent-skill",
        "Documentation": "https://github.com/xagent/xagent-skill/blob/main/SKILL.md",
    },
)