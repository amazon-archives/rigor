A Rigor walkthrough
===================

Let's say you want to use Rigor to manage your ground truth. Good choice! This brief tutorial will help you get set up with a new installation.

.. note:: This tutorial is geared towards POSIX systems using the command line. If any Windows users want to port it, fantastic. We'll make the changes.

First steps
-----------
Be sure you've got everything installed. See :ref:`installation` for installation instructions. We'll be using the :py:mod:`sqlite3` module for database access in this tutorial. If you want to store your data in `S3`_, you'll also need the `Boto`_ module installed.

.. _Boto: https://pypi.python.org/pypi/boto
.. _S3: http://aws.amazon.com/s3/

Let's create a new project directory::

  mkdir rigor_tutorial
  cd rigor_tutorial

We'll need somewhere to store the imported data::

  mkdir data_repo

And, somewhere to store data we're about to import::

  mkdir to_import

Configure
---------
Rigor has a few options, mostly dealing with database connections. Copy the :download:`rigor.ini.sample <../rigor.ini.sample>` into your home directory as :file:`.rigor.ini`. You shouldn't need to make any changes to it for now.

Create database
---------------
Rigor uses `Alembic`_ for database migrations. Make sure you have that installed first, then you should be able to create your database by running::

  alembic upgrade head

The script will prompt you for a database name. Enter :file:`tutorial.db`; it'll create a new database in the current directory.

.. _Alembic: https://bitbucket.org/zzzeek/alembic

Create data
-----------
Normally, you'll have some data you want to import into Rigor. To make this tutorial consistent, we'll create our own very simple synthetic data.

Here's a simple Python program that will create some example data files in our :file:`to_import` directory, and a master import file in the current directory:

.. literalinclude:: tut_make_data.py
  :language: python

You can download it :download:`here <tut_make_data.py>`.

The script will create a file called :file:`percepts.json` in the current directory. You can find some more information on annotations in :ref:`importing`. Basically, this file describes the contents of the data files we just created.

Import data
-----------
We now have percept data and percepts. Let's bring them into the database::

  import.py tutorial.db percepts.json

You'll get some output showing each percept being imported, and now :file:`data_repo` should contain these files::

   01.txt  03.txt  05.txt  07.txt  09.txt
   02.txt  04.txt  06.txt  08.txt  10.txt

You can refer to documentation for :py:class:`rigor.interop.Importer` if the command line tool doesn't do everything you want.

Design an Algorithm
-------------------
A Rigor :py:class:`~rigor.algorithm.Algorithm` is the interface between Rigor's data store and the algorithm you wish to run against it.

Let's create the most basic :py:class:`~rigor.algorithm.Algorithm` possible -- one that just reads the data file and returns its contents. Here it is:

.. literalinclude:: tut_runner.py
  :pyobject: PassthroughAlgorithm

Run the Algorithm
-----------------
Now that we have our algorithm to test, let's get Rigor to run it for us. In order to do that, we create a :py:class:`~rigor.runner.Runner`. In it, we implement two methods: :py:meth:`~rigor.runner.Runner.get_percepts` and :py:meth:`~rigor.runner.Runner.evaluate`.

.. literalinclude:: tut_runner.py
  :pyobject: AllPerceptRunner

:py:meth:`~rigor.runner.Runner.get_percepts` is where we decide which ground truth we wish to run our algorithm against. It returns a list of :py:class:`~rigor.types.Percept` objects, with attached annotations.

The :py:meth:`~rigor.runner.Runner.evaluate` method gets a list of result tuples from the :py:class:`~rigor.algorithm.Algorithm` -- by default, the original :py:class:`~rigor.types.Percept`, the result (returned value of the :py:meth:`~rigor.algorithm.Algorithm.run` method), the :py:class:`~rigor.types.Annotation` objects associated with that :py:class:`~rigor.types.Percept`, and the elapsed time in seconds. Our simple example just prints the percept's ID, the expected value (from the first :py:class:`~rigor.types.Annotation`; there can be more than one), and the actual value (from the :py:class:`~rigor.algorithm.Algorithm`).

Now that everything's set up, we create the objects and run the algorithm against the chosen percepts:

.. literalinclude:: tut_runner.py
  :lines: 23-26

This is creating a configuration object that reads the :file:`.rigor.ini` file we created earlier. It then instantiates the :py:class:`~rigor.algorithm.Algorithm` we designed, passes it to a :py:class:`~rigor.runner.Runner` instance that can find our database, and then tells the :py:class:`~rigor.runner.Runner` to run.

All of this code is available :download:`here <tut_runner.py>`. Time to run the code::

  python tut_runner.py

The output should include some debug information, and then print::

  Percept Expected  Actual
  1       1         1
  2       2         2
  3       3         3
  4       4         4
  5       5         5
  6       6         6
  7       7         7
  8       8         8
  9       9         9
  10      10        10

Looks like our :py:class:`~rigor.algorithm.Algorithm` was successful. That's great!

Export data
-----------
In some cases, it might be useful to export the data in Rigor to another application. It's also a simple way to create snapshots or backups.

To export your entire database, run::

  export.py tutorial.db metadata.json

This will create a :file:`metadata.json` file with the contents of the database. It can be imported (into a new database) using the :file:`import.py` script. See :py:class:`rigor.interop.Exporter` for more information if you need finer-grained control of the export process.
