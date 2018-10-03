*
|Build Status|

TruFont
=======

`TruFont <https://trufont.github.io>`__ is a streamlined and hackable
font editor that lets you create and release OpenType font families.

Getting started
~~~~~~~~~~~~~~~

1. Install **Python 3.6** (or later):

   -  Windows: Download installer from
      `python.org/downloads <https://www.python.org/downloads/>`__
   -  OS X: Install using `Homebrew <http://brew.sh/>`__:
      ``brew install python3``
   -  Linux: It’s usually packaged with the OS.

2. Clone the repository and install the dependencies:

   .. code::

     git clone https://github.com/trufont/trufont
     cd trufont
     pip install -r requirements.txt
     pip install -e .

   Alternatively, you can install/update TruFont to the latest stable release:

   .. code::

     pip install --upgrade trufont

3. Run the app as ``trufont``, shorthand for ``python -m trufont``.

Contributing
~~~~~~~~~~~~

Here’s a quick tutorial if you’d like to contribute to TruFont.

1. Click the "Fork" button above, and clone the forked git repository
   to a new directory called ``trufont``:

   .. code::

     git clone https://github.com/<YOUR_USERNAME>/trufont

2. Move into the new folder and run this command to add the upstream
   repository url to the local list of remotes:

   .. code::

     git remote add upstream https://github.com/trufont/trufont

   This enables you to keep up-to-date with the upstream development.

3. Now, you can create and checkout your new feature branch:

   .. code::

     git checkout -b my-cool-new-feature

4. Use pip to install TruFont in "editable" mode:

   .. code::

     pip install --editable .

   This will link the package to your working directory instead of
   making a copy to Python site-packages directory, so you always run
   latest changes without having to reinstall.

5. It is also recommended to regularly update the dependencies to the
   curently tested versions as listed in `requirements.txt`:

   .. code::

     pip install --upgrade -r requirements.txt

6. Once you have commited your patch, push the new branch to your fork:

   .. code::

     git push -u origin my-cool-new-feature

7. Finally, click "New pull request" on TruFont’s Github page to submit
   your patch.

.. |Build Status| image:: https://travis-ci.org/trufont/trufont.svg?branch=master
   :target: https://travis-ci.org/trufont/trufont
