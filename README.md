# Important Announcement

This project is no longer maintained and has been archived. Feel free to fork this project and update the codebase as your heart desires.

-----------------------------------------------------

# Introduction

This program is an extensible webscraper for Facebook that can scrape entire profiles of users, including: posts, photos, albums, friends list, groups, likes, and their about page (profile information).

Since this is a hand-crafted webscraper, whenever Facebook updates their source code, there is a high possibility that it will break this webscraper. That means that this webscraper will need to be actively maintained and updated whenever Facebook modifies their source code. `custom.py` is the file that contains all the CSS and XPATH selectors. These are the selectors that must be updated. The future maintainer should be well versed in CSS and XPATH before familiarising themselves with the fbscrape.crawler source code. Once they have a good understanding, it should not be too hard to examine Facebook's source code to update the selectors in custom.py appropriately.


# Installation
Open a Terminal shell and type in `sudo ./setup.sh`. Follow the prompts to install all dependencies. You may need to hit 'Y' a couple of times to proceed with the install.


# Running the Program
Open a Terminal shell and type in the command `python2.7 main.py`. If a whole bunch of errors come up try running it in `sudo` mode, i.e. running the command `sudo python2.7 main.py`. It shouldn't need `sudo` access but sometimes the GUI package Kivy complains without it.


# Important Information

## Python Version Compatibility
Although effort has been made to make the Python code as version-agnostic as possible, the Kivy graphics library's clipboard functionality is currently broken on Python 3, and currently only works with Python 2. As a result, even though the fbscrape module should theoretically be Python 3 compatible, the majority of the testing done has been done in Python 2 only.

## Scrape Delay
By default, whenever a page load is requested, the scraper will wait until that page is fully loaded. However, fbscrape.crawler will sometimes need to execute Javascript to load content such as scrolling to the bottom of the page for Facebook's infinite scroll, or clicking on the different sections in a profile's About page. As of writing, there is no sure-fire way of knowing exactly when this dynamically loaded content has completely finished loading. Thus, whenever a page is loaded normally by the scraper, it will time how long it took, and when loading dynamic content will wait an average of how long pages have taken to load thus far. This is an imperfect solution since sometimes pages take a long time to load but dynamic content might load quickly so there's a lot of time wasted, or pages might load quickly but for some reason the dynamic content is taking a long time to load and thus the new content is missed/skipped by the scraper since it thought that the content was already loaded. Feel free to suggest better solutions.

## Facebook Targets
Facebook has two main methods of identifying users -- a unique ID number (a roughly 16 digit number), and usernames (a combination of letters, numbers, and/or full-stops (periods). This scraper can scrape users using either method of identification.


# Inner Workings
The program is composed of a backend module called fbscrape and a frontend main.py file. It uses an Model-view-controller (MVC) model with the fbscrape module as the model, the `gui/*.py` files as the controllers, and the `gui/*.kv` files as the view. 

The fbscrape.crawler is responsible for opening/loading/processing through webpages whilst the fbscrape.scraper extends this by storing the information crawled by the crawler and saving it onto the local hard disk. The storing component is generally handled by record.py.


# Known Issues

## Not All Posts included in Current Year Scraping
At the time of writing, Facebook separates posts from the current year into "Recents" and "Current Year". The posts split into recents are placed in a different container compared to that of the current year and as a result might not be included. A planned fix is to allow stopping the scraper after a certain date has been reached. For example, adding an option to scrape from the latest post up until a certain year, then proceeding to do a scrape range from the past up until that year would allow all posts to be scraped without duplicates. This fix is not ready yet so for the time being, avoid using the year ranges with the end year of the current year.

## Unicode Problems
The GUI version of the scraping program can not display certain unicode. This is a limitation with the Kivy graphics library. It could have been solved by using a completely different graphics library but Kivy was the least painful to use. What this means to the end user is that foreign names not in English are often replaced with question marks (?) in the Python GUI. Using a terminal/shell with a larger unicode support will solve this problem since the log displayed by the GUI window reflects the log in the terminal anyway.

## Occasional Slowness
When running the search (for Facebook targets) several times can eventually cause the search results to populate really slowly. I believe this is due to previously running threads not terminating cleanly for whatever reason. I am unsure how to solve this. My suggestion is to close and restart the program once every now and then.

## GUI Log Limit
The GUI log has been limited to displaying the last 30 messages. This was done to avoid an issue where the Kivy Label Widget disappears once the label text has reached a certain size. It is unconfirmed whether or not exceeding a text character limit inside a Label Widget is the cause of this issue but limiting the messages to 30 seems to fix it.

# Changelog

## 1.7 f36d4fb2 (17 July 2017)
* Split Photos option into separate Timeline Photos and Albums option 
* Add check-ins scraping
* Fix skipping of groups with emojis in their name
* Fix occasional returning on un-finished page load
* Better handle translated posts
* Allow post scraping by year
* Make settings persistent upon restart

## 1.6 b27ecf37 (26 June 2017)
* Add event guest list scraping
* Fix broken photos selector
* Fix broken friends selector

## 1.5 a5b4359c (22 May 2017)
* Fix crash when clicking "See More" in externally shared Notes

## 1.4 68b6dc55 (15 May 2017)
* Fix duplicated log message issue
* GUI mode is enabled by default when executing `python main.py`

## 1.3 e106bf4a (2 May 2017)
* Added option for constant delay
* Fix issues with threads not terminating properly (hopefully)

## 1.2 dcf04096 (1 May 2017)
* Added load targets list from file
* Targets can now be searched for using in-built target search

## 1.1 d911941d (27 March 2017)
* Login button is now disabled while logging in
* Fixed randomly appearing red dots on click
* Scrape complete dialog box now appears on scrape completion
* Scrape progress is now displayed during scrape
* Scrape can now be paused and unpaused while running

## 1.0 72cc031d (6 March 2017)
* Initial release


# License

This project is licensed under the MIT License. See `LICENSE.txt` for more details.


# Author

Vince Au <vinceau09@gmail.com>
