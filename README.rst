Wagtail Page Importer
=====================

Adds the ability to Wagtail to import/update pages from a Yaml file.

Installing
----------

::

    INSTALLED_APPS = (
        ...
        'wagtailimporter',
        ...
    )

Usage
-----

::

    ./manage.py import_pages <page.yml> [<page.yml> [<page.yml> ... ] ...]

File format
-----------

Create a Yaml file/s for your pages.

::

    url: /site
    type: home.homepage

    # Your fields go here
    title: Welcome to my site!

    ---

    url: /site/about-us
    type: basic.basicpage

    title: About Us
    # This is a stream field
    body:
        - type: heading
          value: About Us
        - type: paragraph
          value: |
                <p>
                    Rich text block.
                </p>

        - type: linkbutton
          # Yaml object to reference another page on the site
          link: !page
              url: /site/contact-us
          text: Contact us

    # This is rich text
    tagline: |
        <div>We are <em>super great!</em></div>

    ---

    !custom_snippet
        slug: my-snippet
        title: My Snippet

Foreign Object References
-------------------------

Instead of having to resolve foreign keys (yuck!) you can pass Yaml objects
to create references, e.g. `!page` takes arguments that are used to reference
a page (by path `url`).

Builtin reference types:

* ``!page``

  Takes a `url` parameter to another page (must be already present).

* ``!image``

  Takes a `file` parameter to an image (either in `MEDIA/original/images`.

  Can also accept other `Image` related parameters such as `title`.

* ``!site``

  Lookup a `Site` by its `hostname`.

  Can also create sites if you specify `root_page` (as a `!page`).

  ::

      !site
          hostname: localhost
          site_name: My Site
          root_page: !page
              url: /my-site
          is_default_site: true

You can also create your own for your models:

::

    import wagtailimporter.serializer

    class Toplevel(wagtailimporter.serializer.GetOrCreateForeignObject):
        """A reference to a toplevel"""
        yaml_tag = '!toplevel'
        model = TopLevel

The following base classes are provided:

* `GetForeignObject`

  Calls `get` on an object defined by `lookup_keys`.

* `GetOrCreateForeignObject` (inherits from `GetForeignObject`)

  Calls `get_or_create` as above.

* `GetOrCreateClusterableForeignObject` (inherits from `GetForeignObject`)

  Calls `get` or creates a new, unsaved object
  (useful for `ClusterableModel` related classes).

  For example:

  ::

      url: /my/page
      type: some.type
      related_pages:
          - !relatedpage
                page: !page
                    url: /my/other/page

  ::

      class RelatedPage(Orderable):
          """A related page."""

          parent = ParentalKey(SiteSettings, related_name='related_pages')
          page = models.ForeignKey('wagtailcore.Page',
                                   null=True, blank=True,
                                   on_delete=models.CASCADE,
                                   related_name='+')

          panels = [
              PageChooserPanel('page'),
          ]


      class RelatedPageTag(GetOrCreateClusterableForeignObject):

          model = RelatedPage
          yaml_tag = '!relatedpage'
          lookup_keys = ('page',)


Importing snippets
------------------

Foreign object references can also be used to create and import snippets.

::

    !custom_snippet
        slug: my-snippet
        title: My Snippet

::

    import wagtailimporter.serializer

    class MySnippet(wagtailimporter.serializer.GetOrCreateForeignObject):
        """Creates a snippet"""
        yaml_tag = '!my-snippet'
        model = MySnippet

        lookup_keys = ('slug',)

License
-------

Copyright (c) 2016, Squareweave Pty Ltd

All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright
  notice, this list of conditions and the following disclaimer.
* Redistributions in binary form must reproduce the above copyright
  notice, this list of conditions and the following disclaimer in the
  documentation and/or other materials provided with the distribution.
* Neither the name of the Squareweave nor the
  names of its contributors may be used to endorse or promote products
  derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL SQUAREWEAVE BE LIABLE FOR ANY
DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
