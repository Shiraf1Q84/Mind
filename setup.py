# setup.py
from setuptools import setup, find_packages

setup(
    name='mindsearch_streamlit',
    version='0.1.0',
    description='MindSearch Streamlit App',
    packages=find_packages(),
    install_requires=[
        'lagent',
        'mindsearch',
        'streamlit',
        'termcolor',
    ],
)