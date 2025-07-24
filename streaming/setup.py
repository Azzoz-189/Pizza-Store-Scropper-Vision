from setuptools import setup, find_packages

setup(
    name="streaming",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        'fastapi',
        'uvicorn[standard]',
        'kafka-python',
        'opencv-python-headless',
        'numpy',
        'pydantic',
    ],
    python_requires='>=3.8',
)
