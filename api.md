Terse JSON-LD API
=================
This memo describes a JSON-based HTTP API framework for accessing and
manipulating resources structured and represented as Linked Data using the
Terse Profile for JSON-LD.

Terminology
-----------
The key words "**MUST**", "**MUST NOT**", "**REQUIRED**", "**SHALL**", "**SHALL
NOT**", "**SHOULD**", "**SHOULD NOT**", "**RECOMMENDED**", "**NOT RECOMMENDED**",
"**MAY**", and "**OPTIONAL**" in this document are to be interpreted as
described in [BCP 14][] \[[RFC2119][]\] \[[RFC8174][]\] when, and only when, they
appear in all capitals, as shown here.

This memo assumes familiarity with the concepts and terminology of
[Linked Data][] and the [Resource Description Framework (RDF)][RDF],
including the terms [graph][],
[default graph](https://www.w3.org/TR/rdf11-concepts/#section-dataset),
[merge](https://www.w3.org/TR/rdf11-mt/#shared-blank-nodes-unions-and-merges),
[triple, subject, predicate, object, node](https://www.w3.org/TR/rdf11-concepts/#dfn-rdf-triple),
and [blank node](https://www.w3.org/TR/rdf11-concepts/#dfn-blank-node);
and the [Terse Profile for JSON-LD][jsonld-terse] serialization syntax and
semantics for RDF graphs.

The terms "safe" and "unsafe", when describing HTTP operations, have the
meanings described in
[Section 9.2.1 of RFC 9110](https://www.rfc-editor.org/rfc/rfc9110.html#section-9.2.1).

The prefix `api:` stands for
[`http://zenomt.com/ns/terse-api#`](http://zenomt.com/ns/terse-api#),
the prefix `rdfs:` stands for
[`http://www.w3.org/2000/01/rdf-schema#`](http://www.w3.org/2000/01/rdf-schema#),
and the prefix `ex:` stands for `https://example.com/ns/`.

HTTP Requests and Responses
---------------------------
This memo defines a profile of additional constraints on the Terse Profile
for JSON-LD, as well as additional semantics. This derived profile is identified
by the URI
[`http://zenomt.com/ns/terse-api`][TERSE-API], and it is signaled in `Content-Type`
and other places by adding its URI to the `profile` parameter of the Terse
JSON-LD media-type:

> `application/ld+json; profile="http://zenomt.com/ns/jsonld-terse http://zenomt.com/ns/terse-api"`

Requests and responses **SHOULD** use `Accept` with that media-type where
appropriate to indicate support of this API.

Normal RESTful use of methods:
* [`OPTIONS`](https://www.rfc-editor.org/rfc/rfc9110.html#name-options)
* [`HEAD`](https://www.rfc-editor.org/rfc/rfc9110.html#name-head)
* [`GET`](https://www.rfc-editor.org/rfc/rfc9110.html#name-get)
* [`QUERY`][QUERY]
  - Query body media-type is application and resource specific
  - `Accept-Query` response header **SHOULD** be provided when supported
* [`POST`](https://www.rfc-editor.org/rfc/rfc9110.html#name-post)
  - Create a new item in an `api:Container`
  - When creating a new item, the base URI will be the URI of the new resource. Don't set an `@base` in `POST` body
  - Application-specific when `POST`ing to a non-container
* [`PATCH`][PATCH]
  - [Replace/insert/delete selected triples](#modifying-and-deleting-resources)
* [`PUT`](https://www.rfc-editor.org/rfc/rfc9110.html#name-put)
* [`DELETE`](https://www.rfc-editor.org/rfc/rfc9110.html#name-delete)

Use of the `Allow` response header is **RECOMMENDED**. It lists understood/supported
methods, not necessarily authorized methods.

Normal RESTful use of HTTP errors: (`4XX`, `5XX`), **OPTIONAL** app-specific
response bodies. If the error response body is intended to be machine-readable,
it **SHOULD** use either an appropriate app-specific RDF vocabulary expressed
as Terse JSON-LD with the Terse API’s content-type, or the JSON form of
[Problem Details for HTTP APIs][RFC9457] \[[RFC9457][]\] with content-type
`application/problem+json`.

Message Body
------------
Request and response bodies **SHALL** be Terse JSON-LD documents encoded as
a single top-level JSON Object.

The JSON Object encodes the default RDF Graph. It **MAY** also contain an
`@metadata` member encoding a supplementary [metadata graph](#metadata-and-paging).

A response graph **SHALL** be considered authoritative for subjects at the
request URI (regardless of query parameters). A response can delegate authority
for its URI namespace to other URIs by using the `Location` and `Content-Location`
response headers, `rdfs:seeAlso` links, and [paging links](#metadata-and-paging),
as might be encountered for example with `3XX` redirects, responses to a
`QUERY`, or paged responses.

For example, if a request was redirected with a `303 See Other`, the final
response graph is authoritative for subjects at the original target URI and
the final response URI. Note: any other automatically-followed intermediate
redirect URIs are not visible to browser JavaScript.

Relative URI references in a response are resolved using the final response
URI as the base URI.

As an optimization to avoid additional HTTP transactions, a response graph
**MAY** include triples that might be useful to the client for subjects at
other URIs. Clients **SHOULD** consider the response authoritative for subjects
at sub-paths of the response's authoritative URIs; however, clients
**MUST NOT** presume that the response graph includes _all_ of the triples
from the other resources' graphs. Whether or not a client ought to believe
extra included triples whose subjects are outside of the authoritative
hierarchies, or from different origins, is application specific.

Metadata and Paging
-------------------
Currently, the response supplementary metadata graph is only used to describe
paging. Other uses TBD. There is currently no defined use for the request
metadata graph.

If present, the metadata graph **SHOULD** have at least a subject _R_ being
the URI of the response.

If the response represents a page of a multi-page resource:

  * The response **SHALL** include a supplementary metadata graph
  * The metadata graph **SHALL** have a subject _R_ = the URI of the response
  * _R_ **MUST** have an `@type` of `api:Page`
  * _R_ **MUST** have an `api:pageOf` to the canonical URI for the resource of which it is a page
  * _R_ **MUST** have at least one of `api:prevPage` or `api:nextPage`

The graph of a paged resource is the merge of the default graphs of its pages.
The merged graph **SHALL** be considered authoritative for triples with
subjects at or at sub-paths of the authoritative URIs of the resource and
each of its pages.

Some applications might intend for just a subset of pages to be processed at
once, rather than merging them all together to a single graph before processing.
In these cases, it may be desirable for some triples to appear in every page.
When the same triples appear in multiple pages, care **SHOULD** be taken (for
example, by avoiding the use of blank nodes in repeated triples) so that pages
with repeated triples _can_ be merged without causing inadvertent duplicate
nodes in the merged graph.

The canonical URI for the paged resource **MAY** include `api:firstPage` and
`api:lastPage` links in the metadata graph, if appropriate and known. The
first and last pages **SHALL** be for the same pagination and result as the
current page, if that is defined.

When requesting a paged resource with `GET` or `QUERY`, if the "first"-ness
involves a request-specific state or cursor, then the first page **SHOULD**
have a URI distinct from the resource's canonical URI, to avoid inadvertently
creating new state or cursors if the first page is requested again. When
answering such a request, in addition to providing the distinct URI in an
`api:firstPage` metadata link, the server **SHOULD** either

* include a `Content-Location` response header linking to the first page's
  distinct URI; or
* redirect with `303 See Other` to the first page of the paged response (though
  this incurs an extra round-trip and doesn't allow for an ETag for the
  canonical resource).

The following example shows a `GET` for page 2 of a hypothetical 4-page
container `https://example.com/api/items/`. The container's canonical URI is
also its first page, because there is no request-specific state or cursor.
Each page includes the same `ex:usefulInfo` that could be safely merged with
other pages because it contains no blank nodes.

    GET /api/items/page2 HTTP/1.1
    Host: example.com
    Accept: application/ld+json; profile="http://zenomt.com/ns/jsonld-terse http://zenomt.com/ns/terse-api"

 
    HTTP/1.1 200 OK
    Content-Type: application/ld+json; profile="http://zenomt.com/ns/jsonld-terse http://zenomt.com/ns/terse-api"
    Date: Sat, 10 Aug 2024 19:04:48 GMT

    {
        "@context": {
            "api": "http://zenomt.com/ns/terse-api#",
            "ex": "http://example.com/ns/"
        },
        "@metadata": {
            "@id": "",
            "@type": "api:Page",
            "api:pageOf": {
                "@id": ".",
                "api:firstPage": { "@id": "." },
                "api:lastPage": { "@id": "page4" }
            },
            "api:prevPage": { "@id": "." },
            "api:nextPage": { "@id": "page3" }
        },
        "@id": ".",
        "@type": "api:Container",
        "api:containerOf": { "@id": "ex:Item },
        "api:contains": [
            { "@id": "4", "@type": "ex:Item", "ex:name": "example item 4" },
            { "@id": "5", "@type": "ex:Item", "ex:name": "example item 5" },
            { "@id": "6", "@type": "ex:Item", "ex:name": "example item 6" }
        ],
        "ex:usefulInfo": { "@id": ".#info", "ex:comment": "I can safely appear in each page." }
    }

Containers
----------
An `api:Container` is an unordered collection of `api:Resource`s. A container's
URI path **MUST** end in a slash. A container's members **MUST** have URIs
at a sub-path of the container's URI; clients **SHOULD** ignore any `api:contains`
triple whose object's URI is not at a sub-path of the container's URI.

A container **MUST** have an `@type` of `api:Container`.

A container's members are enumerated by `api:contains`.

A container **MAY** have `api:containerOf` triples to advertise potential
types for the container's members. These triples are optional, but may be
useful for understanding the types of members that can be added with `POST`
as described below.

A container or the container resource's graph **MAY** have other triples
including addtional `@type`s, according to the application.

If supported, a new member is added to a container by a `POST` to the container's
URI. If supported, the server might (but is under no obligation to) honor a
[`Slug`](https://www.rfc-editor.org/rfc/rfc5023.html#section-9.7) request
header, if present, for influencing the URI of the new member.

If supported, a member is deleted and removed from the container by a `DELETE`
of the member's URI.

An existing container's URI **SHOULD NOT** support `PUT`. The server **MAY**
permit creation of a new empty container resource using `PUT` to a sub-path
of an appropriate parent resource. `PATCH` of a container **MAY** be supported,
but only for modifying application-specific non-container attributes of the
container resource; that is, containment `api:contains` relations **MUST NOT**
be modified with `PATCH`.

If supported, the container and (recursively) its contained members are deleted
by a `DELETE` of the container's URI.

Modifying and Deleting Resources
--------------------------------
If supported, an existing resource can be partially modified using the `PATCH`
method. The effect is that for each subject and predicate represented in the
request's default graph serialization, all triples with the same subject and
predicate in the resource's graph are replaced with the corresponding triples
from the request body's default graph. Note that the serialization permits
identifying a subject and predicate with no objects (and therefore no triples).

Example: Given an existing resource state for `https://example.com/api/example`
(expressed here as [N-Triples][])

    <https://example.com/api/example>  <http://example.com/ns/foo>  "foo".
    <https://example.com/api/example>  <http://example.com/ns/bar>  "bar1".
    <https://example.com/api/example>  <http://example.com/ns/bar>  "bar2".
    <https://example.com/api/example>  <http://example.com/ns/bif>   4.

The following patch says that the `ex:foo` triple should be removed, that one
_new_ `ex:bar` triple should be added, and two new `ex:baz` triples should
be added, while leaving the `ex:bif` triple alone:

    PATCH /api/example HTTP/1.1
    Host: example.com
    Content-Type: application/ld+json; profile="http://zenomt.com/ns/jsonld-terse http://zenomt.com/ns/terse-api"

    {
        "@context": { "ex": "http://example.com/ns" },
        "@id": "",
        "ex:foo": [ ],
        "ex:bar: [ "bar1", "bar2", "bar3" ],
        "ex:baz": [ "baz1", "baz2" ]
    }

And might result, if there were no problems, in the resource now having state

    <https://example.com/api/example>  <http://example.com/ns/bar>  "bar1".
    <https://example.com/api/example>  <http://example.com/ns/bar>  "bar2".
    <https://example.com/api/example>  <http://example.com/ns/bar>  "bar3".
    <https://example.com/api/example>  <http://example.com/ns/baz>  "baz1".
    <https://example.com/api/example>  <http://example.com/ns/baz>  "baz2".
    <https://example.com/api/example>  <http://example.com/ns/bif>   4.

If supported, a resource's state is created or completely replaced by a `PUT`
request body's default graph.

If supported, an existing resource (and any sub-resources) is completely
removed by a `DELETE` of its URI.

It may be difficult or awkward to `PATCH` a complex resource, and in particular
to insert, modify, or remove deeply-nested triples. It is therefore **RECOMMENDED**
that complex resources intended to be modified be factored into hierarchical
sub-resources with distinct URIs that can be `POST`ed, `PATCH`ed, `PUT`, or
`DELETE`d independently.

The application and the shapes & semantics of the resources determine whether
the requested modifications are valid and allowed. A successful modification
**SHOULD** answer `204 No Content`; unsuccessful or invalid modifications
**SHOULD** answer the most appropriate `4XX` status code. If possible,
successful `PATCH` or `PUT` `204` responses **SHOULD** include an `ETag` for
the new state of the resource.

Conditional Requests
--------------------
Where appropriate, servers **SHOULD** support conditional requests by supplying
`ETag`s in responses and supporting `If-Match` and `If-None-Match` request
headers, especially for unsafe methods.

Security and Privacy Considerations
-----------------------------------
Responses can include triples with subjects or objects at different origins,
or outside the authoritative realm, of the response's URI. Clients **SHOULD**
take care to not _inadvertently_ dereference URIs beyond the authority of the
server from which they were learned, particularly with unsafe methods.

To avoid leaking access credentials, clients **SHOULD** take care to not
dereference URIs at other origins while inadvertently using access credentials
that don't belong with the other origins.


  [Linked Data]: https://www.w3.org/DesignIssues/LinkedData
  [jsonld-terse]: https://zenomt.github.io/jsonld-terse/
  [RDF]: https://www.w3.org/RDF/
  [graph]: https://www.w3.org/TR/rdf11-concepts/#section-rdf-graph
  [QUERY]: https://datatracker.ietf.org/doc/draft-ietf-httpbis-safe-method-w-body/
  [PATCH]: https://www.rfc-editor.org/rfc/rfc5789.html
  [BCP 14]: https://www.rfc-editor.org/info/bcp14
  [RFC2119]: https://www.rfc-editor.org/rfc/rfc2119
  [RFC8174]: https://www.rfc-editor.org/rfc/rfc8174
  [RFC9457]: https://www.rfc-editor.org/rfc/rfc9457
  [N-Triples]: https://www.w3.org/TR/n-triples/
  [TERSE-API]: http://zenomt.com/ns/terse-api
