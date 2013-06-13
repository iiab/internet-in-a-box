from setuptools import setup

setup(
    name='Internet-in-a-Box',
    version='0.2',
    author="Braddock Gaskill",
    author_email="braddock@braddock.com",
    license="LICENSE.txt",
    long_description="Sharing the world's Free information",
    packages=['iiab'],
    scripts=['iiab-server', 'iiab.wsgi'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'Flask',
        'Flask-Babel',
        'Flask-AutoIndex',
        'Flask-SQLAlchemy',
        'whoosh',
        'pyliblzma'
    ]
)
