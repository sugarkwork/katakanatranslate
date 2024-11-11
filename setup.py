import codecs
import setuptools

with codecs.open('requirements.txt', 'r', encoding='utf-16') as f:
    requirements = f.read().splitlines()

setuptools.setup(
    name="katakanatranslate",
    version="0.1.1",
    install_requires=requirements,
    packages=setuptools.find_packages(),
    description="A simple katakana translator",
    author="sugarkwork",
    python_requires='>=3.10',
)
