Text annotations
================

An annotation has the following fields:

- id
- percept_id
- confidence
- stamp
- :term:`boundary`
- :term:`domain`
- :term:`model`

Definitions
-----------

.. glossary::

    domain
        Use one of the following values:

        - ``text:char`` -- A single character
        - ``text:word`` -- A word
        - ``text:line`` -- A line of words
        - ``text:lineorder`` -- A series of lines

    boundary
        A list of points defining the geometry of the annotation.

        For ``text:lineorder``, this represents a polyline which intersects some ``text:line`` annotations in the same order they should be read.  It must have two or more points. Each ``text:lineorder`` annotation should connect the lines of a single paragraph or column of text.

        For the other domains, the boundary should have exactly four points representing the corners of the bounding box of the char/word/line.  The bounding box is a quadrilateral which can be rotated or distorted; it does not have to be a perfect rectangle. The first point should be the top left corner of the object (in its local coordinate frame), and following points should be in clockwise order.

    model
        A string containing the text that this domain represents.  For example, "Hello there." or "Hello" or "H".  This can be ``NULL`` if an annotation has been placed on the image but the text has not yet been filled in.

        ``model`` will always be ``NULL`` in ``text:lineorder`` annotations.

Representing a lack of features in an image
-------------------------------------------

If an image does not contain any features in a particular domain, add one annotation in that domain with ``boundary`` set to ``NULL``, which we will call a :dfn:`NULL annotation`.  For example, a photo with no text whatsoever would contain four NULL annotations -- one for each domain.

If an image has not yet been annotated, it should have no annotations at all.  NULL annotations represent a certain lack of annotatable features in the image.

Legal combinations of annotations
---------------------------------

Annotations may occur in almost any combination in a single image.  For example, an image may have words but no lines or characters.

Each ``text:line`` should be a a part of either zero or one ``text:lineorder`` annotations, not more.

A NULL annotation and a non-NULL annotation for a particular domain should not both be present in the same image, because this would mean that the image has no features in that domain but also has a specific feature in that domain.

An image should never have more than one NULL annotation in a particular domain.

Punctuation and spaces
----------------------

Each piece of punctuation should have its own ``text:char`` annotation.

Words are separated by spaces only, so punctuation characters should be considered part of the word they're attached to if there's no space in between.  For example, the sentence "Hello there." contains two words, "Hello" and "there.".

Spaces are present in the model text of ``text:line`` annotations.  They are not included in ``text:char`` or ``text:word`` annotations.







