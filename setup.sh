#!/usr/bin/env bash

#make sure we are running as root
if [ "$EUID" -ne 0 ]
  then echo "Please re-run as root.\n"
  exit
fi

if [[ "$OSTYPE" == "linux-gnu" ]]; then
  # we are a linux distro of some sort

  if command -v apt-get > /dev/null 2>&1; then
    # we are a debian/Ubuntu distro
    # add the kivy PPA and update
    add-apt-repository ppa:kivy-team/kivy
    apt-get update
  
    #install pip and python-kivy for gui
    apt-get install python-setuptools python-dev build-essential python-kivy
  
    #install geckodriver
    wget https://github.com/mozilla/geckodriver/releases/download/v0.14.0/geckodriver-v0.14.0-linux64.tar.gz
  else
    # we are not a debian/Ubuntu distro so quit
    echo "Your Linux distribution is not supported. Sorry."
    exit
  fi

elif [[ "$OSTYPE" == "darwin"* ]]; then
  # we are Mac OS X

  if command -v brew > /dev/null 2>&1; then
    echo "Brew found. Skipping installation."
  else
    echo "Brew not found. Installing brew."
    # install homebrew
    /usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"
  fi

  # install kivy and dependencies
  brew install wget sdl2 sdl2_image sdl2_ttf sdl2_mixer gstreamer

  # get geckodriver
  wget https://github.com/mozilla/geckodriver/releases/download/v0.14.0/geckodriver-v0.14.0-macos.tar.gz
else
  echo "Your platform isn't supported. Sorry.\n"
  exit
fi

tar -xvzf geckodriver*.tar.gz
chmod +x geckodriver
mv geckodriver /usr/local/bin

easy_install pip

#install dependencies for fbscraper
pip install -r requirements.txt

