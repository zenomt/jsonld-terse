A Terse Profile for JSON-LD
===========================

[JSON-LD][] is a [JSON][]-based serialization syntax for [Linked Data][] and
[Resource Description Framework (RDF)][RDF] [datasets][]. JSON-LD facilities
are typically used to interpret otherwise idiomatic and ad hoc JSON documents
as RDF datasets.

JSON-LD provides a rich set of tools, some with complex semantics, to accommodate
the many idiomatic ad hoc data representations in common use by JSON-based
applications. In particular, JSON-LD allows a JSON document to reference
additional external context documents, without which the initial document
can’t be parsed to an RDF dataset. Popular implementations of the full JSON-LD
toolset (such as [jsonld.js][]) comprise thousands of lines and hundreds (or
thousands) of Kbytes of JavaScript.

[This project][] proposes the “[Terse](terse.md)” profile, a simplified,
constrained, backward-compatible profile of JSON-LD, inspired by
[Turtle][] (Terse RDF Triple Language). The Terse profile is intended for
pure Linked Data applications that don’t require compatibility with ad hoc
JSON documents, and therefore don’t require the complexity of the full JSON-LD
toolset. It leverages the ubiquity of JSON document parsers for most popular
programming languages and environments, including web browsers, to eliminate
the need to load large lexical analyzer and parser implementations for the
common RDF serialization formats (such as Turtle) typically used in pure
Linked Data applications. Conforming documents are intended to be easy for
humans and computers to write and read.

The [reference implementation](jsonld-terse.js), which parses documents
conforming to this profile, is about 200 lines of non-minified JavaScript
with a compressed transfer size of about 2000 bytes. This implementation
intentionally doesn’t expand `@list`s into RDF Lists, since the RDF List
construct is much harder to work with than JavaScript `Array`s. Also, this
implementation only processes URIs, since web browser JavaScript doesn’t
provide native IRI processing functions. IRIs in documents will be converted
to URIs according to JavaScript’s [`URL`][URL api] API.

The Terse profile is provisionally identified by the URI

    http://zenomt.com/ns/jsonld-terse

A [test page][] exercises the reference implementation.

Documentation
-------------
Documentation for the reference implementation is coming soon. Meanwhile,
please see the [test page][] for an example of how to use it.

Copyright Notice
----------------
Copyright © 2024 Michael Thornburgh. All rights reserved.

    SPDX-License-Identifier: MIT


  [JSON-LD]: https://json-ld.org/
  [JSON]: https://www.rfc-editor.org/rfc/rfc8259
  [Linked Data]: https://www.w3.org/wiki/LinkedData
  [RDF]: https://www.w3.org/RDF/
  [datasets]: https://www.w3.org/TR/rdf11-concepts/#section-dataset
  [This project]: https://github.com/zenomt/jsonld-terse
  [Turtle]: https://www.w3.org/TR/turtle/
  [jsonld.js]: https://github.com/digitalbazaar/jsonld.js
  [test page]: test.html
  [URL api]: https://url.spec.whatwg.org/#api
