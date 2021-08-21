# Assignment Scraper

## Description

Authored by [rschubkegel](https://github.com/rschubkegel).

Keeping up with new school assignments can be a pain in the b*tt. This automates the process of checking the assignments pages for new homework.

## Dependencies

Imports:
- [beautifulsoup4](https://www.crummy.com/software/BeautifulSoup/)
- [requests](https://docs.python-requests.org/en/master/index.html)
- [re](https://docs.python.org/3/library/re.html)
- [json](https://docs.python.org/3/library/json.html)
- [getpass](https://docs.python.org/3/library/getpass.html)
- [sys](https://docs.python.org/3/library/sys.html)
- [datetime](https://docs.python.org/3/library/datetime.html)

## Usage

### Untracked Files

This program expects two files: `credentials.json` and `site-info.json`. A filepath to `credentials.json` and `site-info.json` may be given as command-line arguments, otherwise they will be searched for in the local diretory. If no arguments are given and `credentials.json` is not found in the local directory, the program will manually ask for a Trello key and token to interact with the REST API. If no arguments are given and `site-info.json` is not found in the local directory, the program will terminate.

### Format of `credentials.json`

```json
{
    "key": "0123456789",
    "token": "01234567890123456789"
}
```

### Format of `site-info.json`

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
