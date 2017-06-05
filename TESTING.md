## Intro

This is a step-by-step tutorial to get TruFont running from source. This enables you to test the GitHub/master branch of TruFont easily, and is simpler than the instructions in README.md. 

## Ubuntu

These steps should work for other versions of Ubuntu, but they were tested only on Ubuntu 16.10.

- *Live CD users only:* `sudo nano /etc/apt/sources.list` *and add the word "**universe**" at the end of every line*

- `sudo apt-get update && sudo apt-get install git python3-pip python3-venv`

- `pip3 install --upgrade pip`

- `git clone https://github.com/trufont/trufont && cd trufont`

- `python3 -m venv TruFont-VENV && source TruFont-VENV/bin/activate`

- `pip3 install -e .`

to run trufont, just type `trufont`
