from setuptools import setup, find_packages

setup(
    name="detection",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        'fastapi',
        'uvicorn[standard]',
        'opencv-python-headless',
        'numpy',
        'pydantic',
        'kafka-python',
        'ultralytics',
    ],
    python_requires='>=3.8',
)
