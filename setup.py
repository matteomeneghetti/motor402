from setuptools import setup, find_packages
from version import __version__
with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="motor402",
    version=__version__,
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=["canopen>=2.0.0"],
    python_requires='>=3.6',
    url="",
    license="MIT",
    author="Matteo Meneghetti && Noè Murr",
    author_email="matteo@meneghetti.dev",
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3'
    ]
)
