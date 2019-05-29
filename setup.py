from os import path
from setuptools import setup, find_packages

_here = path.dirname(path.abspath(__file__))

setup(
    name='multisocketServer',
    description='TCP/Websocket bridge with JSON message routing and reconnecting clients',
    version='0.0.1',
    #package_dir={'': 'client/python'},
    packages=find_packages(
        #'client/python',
        exclude=["*.tests", "*.tests.*", "tests.*", "tests"],
    ),
    include_package_data=True,
    long_description=open(path.join(_here, 'README.md')).read(),
    install_requires=[
    ],
    url='https://github.com/superLimitBreak/multisocketServer',
    author='Allan Callaghan',
    author_email='calaldees@gmail.com',
    license='GPL3',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GPL3 License',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    keywords=[
    ],
)
