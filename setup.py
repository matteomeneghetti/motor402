from setuptools import setup
with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="motor402",
    version="0.1.0",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=["motor402"],
    install_requires=["canopen>=2.0.0"],
    python_requires='>=3.6',
    url="",
    license="MIT",
    author="Matteo Meneghetti && Noè Murr",
    author_email="matteo@meneghetti.dev"
)
