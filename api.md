Terse JSON-LD API
=================
This memo describes a hypermedia application protocol using HTTP to retrieve,
create, and manipulate resources structured and represented as Linked Data
using the Terse Profile for JSON-LD.

Terminology
-----------
The key words "**MUST**", "**MUST NOT**", "**REQUIRED**", "**SHALL**", "**SHALL
NOT**", "**SHOULD**", "**SHOULD NOT**", "**RECOMMENDED**", "**NOT RECOMMENDED**",
"**MAY**", and "**OPTIONAL**" in this document are to be interpreted as
described in [BCP 14][] \[[RFC2119][]\] \[[RFC8174][]\] when, and only when, they
appear in all capitals, as shown here.

This memo assumes familiarity with the concepts and terminology of the
[Representational State Transfer (REST)][REST] architectural style;
[Hypertext Transfer Protocol (HTTP, RFC 9110)][RFC9110];
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
and the prefix `ex:` stands for `https://example.com/ns#`.

HTTP Requests and Responses
---------------------------
This memo defines a profile of additional constraints on the Terse Profile
for JSON-LD, as well as additional semantics. This derived profile is identified
by the URI
[`http://zenomt.com/ns/terse-api`][TERSE-API], and it is signaled in `Content-Type`
and other places by adding its URI to the `profile` parameter of the Terse
JSON-LD media-type:

> `application/ld+json; profile="http://zenomt.com/ns/jsonld-terse http://zenomt.com/ns/terse-api"`

Requests and responses **SHOULD** use
[`Accept`](https://www.rfc-editor.org/rfc/rfc9110.html#name-accept)
with that media-type where appropriate to indicate support of this API.

Normal RESTful use of standard HTTP methods:
* [`OPTIONS`](https://www.rfc-editor.org/rfc/rfc9110.html#name-options)
* [`HEAD`](https://www.rfc-editor.org/rfc/rfc9110.html#name-head)
* [`GET`](https://www.rfc-editor.org/rfc/rfc9110.html#name-get)
* [`QUERY`][QUERY]
  - Query body media-type is application and resource specific
  - `Accept-Query` response header **SHOULD** be provided when supported
* [`POST`](https://www.rfc-editor.org/rfc/rfc9110.html#name-post)
  - Create a new item in an `api:Container`
    - When creating a new item, the base URI will be the URI of the new resource. Don't set an `@base` in `POST` body
  - Resource-specific when `POST`ing to a non-container
* [`PATCH`][PATCH]
  - [Replace/insert/delete selected triples](#modifying-and-deleting-resources)
* [`PUT`](https://www.rfc-editor.org/rfc/rfc9110.html#name-put)
* [`DELETE`](https://www.rfc-editor.org/rfc/rfc9110.html#name-delete)

Use of the [`Allow`](https://www.rfc-editor.org/rfc/rfc9110.html#name-allow)
response header is **RECOMMENDED**. It lists understood/supported
methods, not necessarily authorized methods.

Responses **MUST** use the most specific, accurate, and appropriate
[HTTP status code][HTTP-STATUS]. HTTP errors (status codes `4XX` & `5XX`)
**MAY** have application-specific response bodies to describe the problem
with more specificity and in greater detail than the status code alone conveys;
see [Problem Details](#problem-details) for more information.

### Conditional Requests
Where appropriate, servers **SHOULD** support conditional requests by supplying
`ETag`s in responses and supporting `If-Match` and `If-None-Match` request
headers, especially for unsafe methods.

Message Body
------------
RDF request and response bodies **SHALL** be encoded as Terse JSON-LD documents
having a single top-level JSON Object. The JSON Object encodes the default
RDF Graph.

The top-level Object **MAY** contain an `@metadata` member encoding a
supplementary [metadata graph](#metadata-and-paging).

The top-level Object **MAY** contain an `@remove` member encoding a graph
consisting of triples
[to be removed in a `PATCH` request](#modifying-and-deleting-resources).

A response graph **SHALL** be considered authoritative for subjects at the
request URI (regardless of query parameters). A response can delegate authority
for its URI namespace to other URIs by using the
[`Location`](https://www.rfc-editor.org/rfc/rfc9110.html#name-location)
and [`Content-Location`](https://www.rfc-editor.org/rfc/rfc9110.html#name-content-location)
response header fields, `rdfs:seeAlso` links, and
[paging links](#metadata-and-paging), as might be encountered for example
with `3XX` redirects, responses to a `POST` or `QUERY`, or paged responses.

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
from the other resources' graphs. How to handle extra included triples whose
subjects are outside of the authoritative hierarchies, or from different
origins, is application specific.

Containers
----------
An `api:Container` is an unordered collection of `api:Resource`s. A container's
URI path **MUST** end in a slash. A container's members **MUST** have URIs
at a sub-path of the container's URI; clients **SHOULD** ignore any `api:member`
triple whose object's URI is not at a sub-path of the container's URI.

A container **MUST** have an `@type` of `api:Container`.

A container's members are enumerated by `api:member`.

A container **MAY** have `api:containerOf` triples to advertise potential
types for the container's members. These triples are optional, but may be
useful for understanding the types of members that can be added with `POST`
as described below.

A container or the container resource's graph **MAY** have other triples
including addtional `@type`s, according to the application.

If supported, a new member is added to a container by a `POST` to the container's
URI. The base URI for resolving relative URI references in the request body
will be the URI of the new member. The server might (but is not obliged to)
honor a [`Slug`](https://www.rfc-editor.org/rfc/rfc5023.html#section-9.7)
request header, if present, for influencing a portion of the URI for the new
member. If the `Slug` header is present and the server incorporates it, but
the resulting URI is already in use, the server **SHOULD** refuse the request
with status `409 Conflict`. When answering `409 Conflict`, the server **SHOULD**
include a `Location` response header giving the URI of the conflicting member.

If supported, a member is deleted and removed from the container by a `DELETE`
of the member's URI.

The server **MAY** permit creation of a new empty container resource using
`PUT` to a sub-path of an appropriate parent resource.

An existing container's URI **SHOULD NOT** support `PUT`. The server **SHOULD**
respond to a `PUT` to an existing container with `409 Conflict`, unless the
request fails a precondition (such as `If-None-Match: *`) in which case
`412 Precondition Failed` takes precedence.

`PATCH` of a container **MAY** be supported, but only for modifying
application-specific non-container attributes of the container resource; that
is, containment `api:member` relations **MUST NOT** be modified with `PATCH`.

If supported, the container and (recursively) its contained members are deleted
by a `DELETE` of the container's URI.

Metadata and Paging
-------------------
There is currently no defined use for a request metadata graph.

If present, the supplementary metadata graph **SHOULD** have _at least_ a
subject _R_ being:

1. The URI indicated by the `Content-Location` response header field; or if not present
2. The URI indicated by the `Location` response header field; or if not present
3. The request's URI.

If the response represents a page of a resource:

  * The response **SHALL** include a supplementary metadata graph
  * The metadata graph **SHALL** have a subject _R_ = the URI as defined above
  * _R_ **SHALL** have an `@type` of `api:Page`
  * _R_ **SHALL** have an `api:pageOf` to the resource of which it is a page
  * If _R_ is not the last page of the resource, it **SHALL** have an `api:nextPage`
    link to the next page. _R_ **MAY** have an `api:prevPage` link to the
    previous page if appropriate, practical, and known.

The graph of a paged resource is the merge of the default graphs of its pages.
The merged graph **SHALL** be considered authoritative for triples with
subjects at or at sub-paths of the authoritative URIs of the resource and
each of its pages.

The paged resource **MAY** include `api:firstPage` and `api:lastPage` links
in the metadata graph, if appropriate and known. The first and last pages
**SHALL** be for the same pagination and result as the current page, if that
is defined.

When requesting a paged resource with `GET` or `QUERY`, if the "first"-ness
involves a request-specific state or cursor, then the first page **SHOULD**
have a URI distinct from the resource's canonical URI, to avoid inadvertently
creating new state or cursors if the first page is requested again. When
answering such a request, in addition to providing the distinct URI in an
`api:firstPage` metadata link, the server **SHOULD** either

* include a `Content-Location` response header linking to the first page's
  distinct URI; or
* redirect with `303 See Other` to the first page of the paged response (though
  this incurs an extra round-trip and doesn't allow for an `ETag` for the
  canonical resource).

Some applications might intend for just a subset of pages to be processed at
once, rather than merging them all together to a single graph before processing.
In these cases, it may be desirable for some triples to appear in every page.
When the same triples appear in multiple pages, care **SHOULD** be taken (for
example, by avoiding the use of blank nodes in repeated triples) so that pages
with repeated triples _can_ be merged without causing inadvertent duplicate
nodes in the merged graph.

A response that is a filtered or projected view of a resource (such as the
result of a `QUERY`) **SHOULD** have an `api:viewOf` in the metadata graph
to the URI of the resource of which it is a view.

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
    Date: Thu, 13 Feb 2025 04:03:10 GMT

    {
        "@context": {
            "api": "http://zenomt.com/ns/terse-api#",
            "ex": "http://example.com/ns#"
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
        "api:containerOf": { "@id": "ex:Item" },
        "api:member": [
            { "@id": "4", "@type": "ex:Item", "ex:name": "example item 4" },
            { "@id": "5", "@type": "ex:Item", "ex:name": "example item 5" },
            { "@id": "6", "@type": "ex:Item", "ex:name": "example item 6" }
        ],
        "ex:usefulInfo": { "@id": ".#info", "ex:comment": "I can safely appear in each page." }
    }

The following example shows a `QUERY` on a hypothetical queryable container
`https://example.com/api/stuff/` to find the items with type `ex:Foo`, and
answering the first page of the queried view of the container:

    QUERY /api/stuff/ HTTP/1.1
    Host: example.com
    Accept: application/ld+json; profile="http://zenomt.com/ns/jsonld-terse http://zenomt.com/ns/terse-api"
    Content-Type: application/x-www-form-urlencoded

    type=http%3A%2F%2Fexample.com%2Fns%23Foo


    HTTP/1.1 200 OK
    Content-Type: application/ld+json; profile="http://zenomt.com/ns/jsonld-terse http://zenomt.com/ns/terse-api"
    Content-Location: queries/42/1
    Date: Sat,  5 Apr 2025 23:30:17 GMT

    {
        "@context": {
            "api": "http://zenomt.com/ns/terse-api#",
            "ex": "http://example.com/ns#"
        },
        "@metadata": {
            "@id": "queries/42/1",
            "@type": "api:Page",
            "api:pageOf": {
                "@type": "api:View",
                "api:viewOf": { "@id": "." }
            },
            "api:nextPage": { "@id": "queries/42/2" }
        },
        "@id": ".",
        "@type": "api:Container",
        "api:containerOf": [ { "@id": "ex:Foo" }, { "@id": "ex:Bar" } ],
        "api:member": [
            { "@id": "1", "@type": "ex:Foo", "ex:name": "example Foo 1" },
            { "@id": "2", "@type": "ex:Foo", "ex:name": "example Foo 2" },
            { "@id": "3", "@type": "ex:Foo", "ex:name": "example Foo 3" }
        ]
    }

Modifying and Deleting Resources
--------------------------------
If supported, an existing resource can be partially modified using the `PATCH`
method. A `PATCH` request **MAY** contain an `@remove` member encoding a graph
consisting of triples to remove from the target resource. The request's default
graph consists of triples to merge into the target after the remove step.

The URI `api:any` is interpreted as a wildcard in the `@remove` graph, and
matches any URI, blank node, or literal in its corresponding role in a triple.
For example, the triple `{ api:any ex:foo "bar" }` matches triples with any
subject that have predicate `ex:foo` and object `"bar"`, the triple 
`{ ex:Mike ex:foo api:any }` matches any triple having subject `ex:Mike` and
predicate `ex:foo`, and the triple `{ ex:Mike api:any api:any }` matches any
triple having subject `ex:Mike`.

The target's graph is transformed as though the following steps were taken:

1. Remove all triples in the target's graph that match any triple in the
   `@remove` graph, including wildcard matches as described above; then

2. Merge all triples of the request's default graph into the resource's graph.

Note: the actual method by which a server implements the above transformation
is not mandatated by this memo; for example, a remove-then-merge for a subject
or subject+predicate might be implemented as updates/replacements to the data
model, rather than independent deletes and inserts.

Example: Given an existing resource state for `https://mike.example.com/card`

    GET /card HTTP/1.1
    Host: mike.example.com
    Accept: application/ld+json; profile="http://zenomt.com/ns/jsonld-terse http://zenomt.com/ns/terse-api"


    HTTP/1.1 200 OK
    Content-Type: application/ld+json; profile="http://zenomt.com/ns/jsonld-terse http://zenomt.com/ns/terse-api"
    Accept: application/ld+json; profile="http://zenomt.com/ns/jsonld-terse http://zenomt.com/ns/terse-api"
    Allow: GET, HEAD, PUT, PATCH, DELETE
    Date: Thu, 13 Feb 2025 04:03:11 GMT
    ETag: "55"

    {
        "@context": {
            "foaf": "http://xmlns.com/foaf/0.1/",
            "ex": "http://example.com/ns#"
        },
        "@id": "",
        "@type": "foaf:PersonalProfileDocument",
        "foaf:primaryTopic": {
            "@id": "#me",
            "@type": "foaf:Person",
            "foaf:name": "Michael Thornburgh",
            "foaf:nick": [ "Mike", "zenomt" ],
            "ex:extras": {
                "@id": "#extra",
                "@type": "ex:Extras",
                "ex:comment": "Some Extras"
            }
        }
    }


The following patch says to remove the nickname `"zenomt"` from `card#me`
(but leave `"Mike"`), remove any `ex:extras` links from `card#me`, remove all
triples with subject `card#extra`, and add an additional `@type` of `schema:Person`
to `card#me`, as long as the resource hasn't changed since the above response:

    PATCH /card HTTP/1.1
    Host: mike.example.com
    Accept: application/ld+json; profile="http://zenomt.com/ns/jsonld-terse http://zenomt.com/ns/terse-api"
    Content-Type: application/ld+json; profile="http://zenomt.com/ns/jsonld-terse http://zenomt.com/ns/terse-api"
    If-Match: "55"

    {
        "@context": {
            "api": "http://zenomt.com/ns/terse-api#",
            "foaf": "http://xmlns.com/foaf/0.1/",
            "schema": "http://schema.org/",
            "ex": "http://example.com/ns#"
        },

        "@remove": [
            {
                "@id": "https://mike.example.com/card#me",
                "foaf:nick": "zenomt",
                "ex:extras": { "@id": "api:any" }
            },
            {
                "@id": "https://mike.example.com/card#extra",
                "api:any": { "@id": "api:any" }
            }
        ],

        "@id": "https://mike.example.com/card#me",
        "@type": "schema:Person"
    }

And might result, if there were no problems, in the resource now having state
(with its representation also returned in the response for convenience):

    HTTP/1.1 200 OK
    Content-Type: application/ld+json; profile="http://zenomt.com/ns/jsonld-terse http://zenomt.com/ns/terse-api"
    Accept: application/ld+json; profile="http://zenomt.com/ns/jsonld-terse http://zenomt.com/ns/terse-api"
    Allow: GET, HEAD, PUT, PATCH, DELETE
    Date: Thu, 13 Feb 2025 04:03:12 GMT
    ETag: "56"

    {
        "@context": {
            "foaf": "http://xmlns.com/foaf/0.1/",
            "schema": "http://schema.org/"
        },
        "@id": "",
        "@type": "foaf:PersonalProfileDocument",
        "foaf:primaryTopic": {
            "@id": "#me",
            "@type": [ "foaf:Person", "schema:Person" ],
            "foaf:name": "Michael Thornburgh",
            "foaf:nick": "Mike"
        }
    }

Note that a successful `PATCH` could have alternatively answered
`204 No Content` and not sent a representation of the new state.

If supported, a resource's state is created or completely replaced by a `PUT`
request body's default graph.

If supported, an existing resource (and any sub-resources) is completely
removed by a `DELETE` of its URI.

It may be difficult or awkward to `PATCH` a complex resource, and in particular
to insert, modify, or remove deeply-nested triples, or to modify blank nodes.
It may be advantageous to factor complex resources into hierarchical sub-resources
with distinct URIs that can be `POST`ed, `PATCH`ed, `PUT`, or `DELETE`d
independently, and to avoid blank nodes.

The application and the shapes & semantics of the resources determine whether
the requested modifications are valid and allowed. If possible and appropriate,
successful responses to modifications **SHOULD** include an `ETag` for the
new state of the resource.

Problem Details
---------------
HTTP errors (status codes `4XX` & `5XX`) **MAY** have application-specific
response bodies to describe the problem with more specificity and in greater
detail than the status code alone conveys.

Error response bodies that are intended to be machine-readable **SHOULD** use
RDF and Terse JSON-LD, rather than an ad-hoc format or [RFC 9457][RFC9457].

A problem description is a subject having an `@type` of `api:Problem`, or a
subclass of it. To aid identifying the problem description without inferencing,
the problem description's `@type` **SHOULD** include both `api:Problem` as
well as the more specific class(es) of the problem.

To aid human diagnostics, implementations ought to include any `rdfs:comment`s
for the specific class of problem (particularly if its URI might not be readily
dereferenceable), as well as an `rdfs:comment` for this problem occurrence.

If the problem description is not a blank node, then its URI uniquely identifies
this specific occurrence of the problem, and if it is dereferenceable, these
problem details can be retrieved again from there, potentially only for a time.

Example describing a similar problem to the one shown in
[Section 3 of RFC 9457](https://www.rfc-editor.org/rfc/rfc9457#section-3):

    HTTP/1.1 403 Forbidden
    Content-Type: application/ld+json; profile="http://zenomt.com/ns/jsonld-terse http://zenomt.com/ns/terse-api"
    Date: Sun, 30 Mar 2025 17:44:12 GMT

    {
        "@context": {
            "@base": "https://store.example.com/",
            "api": "http://zenomt.com/ns/terse-api#",
            "ex": "http://example.com/ns#",
            "rdfs": "http://www.w3.org/2000/01/rdf-schema#"
        },
        "@id": "/accounts/12345/msgs/abc#the-problem",
        "http://www.w3.org/1999/02/22-rdf-syntax-ns#type": [
            { "@id": "api:Problem" },
            { "@id": "https://example.com/probs/out-of-credit", "rdfs:comment": "You do not have enough credit." }
        ],
        "rdfs:comment": "Your current balance is 30, but that costs 50.",
        "ex:balance": 30,
        "ex:account": [ { "@id": "/accounts/12345" }, { "@id": "/accounts/67890" } ]
    }

The response graph **MAY** include multiple problem descriptions if there were
multiple problems with the request, so long as the HTTP status code is
appropriate to all of the described problems.

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
  [REST]: https://roy.gbiv.com/pubs/dissertation/fielding_dissertation.pdf
  [RFC2119]: https://www.rfc-editor.org/rfc/rfc2119
  [RFC8174]: https://www.rfc-editor.org/rfc/rfc8174
  [RFC9110]: https://www.rfc-editor.org/rfc/rfc9110
  [RFC9457]: https://www.rfc-editor.org/rfc/rfc9457
  [N-Triples]: https://www.w3.org/TR/n-triples/
  [TERSE-API]: http://zenomt.com/ns/terse-api
  [HTTP-STATUS]: https://www.iana.org/assignments/http-status-codes/http-status-codes.xhtml
