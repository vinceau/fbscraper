#!/usr/bin/env bash

# function for generating the Ubuntu icon onto the desktop
function gen_ubuntu_icon() {
  FBSpath="$HOME/Documents/fbscraper/main.py"
  ShortcutContents="[Desktop Entry]\nName=FBScraper\nType=Application\nIcon=facebook\nExec=python $FBSpath\nTerminal=false\nStartupNotify=true"
  ShortcutLocation="$HOME/Desktop/fbscraper.desktop"
  printf "$ShortcutContents" > "$ShortcutLocation"
  chmod +x "$ShortcutLocation"

  return 0
}


function ubuntu_install() {
  # add the kivy PPA and update
  add-apt-repository ppa:kivy-team/kivy
  apt-get update

  #install pip and python-kivy for gui
  apt-get install python-setuptools python-dev build-essential python-kivy

  #install geckodriver
  wget https://github.com/mozilla/geckodriver/releases/download/v0.14.0/geckodriver-v0.14.0-linux64.tar.gz

  # make the fbscraper icon
  gen_ubuntu_icon

  return 0
}


function osx_install() {
  if command -v brew > /dev/null 2>&1; then
    echo "Brew found. Skipping installation."
  else
    echo "Brew not found. Installing brew."
    # install homebrew
    /usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"
  fi

  # install wget and kivy dependencies
  brew install wget pkg-config sdl2 sdl2_image sdl2_ttf sdl2_mixer gstreamer

  # get geckodriver
  wget https://github.com/mozilla/geckodriver/releases/download/v0.14.0/geckodriver-v0.14.0-macos.tar.gz

  return 0
}


#make sure we are running as root
if [ "$EUID" -ne 0 ]
  then echo "Please re-run as root."
  exit
fi

if [[ "$OSTYPE" == "linux-gnu" ]]; then
  # we are a linux distro of some sort

  if command -v apt-get > /dev/null 2>&1; then
    # we are a debian/Ubuntu distro
    ubuntu_install
  else
    # we are not a debian/Ubuntu distro so quit
    echo "Your Linux distribution is not supported. Sorry."
    exit
  fi

elif [[ "$OSTYPE" == "darwin"* ]]; then
  # we are Mac OS X
  osx_install
else
  echo "Your platform isn't supported. Sorry."
  exit
fi

tar -xvzf geckodriver*.tar.gz
chmod +x geckodriver
mv geckodriver /usr/local/bin

easy_install pip

if [[ "$OSTYPE" == "darwin"* ]]; then
  # we are Mac OS X
  pip install -U Cython
  pip install kivy
fi

#install dependencies for fbscraper
pip install -r requirements.txt

