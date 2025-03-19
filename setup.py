from setuptools import setup, find_packages

setup(
    name="llm_consortium",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "gradio",
        "pydantic",
        "llama-index",
        "openai",
    ],
    python_requires=">=3.8",
)