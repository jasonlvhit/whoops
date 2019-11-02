from setuptools import setup

with open("README.rst") as f:
    long_description = f.read()

version = "0.0.1"

setup(
    name="whoops",
    version=version,
    packages=["whoops", "whoops.wsgilib", "whoops.httplib"],
    author="jasonlvhit",
    author_email="jasonlvhit@gmail.com",
    description="whoops is a lightweight, asynchronous, event-driven network programming snippets(maybe framework) in Python",
    classifiers=[
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "Operating System :: Linux",
        "Programming Language :: Python",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    long_description=long_description,
)
