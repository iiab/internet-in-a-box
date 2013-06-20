#!/usr/bin/env python
# -*- coding: utf-8 -*- #

AUTHOR = u'Braddock Gaskill'
SITENAME = u'Internet-in-a-Box'
SITESUBTITLE = u"Sharing the world's Free information"
SITEURL = ''
GITHUB_URL = 'https://github.com/braddockcg/internet-in-a-box'

# Use relative URLS when generating locally
RELATIVE_URLS = True

TIMEZONE = 'US/Pacific'

DEFAULT_LANG = u'en'

DEFAULT_PAGINATION = 0

# Custom theme based on Github Pages slate theme
THEME = "theme/bootlex"

DISPLAY_PAGES_ON_MENU = False
INDEX_SAVE_AS = "news.html"
INDEX_PAGE_TITLE = "News"

MENUITEMS = ( ('Home', '/'),
              ('News', '/news.html'),
              ('About', '/pages/about.html'),
            )

FILES_TO_COPY = (("CNAME","CNAME"), ("201304_SGVLUG_Presentation.pdf", "201304_SGVLUG_Presentation.pdf"))
