"""Setup file...."""
from setuptools import setup

setup(
    name="pyyaledoorman",
    version="1.0.0",
    description="Python Yale Doorman interface",
    author="Espen Fjellvær Olsen",
    author_email="espen@mrfjo.org",
    license="MIT",
    url="https://github.com/espenfjo/pyyaledoorman",
    python_requires=">=3.9",
    packages=["pyyaledoorman"],
    keywords=["homeautomation", "yaledoorman"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "Topic :: Home Automation",
    ],
    install_requires=["aiohttp", "aioresponses"],
    scripts=[],
)
