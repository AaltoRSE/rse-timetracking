# RSE Time Tracking System


The Aalto RSE team tracks their time and Key Performance Indicators
(KPIs) in a Gitlab repository.  Gitlab provides some tracking support
(time estimate and time spent), but we need more than just that.  In
addition, when using lots of labels to classify projects, some extra
structure in parsing these is very helpful.

This package downloads issues and issue metadata from a Gitlab
repository and assists in making reports.  Many of the actual reports
are in Jupyter Notebooks, which are currently not included here (right
now they are unfortunately tied up with internal data - we need to fix
this).

This package contains the command line utility `rse_timetracking` with various subcommands.  The general process is first run a `scrape` subcommand to download data and store it in a csv/pickle file, and then other commands will process this into reports.

This project is probably specific to Aalto RSE right now, but we would
be happy to make it more general (if we can find a way to make it
general enough).



## General procedures of tracking time

In general, when a project is started, create a new issue in the
rse-projects repository (this is a private repo).  This is usually
done during the "introductory meeting", which rkdarst will usually
have with each new project.  Use one of the issue templates to help
guide you through some of the questions you may want to discuss.  Add
any relevant labels.  Set an initial time estimate with `/estimate`.
Each time you work on the project, record your time using `/spend`.

Then, during our next weekly meeting, we will discuss any new projects
and schedule them among us.

When a project is done, have a follow-up meeting and use the
reportable commands to make a note of what kind of projects were
supported.



## Issue syntax / GitLab Commands

### Commands

The following Gitlab commands are natively processed by GitLab:

* Use these within the issue as a comment, to control the time
  allocation.

* `/estimate TIME-RECORD [YYYY-MM-DD]` - estimate total time a project
  make take.  Used as soon as possible at beginning of a project, can
  always be updated

* `/spend TIME-RECORD [YYYY-MM-DD]` - **announce that you have spent a
  certain amount of time on the project**

* `TIME-RECORD` has the form `XXmoYYwZZdUUhVVm` for `XX` month, `YY`
  weeks `ZZ` days `UU` hours and `VV` minutes.
* Time units: Months (`mo`), Weeks (`w`), Days (`d`), Hours (`h`),
  Minutes (`m`). Default conversion rates are 1mo = 4w, 1w = 5d, and
  1d = 8h.


The following commands are *not* GitLab commands, but are entered as
only text comments.  a separate script downloads the text and
processes them.  Commands must start after a `\n`.

The following commands are used for basic metadata, and asked at the
start of a project:

* `/contacts EMAIL[, EMAIL [...]]` - who we usually communicate with.
  Each project should have a contact, and these should be people who
  are not surprised to get email about it at some time in the future.

* `/supervisor EMAIL[, EMAIL [...]]` - PI(s) responsible for research
  (not usually contacted).

* `/summary TEXT` - a free-form summary of the project, used for
  reports.  Normally a sentence or two in the imperative form (a lot
  like a git commit message).  It should focus on the high-level
  impact, not the low-level technical details.  Example: "A researcher
  needed to acquire data from a web API.  We created a tool to do this
  and set up an automatic workflow to keep data coming in during the
  two-year project."


The following are used for reportables, and normally are asked and
entered only at the end of a project in some sort of wrap-up
discussion:

* `/timesaved TIME-RECORD [YYYY-MM-DD]` - **estimate total researcher
  time saved**.

  * TIME-RECORD is like `5h`. Time units: Months (`mo`), Weeks (`w`),
    Days (`d`), Hours (`h`), Minutes (`m`). Default conversion rates
    are 1mo = 4w, 1w = 5d, and 1d = 8h.

* `/projects INT` - number of research projects supported by this RSE work
* `/publications INT` - number of publications supported by this RSE work
* `/software INT` - number of software packages supported by this RSE work
* `/datasets INT` - datasets supported by this RSE work
* `/outputs INT` - number of open science outputs produced other than the categories above


### Labels

There are various labels which we can add:

Status:
* `Status::0-Lead` - someone had an idea that this project might be available.  Maybe the final customer hasn't even been talked to yet
* `Status::0-WaitingForGrant` - RSE services needed if grant is funded (usually includes funding via the grant)
* `Status::1-Consulting` - Not actively worked on, but the customers drop by occassionally and ask us questions.  Does not require ongoing attention from us
* `Status::1-Waiting` - We are waiting for the customer to become ready for us to start.  Maybe the customer will contact us when they are ready.  Maybe we have a "follow-up date" at which time we should contact them again.
* `Status::2-Queued` - We are waiting for time, then we will start this project.
* `Status::3-InProgress` - We are working on it
* `Status::3-NeedsReview` - Needs to be checked internally
* `Status::4-Review` - Being checked by the customer
* `Status::5-Reporting` - Project is done, but all of the stats (timesaved, outputs, etc). are not there yet.
* `Status::6-Done` - Done, don't need to think about it anymore.
* `Status::7-Cancelled` - We decided (along with the customer) to not do this project
* `Status::8-Maintenance` - Project is "done" but the customer will keep coming back to us for support or updates as needed.

Funding:
* `Funding::Unit` - Funding from basic RSE service funding, coming from the different member units.
* `Funding::Project` - The project is paying for this service itself
* `Funding::ProjectOffers` - The project would be willing to pay for the service, but isn't doing so for practical reasons (for example, the project is too small for finance to want to deal with it)
* `Funding::ASC` - similar to `Unit` but it's more of a ASC-internal project, so you could say that ASC is the customer itself.

Task:
* Task labels indicate the type of work in the project.  Multi-select,
  every project should have every one of these relevant labels
  attached to it.  Examples include `Task:SwDev`, `Task:Workflow`,
  `Task:WebDev`.

Unit:
* From what department are the customers?  Select one, `Unit::NAME`.

Special use:
* `a_Discuss` - should be discussed at the next meeting
* `a_NoReport` - Don't include this project in reports.



## Installation

Install with: `python setup.py install`



## Usage

Use the `rse_timetracking` command to scrape the Gitlab repo:

```bash
$ rse_timetracking scrape [--v2]
```

This produces a file called `report.csv` (this can be changed with the
`-o` option, and `--v2` saves it in a pickle format).  Then, an HTML
report can be build with:

```bash
$ rse_timetracking report
```

This reads in the `report.csv` file (this can be changed with the `-i` option) and produces a file called `report.html` (this can be changed with the `-o` option).

Or, the `scrape2.dataframes` and `scrape2.combine_dataframes`
functions can be used to get Pandas dataframes out of the pickle file.



## Development

To develop on this package, it's recommended to install it as: `python setup.py develop`. This will install the scripts in your path, but link them to the repo dir and not copy everything into your `site-packages` dir.
