from setuptools import setup

setup(
    name='Internet-in-a-Box',
    version='0.3.8',
    author="Braddock Gaskill",
    author_email="braddock@braddock.com",
    license="2-clause BSD license",
    description="Sharing the world's Free information",
    long_description=open('README.md').read(),
    url="http://internet-in-a-box.org",
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
    #data_files=[("", ["LICENSE.txt", "README.md", "INSTALL.txt"])]
)
