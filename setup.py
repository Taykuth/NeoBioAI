"""
Neo-Dock — setup.py
Projeyi pip ile editable kurulum yapar.
  pip install -e .
Bu sayede 'from backend.xxx import ...' ve 'from ml.xxx import ...'
her yerden çalışır.
"""
from setuptools import setup, find_packages

setup(
    name="neodock",
    version="1.0.0",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "fastapi>=0.110",
        "uvicorn[standard]>=0.27",
        "python-dotenv>=1.0",
        "pydantic>=2.0",
        "numpy>=1.24",
    ],
)
