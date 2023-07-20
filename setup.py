from setuptools import setup, find_packages


with open('README.rst') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='GPT4Server',
    version='0.1.0',
    description='Python Server for accessing gpt4all from web',
    long_description=readme,
    author='Mabenan',
    author_email='doener123@googelmail.com',
    url='https://github.com/mabenan/gpt4server',
    license=license,
    packages=find_packages(exclude=('tests', 'docs'))
)