from setuptools import setup

setup(name='request_generator',
      version='1.0',
      description='Utilities for driving API requests.',
      url='https://github.com/EOSIO/auto-request-generator',
      author='EOSIO',
      author_email='automation@block.one',
      license='MIT',
      packages=['src.request_generator', 'src.benchmarks'],
      zip_safe=False)
