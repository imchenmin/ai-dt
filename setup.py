from setuptools import setup, find_packages

try:
    with open("README.md", "r", encoding="utf-8") as fh:
        long_description = fh.read()
except FileNotFoundError:
    long_description = "AI-Driven Test Generator for C/C++ code"

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="ai_dt",
    version="1.0.3",
    author="AI-DT Team",
    author_email="",
    description="AI-Driven Test Generator for C/C++ code",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-repo/ai-dt",
    packages=['ai_dt', 'ai_dt.analyzer', 'ai_dt.llm', 'ai_dt.parser', 'ai_dt.test_generation', 'ai_dt.utils'],
    package_dir={'ai_dt': 'src'},
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
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "ai-dt=ai_dt.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "src": ["config/*.yaml", "config/*.json"],
    },
)