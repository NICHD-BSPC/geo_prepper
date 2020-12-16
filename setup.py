import os
import setuptools

requirements = open(os.path.join(os.path.dirname(__file__), 'requirements.txt')).readlines()

setuptools.setup(
    name="geo_prepper",
    version="0.0.4",
    author="Apratim Mitra",
    author_email="apratim.mitra@nih.gov",
    description="GEO submission prepper",
    description_content_type="text/plain",
    long_description="Tool to prepare data for NCBI GEO submission",
    long_description_content_type="text/plain",
    license='GNU GPLv3',
    url="http://github.com/NICHD-BSPC/geo_prepper",
    packages=['geo_prepper'],
    package_dir={'geo_prepper': 'geo_prepper'},
    install_requires=requirements,
    classifiers=[
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
    ],
    scripts=[
        "scripts/geo_prepper"
    ],
)
