# Assignment Scraper

## Description

Authored by [rschubkegel](https://github.com/rschubkegel).

Keeping up with new school assignments can be a pain in the b\*tt. This automates the process of checking the assignments pages for new homework.

_Disclaimer: I know this is not programmed in the best way; i.e. there is no assignment chaching, user authentication should use OAuth, etc. This scraper is for personal use and not expected to be professional quality._

## Usage

First, activate the virtual environment and update dependencies.

```
. .venv/Scripts/activate
pip install -r requirements.txt
```

Then you can run the program with the folling command:

```
python main.py [<credentials-info-path>] [<site-info-path>] [<trello-info-path>]
```

The program requires three JSON files: `credentials.json`, `site-info.json`, and `trello-info.json`. If one or more of the paths are not given as program arguments, it is expected that they exist in the working directory. If they do not, the program will exit with error code `1`.

`credentials.json` and `site-info.json` are omitted from the repository for security, so you must add them manually. The file contents are described below.

### Tracked Files

The file `trello-info.json` stores the ID of the Trello board that holds assignments and the different lists on that board. While cards are expected to change frequently and labels will change each semester, the board and lists are not likely to change so it is stored in a file for efficiency.

### Untracked Files

This program also expects two untracked files: `credentials.json` and `site-info.json`. The first contains the REST API developer key and token for Trello and Canvas LMS. The second contains a list of school assignment pages from which to parse new assignments.

#### Format of `credentials.json`

```json
{
    "trello": {
        "key": "0123456789",
        "token": "01234567890123456789"
    },
    "canvas": {
        "token": "01234567890123456789"
    }
}
```

#### Format of `site-info.json`

```json
{
  "CSIS 420": {
    "title": "Computer Class",
    "url": "http://{professor}.cs.georgefox.edu/courses/{course-name}/assignments/",
    "headers": {
      "request-info": "Omitted for privacy; see Generating Request Headers."
    }
  }
}
```

### Generating Request Headers

To generate the proper HTTP request headers, log in to the assignments page once, then copy the HTTP request as a cURL command via the web browser's inspector. Convert the cURL command to the proper request using [this tool](https://curl.trillworks.com/). Paste into `site-info.json`.