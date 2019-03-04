from distutils.core import setup

setup(
    name='backportbot',
    packages=[],
    version='0.1.0',
    description='backport pull requests in a target repository',
    author='redshiftzero',
    license='GPLv3',
    author_email='jen@redshiftzero.com',
    url='https://github.com/redshiftzero/backportbot',
    keywords=['backport', 'release', 'maintenance', ],
    classifiers=[
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Software Development',
    ],
    entry_points = {
        'console_scripts': ['backport-bot=backportbot.cli:main'],
    }
)