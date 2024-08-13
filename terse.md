A Terse Profile for JSON-LD
===========================

Introduction
------------
[JSON-LD][] is a [JSON][]-based serialization syntax for [Linked Data][] and
[Resource Description Framework (RDF)][RDF] [datasets][]. JSON-LD facilities
are typically used to interpret otherwise idiomatic and ad hoc JSON documents
as RDF datasets, or to express RDF Datasets in idiomatic JSON.

JSON-LD provides a rich set of tools, some with complex semantics, to accommodate
the many idiomatic ad hoc data representations in common use by JSON-based
applications. In particular, JSON-LD allows a JSON document to reference
additional external context documents, without which the initial document
can’t be parsed to an RDF dataset. Popular implementations of the full JSON-LD
toolset (such as [jsonld.js][]) comprise thousands of lines and hundreds (or
thousands) of Kbytes of JavaScript.

This memo proposes the “Terse” profile, a simplified, constrained,
backward-compatible profile of JSON-LD, inspired by [Turtle][] (the Terse RDF
Triple Language). The Terse profile removes external context references,
keyword aliases, recursive compact IRI prefix definitions, transformations,
mappings, data indexing, reverse properties, property nesting, type coercions
(except for the `@type` keyword itself), and [named graphs][datasets]. This
profile is intended for pure Linked Data applications that don’t require
compatibility with ad hoc JSON documents, and therefore don’t require the
complexity of the full JSON-LD toolset. It leverages the ubiquity of JSON
document parsers for most popular programming languages and environments
(including web browsers) to eliminate the need to load large parser implementations
for common RDF serialization formats (such as Turtle) typically used in pure
Linked Data applications. Conforming documents are intended to be easy for
humans and computers to read and write.

The [reference implementation][], which parses documents conforming to this
profile, is about 220 lines of non-minified JavaScript with a compressed
transfer size of about 2300 bytes.

The Terse profile is provisionally identified by the URI

    http://zenomt.com/ns/jsonld-terse

Terminology
-----------
The key words "**MUST**", "**MUST NOT**", "**REQUIRED**", "**SHALL**", "**SHALL
NOT**", "**SHOULD**", "**SHOULD NOT**", "**RECOMMENDED**", "**NOT RECOMMENDED**",
"**MAY**", and "**OPTIONAL**" in this document are to be interpreted as
described in [BCP 14][] \[[RFC2119][]\] \[[RFC8174][]\] when, and only when, they
appear in all capitals, as shown here.

The key words "**MUST (BUT WE KNOW YOU WON'T)**", "**SHOULD CONSIDER**",
"**REALLY SHOULD NOT**", "**OUGHT TO**", "**WOULD PROBABLY**", "**MAY WISH TO**",
"**COULD**", "**POSSIBLE**", and "**MIGHT**" in this document are to be
interpreted as described in [RFC 6919][] when, and only when, they appear in
all capitals, as shown here.

This document assumes an understanding of Linked Data, RDF, JSON, and JSON-LD
terminology, syntax, and semantics.

Definition
----------
A “Terse” JSON-LD document is a JSON-LD document constrained thus:

A Terse document encodes exactly one [RDF Graph][graph] (the default graph).
The `@graph` keyword is not recognized; use `@included` instead if needed.

A document **SHALL** consist of either one top-level JSON `Object`, or a JSON
`Array` of `Object`s, the `Object`s representing named or blank nodes.

If an `Object` contains an `@list` member, it is an RDF List, the member’s
value **MUST** be a (potentially empty) `Array`, and any other members of the
`Object` are ignored.

Otherwise, if an `Object` contains an `@value` member, it is an RDF Literal.
An RDF Literal `Object` **MAY** also include `@type`, `@language`, and
`@direction` members, as appropriate. Any other members are ignored.

If an RDF Literal `Object` has an `@type` member, its value **SHALL** be a
`String` representing a compact IRI, IRI reference, or be the keyword `@json`,
which is equivalent to `http://www.w3.org/1999/02/22-rdf-syntax-ns#JSON`.

Otherwise, an `Object` is a node, which can be named or blank.

A node is a named node if it has an `@id` member whose value is a `String`
not beginning with “`_:`”, that represents a compact IRI or IRI reference.

A node is a blank node if it does not have an `@id` member, or it has an `@id`
member and its value is a `String` beginning with “`_:`”.

A node **MAY** have an `@context` member.

An `@context`’s value **MUST** be an `Object`.

An `@context`’s members **SHALL** consist only of:
* `@base` : (**OPTIONAL**), whose value **SHALL** be a `String` representing an IRI reference relative to the currently-in-force base to use as the new base IRI against which to resolve IRI references within this `Object`'s scope;
* `@vocab` : (**OPTIONAL**), whose value **SHALL** be a `String` representing an IRI reference relative to the currently-in-force base (after applying the `@base` of this context, if any) to be used as a prefix to be prepended to `Object` member keys that aren’t absolute IRIs, compact IRIs, or exact matches to `@context` terms;
* zero or more non-IRI terms (that is, not containing a colon) and not beginning with an `@`, whose values **SHALL** be `null` or a `String` representing an IRI reference relative to the currently-in-force base (after applying the `@base` of this context, if any) to be used as a compact IRI prefix or, for `Object` member names, an exact-match replacement. Values **SHALL NOT** themselves be compact IRIs to be recursively expanded.

While allowed, document authors **OUGHT TO** avoid nested `@context`s, as
doing so should be unnecessary in idiomatic documents and could obfuscate the
document’s meaning to a casual human reader.

A node **MAY** have an `@type` member, whose value **SHALL** be either a
`String` or an `Array` of `String`s each representing a compact IRI or IRI
reference.

A node `Object` **MAY** have an `@included` member, whose value **SHALL** be
either a node `Object`, or an `Array` of node `Object`s.

Any other `Object` member names beginning with “`@`” **SHALL** be ignored.

Any other `Object` member names of a node that are not compact IRIs, absolute
IRIs, or exact matches with an `@context` member, **SHALL** be ignored unless
an `@vocab` is set, in which case each is concatenated with the `@vocab` to
form an absolute IRI.

JSON’s primitive values (`Number`s, `String`s, `null`, `true`, and `false`)
are RDF Literals.

Only the following JSON-LD keywords are recognized:

* `@context` : Only in a node
* `@base` : Only in an `@context`
* `@vocab` : Only in an `@context`
* `@list` : As the only member of an `Object` that is the object of a triple
* `@value` : The presence of this member defines the `Object` as an RDF Literal
* `@id` : Only in a node
* `@type` : Can appear in a node or an RDF Literal
* `@language` : Only in an RDF Literal whose value is a string type
* `@direction` : Only in an RDF Literal whose value is a string type
* `@json` : Only as the `String` value of an `@type` keyword
* `@included` : Only in a node

Example 1
---------
#### Graph Expressed as Terse JSON-LD
```
{
    "@context": {
        "@base":  "https://example.com/people/card",
        "foaf":   "http://xmlns.com/foaf/0.1/",
        "schema": "http://schema.org/"
    },
    "@id": "#me",
    "@type": ["foaf:Person", "schema:Person"],
    "foaf:name": { "@value": "Michael Thornburgh", "@language": "en-us" },
    "foaf:nick": "Mike",
    "foaf:depiction": { "@id": "mike.jpg" },
    "schema:worksFor": {
        "@type": "schema:Corporation",
        "schema:name": "Example Corp.",
        "schema:employee": { "@id": "#me" }
    },
    "@included": [
        { "@id": "", "@type": "foaf:PersonalProfileDocument", "foaf:primaryTopic": { "@id": "#me" } },
        { "@id": "_:b86", "foaf:knows": { "@id": "_:b99" } },
        { "@id": "_:b99", "foaf:knows": { "@id": "_:b86" } }
    ]
}
```

#### Same Graph Expressed as Idiomatic Turtle
```
@base           <https://example.com/people/card> .
@prefix foaf:   <http://xmlns.com/foaf/0.1/> .
@prefix schema: <http://schema.org/> .

<#me>
    a foaf:Person, schema:Person;
    foaf:name "Michael Thornburgh"@en-us;
    foaf:nick "Mike";
    foaf:depiction <mike.jpg>;
    schema:worksFor [
        a schema:Corporation;
        schema:name "Example Corp.";
        schema:employee <#me>
    ] .

<> a foaf:PersonalProfileDocument; foaf:primaryTopic <#me> .

_:b86 foaf:knows _:b99 .
_:b99 foaf:knows _:b86 .
```

#### Graph Resolved to N-Triples
```
<https://example.com/people/card#me> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://xmlns.com/foaf/0.1/Person> .
<https://example.com/people/card#me> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://schema.org/Person> .
<https://example.com/people/card#me> <http://xmlns.com/foaf/0.1/name> "Michael Thornburgh"@en-us .
<https://example.com/people/card#me> <http://xmlns.com/foaf/0.1/nick> "Mike" .
<https://example.com/people/card#me> <http://xmlns.com/foaf/0.1/depiction> <https://example.com/people/mike.jpg> .
<https://example.com/people/card#me> <http://schema.org/worksFor> _:b0 .

<https://example.com/people/card> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://xmlns.com/foaf/0.1/PersonalProfileDocument> .
<https://example.com/people/card> <http://xmlns.com/foaf/0.1/primaryTopic> <https://example.com/people/card#me> .

_:b0 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://schema.org/Corporation> .
_:b0 <http://schema.org/name> "Example Corp." .
_:b0 <http://schema.org/employee> <https://example.com/people/card#me> .

_:b1 <http://xmlns.com/foaf/0.1/knows> _:b2 .

_:b2 <http://xmlns.com/foaf/0.1/knows> _:b1 .
```

Example 2
---------
#### Graph From [Example 7 of the JSON-LD Spec](https://www.w3.org/TR/json-ld/#example-7-in-line-context-definition)
```
{
  "@context": {
    "name": "http://schema.org/name",
    "image": {
      "@id": "http://schema.org/image",
      "@type": "@id"
    },
    "homepage": {
      "@id": "http://schema.org/url",
      "@type": "@id"
    }
  },
  "name": "Manu Sporny",
  "homepage": "http://manu.sporny.org/",
  "image": "http://manu.sporny.org/images/manu.png"
}
```

#### Same Graph Expressed as Idiomatic Terse JSON-LD
```
{
    "@context": {
        "schema": "http://schema.org/"
    },
    "schema:name": "Manu Sporny",
    "schema:url": { "@id": "http://manu.sporny.org/" },
    "schema:image": { "@id": "http://manu.sporny.org/images/manu.png" }
}
```

#### Same Graph Expressed as Idiomatic Turtle
```
@prefix schema: <http://schema.org/> .

[
    schema:name "Manu Sporny";
    schema:url <http://manu.sporny.org/>;
    schema:image <http://manu.sporny.org/images/manu.png>
] .
```

#### Graph Resolved to N-Triples
```
_:b0 <http://schema.org/name> "Manu Sporny" .
_:b0 <http://schema.org/url> <http://manu.sporny.org/> .
_:b0 <http://schema.org/image> <http://manu.sporny.org/images/manu.png> .
```

  [JSON-LD]: https://json-ld.org/
  [JSON]: https://www.rfc-editor.org/rfc/rfc8259
  [Linked Data]: https://www.w3.org/DesignIssues/LinkedData
  [RDF]: https://www.w3.org/RDF/
  [graph]: https://www.w3.org/TR/rdf11-concepts/#section-rdf-graph
  [datasets]: https://www.w3.org/TR/rdf11-concepts/#section-dataset
  [Turtle]: https://www.w3.org/TR/turtle/
  [jsonld.js]: https://github.com/digitalbazaar/jsonld.js
  [reference implementation]: https://github.com/zenomt/jsonld-terse
  [BCP 14]: https://www.rfc-editor.org/info/bcp14
  [RFC2119]: https://www.rfc-editor.org/rfc/rfc2119
  [RFC8174]: https://www.rfc-editor.org/rfc/rfc8174
  [RFC 6919]: https://www.rfc-editor.org/rfc/rfc6919
