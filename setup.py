from setuptools import setup, find_packages

setup(
    name="llm_consortium",
    version="0.1.1",
    packages=find_packages(),
    install_requires=[
        "gradio",
        "pydantic",
        "llama-index",
        "openai",
        "streamlit",
        
    ],
    python_requires=">=3.8",
)