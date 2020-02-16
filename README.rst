|Build Status|

TruFont
=======

`TruFont <https://trufont.github.io>`__ is a font-editing application
written with Python3, ufoLib, defcon and PyQt5.

Getting started
~~~~~~~~~~~~~~~

1. Install **Python 3.6** (or later):

   -  OS X: Install using `Homebrew <http://brew.sh/>`__:
      ``brew install python3``
   -  Windows: Download installer from
      `python.org/downloads <https://www.python.org/downloads/>`__
   -  Linux: It's usually packaged with the OS.

2. Set up a new Python **virtual environment**. Although this is not
   required, it's *highly recommended*, since TruFont has lots of
   dependencies, which may (or may not) conflict with other modules
   you installed globally.

   -  To create a new virtual environment in ``ENV_DIR``:

      ``python3 -m venv ENV_DIR``

      This creates a new ``ENV_DIR`` folder (you can choose the name
      you want). The ``bin`` subfolder (or ``Scripts`` if you are
      on Windows) contains a new ``python`` executable, and the
      ``pip`` installer linked to that.

   -  Activate the newly created environment:

      -  OS X or Linux: ``source ENV_DIR/bin/activate``
      -  Windows: ``ENV_DIR\Scripts\activate.bat``

      This temporarily adds the virtual environment's scripts folder to
      your console's `PATH`, so you can access `python`, `pip` and
      the `trufont` script from anywhere.

   -  Run ``deactivate`` when you wish to exit the virtual environment.
      This restores the default system `PATH`.

3. Install/update TruFont to the latest stable release:

   ``pip install --upgrade trufont``

4. Run the app as ``trufont``.

Contributing
~~~~~~~~~~~~

Here's a quick tutorial if you'd like to contribute to TruFont.

1. Click the "Fork" button above, and clone the forked git repository
   to a new directory called ``trufont``:

   ``git clone https://github.com/<YOUR_USERNAME>/trufont``

2. Move into the new folder and run this command to add the upstream
   repository url to the local list of remotes:

   ``git remote add upstream https://github.com/trufont/trufont``

   This enables you to keep up-to-date with the upstream development.

4. Synchronize your fork's `master` branch with the
   ``upstream/master``, especially before creating new branches:

   .. code::

     git checkout master
     git fetch upstream
     git rebase upstream/master
     git push

5. Install pre-commit. It will run some checks every time you are
   about to commit something.

   .. code::

     pip install pre-commit
     pre-commit install

5. Now, you can create and checkout your new feature branch:

   ``git checkout -b my-cool-new-feature``

6. Use pip to install TruFont in "editable" mode:

   ``pip install --editable .``

   Instead of copying `trufont` to your Python site-packages directory,
   this command only creates a link to the source directory inside the
   git repository. You can then modify the code in place, or
   synchronize the latest upstream changes (as in step 4) without
   having to re-install.

7. It is also recommended to regularly update the dependencies to the
   curently tested versions as listed in `requirements.txt`:

   ``pip install --upgrade -r requirements.txt``

8. Once you have commited your patch, push the new branch to your fork:

   ``git push -u origin my-cool-new-feature``

9. Finally, click "New pull request" on TruFont's Github page to submit
   your patch.

We will be happy to review and integrate it into the main app.

Happy hacking with TruFont! :muscle:

.. |Build Status| image:: https://travis-ci.org/trufont/trufont.svg?branch=master
   :target: https://travis-ci.org/trufont/trufont
