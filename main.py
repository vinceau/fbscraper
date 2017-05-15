#!/usr/bin/env python2.7

# -*- coding: utf-8 -*-

import sys
try:
    # allow printing of non-standard characters to stdout
    reload(sys)
    sys.setdefaultencoding("utf8")
except NameError:
    # we're on Python 3 so we already good
    pass

import argparse
import logging

from builtins import input
from getpass import getpass

# local imports
from fbscrape import FBScraper


def main(args):
    output_dir = args.outputdir if args.outputdir else ''
    loginfile = args.loginfile if args.loginfile else 'login.txt'
    infile = args.inputfile if args.inputfile else ''
    fbs = FBScraper(output_dir)

    # run the gui version if there's no --nogui flag
    if not args.nogui:
        # hide the current arguments from kivy
        sys.argv = [sys.argv[0]]
        from gui import FBScraperApp
        return FBScraperApp(fbs, loginfile, infile).run()

    # configure logging level
    logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)
    log = logging.getLogger('fbscraper')

    # not running the gui version
    # attempt to login
    fb_user = ''
    fb_pass = ''
    if loginfile:
        with open(loginfile, 'r') as f:
            lines = f.readlines()
            fb_user = lines[0].strip()
            fb_pass = lines[1].strip()
    else:
        fb_user = input('Enter your Facebook login email: ')
        fb_pass = getpass('Enter your Facebook password:  ')
    if not fbs.login(fb_user, fb_pass):
        sys.exit('Failed to log into Facebook. Check your credentials and try again.')

    # login successful
    if infile:
        with open(infile, 'r') as input_f:
            for line in input_f:
                fbs.scrape(line.strip())
    else:
        log.info('No input file specified. Reading input from stdin.')
        print('Enter the Facebook ID, Username, or URL to scrape followed by the <Enter> key.')
        while True:
            line = sys.stdin.readline().strip()
            if not line:
                break
            fbs.scrape(line)
            print('Scrape complete. Enter another Facebook ID, Username, or URL followed by the <Enter> key.')
        print('Exiting...')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Crawl a bunch of Facebook sites and record the posts.')
    parser.add_argument('--nogui', '-n', dest='nogui', action='store_true', required=False,
                        help='run the program without the graphical user interface')
    parser.add_argument('--input', '-i', dest='inputfile', required=False,
                        help='a file to read a list of Facebook usernames from')
    parser.add_argument('--outputdir', '-o', dest='outputdir', required=False,
                        help='the directory to store the scraped files')
    parser.add_argument('--loginfile', '-l', dest='loginfile', required=False,
                        help='the file to read login credentials from (username/email on the first line, and password on the second line)')
    args = parser.parse_args()
    main(args)
