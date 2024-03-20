from setuptools import setup, find_packages

setup(
    name='vino',
    version='0.0.2',
    packages=find_packages(),
    install_requires=[
        'pyzmq',
    ],
    url='https://github.com/DrCelesteTurquoise/Celeste.git',
    author='vino',
    author_email='your_email@example.com',
    description='VIONDDDD',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
)
