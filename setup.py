import setuptools

with open('README.md', 'r', encoding='utf-8') as fh:
    long_description = fh.read()

setuptools.setup(
    name='rse-timetracking',
    version='0.1',
    author='Marijn van Vliet and Jarno Rantaharju',
    #author_email='',
    description='A scraper for our RSE projects on Gitlab',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/AaltoRSE/rse-timetracking',
    packages=setuptools.find_packages(),
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
    install_requires=[
        'ipywidgets',
        'matplotlib',
        'pandas',
        'plotly',
        'python-dateutil',
        'python-gitlab',
        'pytz',
        'requests',
        ],
    entry_points=dict(
        console_scripts=['rse-timetracking=rse_timetracking:main.main'],
    )
)
