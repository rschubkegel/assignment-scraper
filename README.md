# Assignment Scraper

## Description

Authored by [rschubkegel](https://github.com/rschubkegel).

Keeping up with new school assignments can be a pain in the b*tt. This automates the process of checking the assignments pages for new homework.

## Usage

This program requires three JSON files: `credentials.json`, `site-info.json`, and `trello-info.json`. The first two are omitted from the repository for security reasons.

### Tracked Files

The file `trello-info.json` stores the ID of the Trello board that holds assignments and the different lists on that board. While cards are expected to change frequently and labels will change each semester, the board and lists are not likely to change so it is stored in a file for efficiency.

### Untracked Files

This program also expects two untracked files: `credentials.json` and `site-info.json`. The first contains the Trello REST API developer key and token. The second contains a list of school assignment pages from which to parse new assignments.

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
