# -*- coding: utf-8 -*-

import sys
try:
    #allow printing of non-standard characters to stdout
    reload(sys)
    sys.setdefaultencoding("utf8")
except NameError:
    #we're on Python 3 so we already good
    pass

import argparse
import logging as log

from builtins import input
from getpass import getpass

#local imports
from model import FBScraper


def main():
    #configure logging level
    log.basicConfig(format='%(levelname)s:%(message)s', level=log.INFO)

    parser = argparse.ArgumentParser(description='Crawl a bunch of Facebook sites and record the posts.')
    parser.add_argument('--input', '-i', dest='inputfile', required=False,
                        help='a file to read a list of Facebook usernames from')
    parser.add_argument('--outputdir', '-o', dest='outputdir', required=False,
                        help='the directory to store the scraped files')
    parser.add_argument('--loginfile', '-l', dest='loginfile', required=False,
                        help='the file to read login credentials from (username/email on the first line, and password on the second line)')
    args = parser.parse_args()
    output_dir = args.outputdir if args.outputdir else ''
    fbs = FBScraper(output_dir)

    fb_user = ''
    fb_pass = ''

    #attempt to login
    if args.loginfile:
        with open(args.loginfile, 'r') as f:
            lines = f.readlines()
            fb_user = lines[0].strip()
            fb_pass = lines[1].strip()
    else:
        fb_user = input('Enter your Facebook login email: ')
        fb_pass = getpass('Enter your Facebook password:  ')
    if not fbs.login(fb_user, fb_pass):
        sys.exit('Failed to log into Facebook. Check your credentials and try again.')

    #login successful
    if args.inputfile:
        with open(args.inputfile, 'r') as input_f:
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
    main()
