Rigor
=====

Introduction
------------
Rigor is a framework for managing labeled data (:dfn:`percepts`), and for testing algorithms against that data in a systematic fashion.

Percept data, once imported, is stored in a file tree using a unique identifier. A separate set of database tables contain the percept metadata, keyed to the data files using the same identifier. Aside from general attributes (MIME type, location, etc.), percepts can also have any number of tags and  key-value pairs (:dfn:`properties`). They can also be members of multiple :dfn:`collections`. Between all of these metadata types, it is possible to perform complex filtering queries to build sets of percepts, which can be useful for more detailed analysis of algorithms.

Each percept can also have a number of annotations. Annotating a percept defines the ground truth in a particular domain, such as whether level of blurriness or location of text in an image-type percept, or extent and content of a phoneme in an audio percept. A single percept can have annotations in different domains, and it can even have multiple annotations in the same domain (generally used when an annotation contains a boundary, and multiple regions of interest exist).

When running Rigor, by default all percepts and annotations in a particular domain will be run against the algorithm. This can be limited to a smaller sample using the command-line tools, or much more extensively tweaked by writing a standalone Python application which includes the Rigor libraries.

.. _prerequisites:

Prerequisites
-------------
* Python v2.7 or higher
* OpenCV 2.x Python bindings (optional, for reading images)
* SQLAlchemy 0.7.6 or higher, plus a suitable driver for your database (e.g. Psycopg2, pg8000, sqlite3, ...)
* Alembic 0.7.3 or higher, for creating database tables
* percept data repository, either mounted locally or accessible via HTTP or S3
* NumPy (optional, to use the ObjectAreaEvaluator)
* Shapely (optional, to use the ObjectAreaEvaluator)
* Boto (optional, to store data in S3)

.. _installation:

Installation
------------
Ensure that all of the :ref:`prerequisites` are installed, and then run::

    python setup.py install

Configuration
-------------
Copy the :file:`rigor.ini.sample` file to :file:`.rigor.ini` in your home directory. Commented-out values reflect the defaults; uncomment and change them to alter settings.

* The ``percept_repository`` can either be a local path, if you have the percept data repository mounted locally, or it can be a base URL for fetching remote percept data.

You may need to set the :envvar:`LD_LIBRARY_PATH` or :envvar:`DYLD_LIBRARY_PATH` to point to any compiled algorithms that are not available systemwide.

Tutorial
--------
See :doc:`tutorial` to get started using Rigor.

.. _Importing:

Importing
~~~~~~~~~
Importing percepts basically entails copying the percept data file into the repository, and updating the database with metadata, tags, and annotations. There is an import script that will do most of this automatically, when supplied with a basic metadata description file.

You can find a guide to annotations at :doc:`textannotations`

.. warning:: Importing percepts into the database should be done carefully, as it is not always easy to undo mistakes.

The :program:`import.py` command takes a single JSON metadata file, or a list of metadata files, and imports all of the percepts described therein.

A minimal :file:`metadata.json` file might just have tags and a source filename specified:

.. topic:: Example minimal :file:`metadata.json` file:

  ::

    {
      "source" : "file:///data/rigor/to_import/IMG000003.png",
      "locator" : "file:///data/rigor/repository/33/25/33253ae286c7ff0da5ff7f29db4db407.png",
      "tags" : [
        "source:berkeley_2011-02",
        "training",
        "money",
        "obscured"
      ],
      "x_size" : 256,
      "y_size" : 256,
      "byte_count": 32411
    }

.. warning:: When importing image percepts the "x_size" and "y_size" fields should be set to the image's width and height respectively, as they are likely to be needed by most algorithms, as well as RigorHub.

Here is an example file for a image with many of the metadata fields used. Most are optional, but it is highly recommended to fill in as much information as is known, as that improves the quality of the database. See :py:meth:`~rigor.dbmapper.DatabaseMapper.add_percept` for a full list of percept fields.

.. topic:: Example :file:`IMG00022.json` file:

  ::

    {
      "source" : "file:///data/rigor/to_import/IMG000124.png",   <1>
      "locator" : "s3://my.bucket.name/ff/d9/ffd9ee17dd0c4d2692b4fa0cae92da29.png",  <2>
      "timestamp" : "2011-02-04T21:24:56Z",                      <3>
      "format" : "image/jpeg",                                   <4>
      "byte_count" : 38611,                                      <5>
      "location" : [ -122.269241, 37.871104 ],                   <6>
      "tags" : [                                                 <7>
        "training",
        "money",
        "obscured"
      ],
      "properties" : {
        "camera_angle": "30"
      },                                                         <8>
      "device_id" : "htc_nexus_one_55a",                         <9>
      "annotations" : [
        {
          "domain" : "money",                                    <10>
          "confidence" : "2",                                    <11>
          "model" : "20d",                                       <12>
          "boundary" : [                                         <13>
            [1, 2],
            [2, 4],
            [2, 8],
            [6, 7]
          ]
          "annotation_tags" : [
            "byhand",
            "multiple_words"
          ],
          "annotation_properties" : {
            "entered_by": "user_4433",
          }
        }
      ]
    }

  1. An absolute URL for the file data. If data is not being copied, this will just be used to determine MIME type
  2. An absolute URL for the final storage location of the file data. If data is not being copied, it will most likely match the source URL.
  3. The time and date (UTC) that the percept was recorded. The source file's timestamp will be used if this is not supplied here.
  4. The MIME type of the percept data. The file's extension will be used to guess a type if none is supplied here. Defaults to :py:data:`rigor.serialize.kDefaultMIMEType` if the guess fails.
  4. File size in bytes
  6. WGS84 lon/lat where the percept was recorded. Optional.
  7. Tags are freeform. The more the merrier.
  8. Properties are key-value pairs. Keys and values are always strings.
  9. Device ID identifies the device used to collect data, if applicable
  10. Domain is a sort of namespace for the annotation. Algorithms tend to test against annotations in a single domain.
  11. Confidence is the level of confidence we have in the annotation's correctness. Values should range from 1 to 5 where 1 is "unreviewed" and 5 is "publishable"
  12. The model is the actual ground truth used to compare against the returned value from an algorithm.
  13. The boundary is a list of coordinates, each defining a point in a polygonal bounding box.

Once you run the :program:`import.py` command, the percepts in the directory will be put into the database, and the source data will be copied into the repository root, unless copying is overridden.
