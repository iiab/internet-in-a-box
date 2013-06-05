from setuptools import setup

setup(
    name='Internet-in-a-Box',
    version='0.1',
    author="Braddock Gaskill",
    author_email="braddock@braddock.com",
    long_description=__doc__,
    packages=['iiab'],
    scripts=['run.py', 'iiab.wsgi'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'Flask',
    ]
)
