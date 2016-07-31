import os
from setuptools import setup, find_packages

requires = ['supervisor >= 3.0.0']

here = os.path.abspath(os.path.dirname(__file__))
version_txt = os.path.join(here, 'supermon/version.txt')
version = open(version_txt).read().strip()

dist = setup(
    name='supermon',
    version=version,
    license='BSD-derived (http://www.repoze.org/LICENSE.txt)',
    url='https://github.com/chicagofire/supermon',
    description='A set up supervisor utilities',
    author='Jeremy Mayes',
    author_email='jeremy.mayes@gmail.com',
    packages=find_packages(),
    install_requires=requires,
    include_package_data=True,
    zip_safe=False,
    entry_points = """\
        [console_scripts]
        supervisor_cron = supermon.cron:main
        """
)

