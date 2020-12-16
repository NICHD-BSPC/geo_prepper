import os
import setuptools

long_description = """
Prepare data for NCBI GEO submission
"""
requirements = open(os.path.join(os.path.dirname(__file__), 'requirements.txt')).readlines()

setuptools.setup(
    name="geo-prepper",
    version="0.0.1",
    author="Apratim Mitra",
    author_email="apratim.mitra@nih.gov",
    description=long_description,
    long_description=long_description,
    long_description_content_type="text/plain",
    license='GNU GPLv3',
    url="http://github.com/NICHD-BSPC/geo-prepper",
    packages=['geo-prepper'],
    package_dir={'geo-prepper': 'geo-prepper'},
    install_requires=requirements,
    classifiers=[
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
    ],
)
