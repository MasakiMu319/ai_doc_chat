from enum import StrEnum


class WEB_CONNECTOR_TYPE(StrEnum):
    # Given a base site, index everything that path
    RECURSIVE = "recursive"
    # Given a base site, index only the given path
    SINGLE = "single"
    # Given a sitemap.xml, parse all the pages in it
    SITEMAP = "sitemap"
    # Given a file upload where the file is a list of URLs, parse all the URLs provided
    UPLOAD = "upload"
