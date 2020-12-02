RSE Time Tracking System
========================

The Aalto RSE team tracks their time and Key Performance Indicators (KPIs) in a Gitlab repository.
This package contains the command line utility `rse_timetracking` to script this repository and write the statistics to a CSV file.


Installation
------------

Install with: `python setup.py install`


Usage
-----
Use the `rse_timetracking` command to scrape the Gitlab repo. It needs the year to scrape as a command line argument, for example:

```bash
$ rse_timetracking 2021 -o report_2021.csv
```

See `rse_timetracking --help` for all options.


Development
-----------

To develop on this package, it's recommended to install it as: `python setup.py develop`. This will install the scripts in your path, but link them to the repo dir and not copy everything into your `site-packages` dir.
