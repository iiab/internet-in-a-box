from setuptools import setup
import iiab

setup(
    name='Internet-in-a-Box',
    version=iiab.__version__,
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
        'Flask >= 0.10',
        'Flask-Babel >= 0.8',
        'Flask-AutoIndex',
        'Flask-SQLAlchemy',
        'SQLAlchemy >= 0.8.2',
        'whoosh >= 2.4.1',
        'backports.lzma >= 0.0.2'
    ]
    #data_files=[("", ["LICENSE.txt", "README.md", "INSTALL.txt"])]
)
