Dal Course Scraper
==================

This scraper builds an sqlite database of Dalhousie courses by scraping
the online [course calendar](https://dalonline.dal.ca/PROD/fysktime.P_DisplaySchedule).

Usage
-----
Written in Python 2.7.
Depends on [Beautiful Soup 4](http://www.crummy.com/software/BeautifulSoup/) and [Requests](http://docs.python-requests.org/en/latest/)

Output:
error.log : a list of all the rows that were not added to the database
courses.db : an sqlite database with all the courses and classes.
