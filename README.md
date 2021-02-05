RSE Time Tracking System
========================

The Aalto RSE team tracks their time and Key Performance Indicators (KPIs) in a Gitlab repository.
This package contains the command line utility `rse_timetracking` to scrape this repository, write the statistics to a CSV file and produce a nice HTML report.


Installation
------------

Install with: `python setup.py install`


Usage
-----
Use the `rse_timetracking` command to scrape the Gitlab repo:

```bash
$ rse_timetracking scrape
```

This produces a file called `report.csv` (this can be changed with the `-o` option).
Then, an HTML report can be build with:

```bash
$ rse_timetracking report
```

This reads in the `report.csv` file (this can be changed with the `-i` option) and produces a file called `report.html` (this can be changed with the `-o` option).


Development
-----------

To develop on this package, it's recommended to install it as: `python setup.py develop`. This will install the scripts in your path, but link them to the repo dir and not copy everything into your `site-packages` dir.
