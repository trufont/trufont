## Intro

This is a step-by-step tutorial to get TruFont running on an Ubuntu live CD. This enables you to test the GitHub/master branch of TruFont easily, and is simpler than the instructions in README.md. 

If all else fails, try these instructions.

## Ubuntu 16.10

These steps might work for other versions of Ubuntu, but they were only tested on an Ubuntu 16.10 LiveCD.

- `sudo nano /etc/apt/sources.list` and add the word "**universe**" at the end of every line

- `sudo apt update && sudo apt install git python3-pip python3-venv`

- `pip3 install --upgrade pip`

- `git clone https://github.com/trufont/trufont && cd trufont`

- `python3 -m venv TruFont-VENV && source TruFont-VENV/bin/activate`

- `pip3 install -e .`

to run trufont, just type `trufont`
