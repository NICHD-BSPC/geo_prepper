import setuptools

long_description = """
Prepare data for NCBI GEO submission
"""

setuptools.setup(
    name="geo-prepper",
    version="0.0.1",
    author="Apratim Mitra",
    author_email="apratim.mitra@nih.gov",
    description=long_description,
    url="http://github.com/NICHD-BSPC/geo-prepper",
    packages=['geo-prepper'],
    package_dir={'geo-prepper': 'geo-prepper'},
    install_requires=[i.strip() for i in open('requirements.txt') if not i.startswith('#')],
    classifiers=[
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
    ],
)
