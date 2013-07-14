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
        'Flask',
        'Flask-Babel',
        'Flask-AutoIndex',
        'Flask-SQLAlchemy',
        'whoosh',
        'backports.lzma'
    ]
    #data_files=[("", ["LICENSE.txt", "README.md", "INSTALL.txt"])]
)
