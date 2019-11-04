from setuptools import setup, find_packages

with open('README.md', 'r') as fh:
    long_description = fh.read()

setup(name='request_generator',
      version='1.0',
      description='Utilities for driving API requests.',
      long_description=long_description,
      long_description_content_type="text/markdown",
      url='https://github.com/EOSIO/auto-request-generator',
      author='EOSIO',
      author_email='automation@block.one',
      license='MIT',
      packages=find_packages(),
      classifiers=[
            "Programming Language :: Python :: 3",
            "License :: OSI Approved :: MIT License",
            "Operating System :: OS Independent",
      ],
      python_requires='>=3.6',
      zip_safe=False)
