from setuptools import setup, find_packages

setup(
    name="modelrouter-sdk",
    version="0.2.0",
    description="Lightweight Python SDK for intelligent, explainable LLM request routing",
    packages=find_packages(),
    install_requires=[
        "httpx>=0.25.0",
        "pydantic>=2.0.0",
    ],
    python_requires=">=3.9",
)
