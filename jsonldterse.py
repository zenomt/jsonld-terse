# Copyright © 2025 Michael Thornburgh
# SPDX-License-Identifier: MIT

from urllib.parse import urlsplit, urljoin, urldefrag
import copy
import json

class JSONLD_Terse:
	def __init__(self, node = None, documentUri = None, vocab = None, fallbackContext = None, maxDepth = 64):
		self._nodes = {}
		self._uris = {}
		self._literals = {}
		self._root = self.get(self.merge(node, documentUri=documentUri, vocab=vocab, maxDepth=maxDepth, fallbackContext=fallbackContext) if node else None) or self._first(self._nodes.values())

	def merge(self, node, documentUri=None, vocab=None, fallbackContext=None, maxDepth=64):
		baseUri, prefixes, vocab = self._resolveContext(documentUri, vocab, fallbackContext, {})
		return self._basicMerge(node, depth=0, visited={}, blankNodes={}, prefixes=prefixes, baseUri=baseUri, vocab=vocab, maxDepth=maxDepth, literals=self._literals)

	def get(self, uriOrNode):
		if type(uriOrNode) == str:
			return self._uris.get(uriOrNode, None)
		if type(uriOrNode) == dict:
			if id(uriOrNode) in self._nodes:
				return uriOrNode
			return self._uris.get(uriOrNode.get("@id", None), None)

	@property
	def nodes(self):
		return list(self._nodes.values())

	@property
	def root(self):
		return self._root or self._first(self._nodes.values())

	@root.setter
	def root(self, uriOrNode):
		self._root = self.get(uriOrNode)

	def asTriples(self):
		nextBlank = 0
		blanks = {}
		def getId(node):
			nonlocal nextBlank
			rv = node.get("@id", None) or blanks.get(id(node), None)
			if rv != None:
				return rv
			name = "_:b" + str(nextBlank)
			nextBlank += 1
			blanks[id(node)] = name
			return name
		def valueObject(node):
			if type(node) == list:
				return list(map(valueObject, node))
			if "@list" in node:
				return { "@list": list(map(valueObject, node["@list"])) }
			if "@value" in node:
				return self._adaptLiteral(node)
			return { "@id": getId(node) }
		rv = []
		for node in self.nodes:
			subject = getId(node)
			for predicate, values in node.items():
				if predicate[:1] != "@":
					for value in values:
						rv.append(dict(subject=subject, predicate=predicate, _object=valueObject(value)))
		return rv

	def asTree(self, root = None, noArray = False, base = None, rawLiteral = False):
		root = self.get(root) if root else self.root
		base = self._resolveUri("", base) if base is not None else None
		basePath = self._resolveUri(".", base) if base is not None else None
		baseRoot = self._resolveUri("/", base) if base is not None else None
		ctx = dict(visited={}, nextBlank=0, noArray=noArray, base=base, basePath=basePath, baseRoot=baseRoot, rawLiteral=rawLiteral)
		rv = self._basicAsTree(root, ctx) if root is not None else {}
		included = []
		for ident, node in self._nodes.items():
			if (ident not in ctx["visited"]) and any(map(lambda k: k[:1] != "@", node.keys())):
				included.append(self._basicAsTree(node, ctx))
		if len(included):
			rv["@included"] = included
		return rv

	def asJSON(self, root = None, indent = None, separators = None, noArray = False, base = None, rawLiteral = False):
		return json.dumps(self.asTree(root, noArray=noArray, base=base, rawLiteral=rawLiteral), indent=indent, separators=separators)

	def select(self, s = None, p = None, o = None, literal = None, nodes = None, column = None, filter = None):
		rv = []
		querySubjectNode = self.get(s)
		queryPredicateNode = self.get(p)
		queryObjectNode = self.get(o)
		nodes = nodes if nodes is not None else ([querySubjectNode] if s is not None else self._nodes.values())
		literal = ({ "@value": literal } if self._isPrimitive(literal) else literal) if literal is not None else None
		if (s is not None and querySubjectNode is None) or (p is not None and queryPredicateNode is None) or (o is not None and queryObjectNode is None):
			return rv
		queryPredicateUri = queryPredicateNode.get("@id", None) if queryPredicateNode is not None else None
		for subject in nodes:
			if querySubjectNode is not None and subject is not querySubjectNode:
				continue
			for key, values in (([(queryPredicateUri, subject.get(queryPredicateUri, []))]) if p is not None else subject.items()):
				if key[:1] != "@":
					predicate = queryPredicateNode or self.get(key)
					for _object in values:
						if queryObjectNode is not None and _object != queryObjectNode:
							continue
						if literal is not None:
							if ("@value" not in _object) or any(map(lambda k: (k in literal) and literal[k] != _object.get(k, None), ["@value", "@language", "@direction", "@type"])):
								continue
						if filter is not None and not filter(subject, predicate, _object):
							continue
						rv.append(dict(subject=subject, predicate=predicate, _object=_object))
		return self._unique(map(lambda each: each.get(column, None), rv)) if column else rv

	@classmethod
	def effectiveRootContext(cls, node, documentUri = None, vocab = None, fallbackContext = None):
		baseUri, prefixes, vocab = cls._resolveContext(documentUri, vocab, fallbackContext, {})
		baseUri, prefixes, vocab = cls._resolveContext(baseUri, vocab, node.get("@context", None) if node else None, prefixes)
		if baseUri:
			prefixes["@base"] = baseUri
		if vocab:
			prefixes["@vocab"] = vocab
		return prefixes

	def _makeRelative(self, uri, base, basePath, baseRoot, **unused):
		if not base:
			return uri
		uri_split = urlsplit(uri)
		base_split = urlsplit(base)
		if uri_split.scheme != base_split.scheme or uri_split.netloc != base_split.netloc:
			return uri
		if urldefrag(uri)[0] == base:
			return ("#" if uri_split.fragment or uri[-1:] == "#" else "") + uri_split.fragment
		if self._resolveUri(".", uri).startswith(basePath):
			return uri[len(basePath):] or "."
		return uri[len(baseRoot) - 1:]

	def _basicAsTree(self, node, ctx):
		if type(node) == list:
			return self._basicAsTree(node[0], ctx) if len(node) == 1 and ctx["noArray"] else list(map(lambda v: self._basicAsTree(v, ctx), node))
		if "@list" in node:
			return { "@list": list(map(lambda v: self._basicAsTree(v, ctx), node["@list"])) }
		if "@value" in node:
			return self._adaptLiteral(node, rawLiteral=ctx["rawLiteral"])
		item = ctx["visited"].get(id(node))
		if item is not None:
			if "@id" not in item:
				item["@id"] = "_:b" + str(ctx["nextBlank"])
				ctx["nextBlank"] += 1
			return { "@id": item["@id"] }
		rv = {}
		ctx["visited"][id(node)] = rv
		for key, value in node.items():
			rv[key] = self._makeRelative(value, **ctx) if key == "@id" else self._basicAsTree(value, ctx)
		return rv

	def _basicMerge(self, node, depth, visited, blankNodes, prefixes, baseUri, vocab, maxDepth, literals):
		depth += 1
		if depth > maxDepth:
			raise RecursionError("nested too deep")

		baseUri, prefixes, vocab = self._resolveContext(baseUri, vocab, node.get("@context", None) if type(node) == dict else None, prefixes)
		ctx = dict(depth=depth, visited=visited, blankNodes=blankNodes, prefixes=prefixes, baseUri=baseUri, vocab=vocab, maxDepth=maxDepth, literals=literals)

		if type(node) == list:
			return list(map(lambda v: self._basicMerge(v, **ctx), node))
		if self._isPrimitive(node):
			return self._adaptLiteral({"@value": node}, **ctx)
		if "@list" in node:
			return { "@list": list(map(lambda v: self._basicMerge(v, **ctx), node["@list"])) if type(node["@list"]) == list else [] }
		if "@value" in node:
			return self._adaptLiteral(node, **ctx)
		if id(node) in visited:
			return visited[id(node)]

		uri = self._expandUri(node.get("@id", None), False, **ctx)
		isBlank = (type(uri) != str) or uri[:2] == "_:"
		rv = blankNodes.get(uri, {}) if isBlank else self._uris.get(uri, {})
		if not isBlank:
			rv["@id"] = uri
		elif uri:
			blankNodes[uri] = rv
		self._nodes[id(rv)] = rv
		if not isBlank:
			self._uris[uri] = rv
		visited[id(node)] = rv

		for key, value in node.items():
			if key == "@type":
				key = "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"
				value = list(map(lambda v: { "@id": self._expandUri(v, isKey = bool(vocab), **ctx) }, value if type(value) == list else [value]))

			if key == "@included":
				self._basicMerge(value, **ctx)
			elif key[:1] != "@":
				key = self._expandUri(key, True, **ctx)
				if key:
					if key not in self._uris:
						keyNode = { "@id": key }
						self._uris[key] = keyNode
						self._nodes[id(keyNode)] = keyNode
					rv[key] = self._unique(rv.get(key, []) + list(map(lambda v: self._basicMerge(v, **ctx), value if type(value) == list else [value])))

		return rv

	@staticmethod
	def _resolveUri(uri, baseUri):
		if uri is not None and not baseUri:
			return uri
		if uri is not None:
			rv = urldefrag(baseUri)[0] if uri == '' else urljoin(baseUri, uri)
			if uri[-1:] == "#" and rv[-1:] != "#":
				# bug in urljoin, empty fragment is distinct from no fragment!
				rv += "#"
			return rv
		return baseUri

	@classmethod
	def _resolveVocab(cls, context, vocab, baseUri):
		vocab = context.get("@vocab", vocab) if context else vocab
		return cls._resolveUri(vocab, baseUri) if vocab != None else None

	@classmethod
	def _overlayPrefixes(cls, base, overlay, baseUri):
		if overlay == None:
			return base
		rv = dict(base)
		for key, value in (overlay or {}).items():
			if key[:1] != "@":
				rv[key] = cls._resolveUri(value, baseUri) if type(value) == str else None
		return rv

	@classmethod
	def _expandUri(cls, uri, isKey = False, prefixes = {}, vocab = None, baseUri = None, **unused):
		if type(uri) != str:
			return None
		if uri == "@json":
			return "http://www.w3.org/1999/02/22-rdf-syntax-ns#JSON"
		colonPosition = uri.find(":")
		if colonPosition >= 0:
			prefix = prefixes.get(uri[:colonPosition], None)
			return prefix + uri[colonPosition + 1:] if type(prefix) == str and uri.find("://") != colonPosition else uri
		return prefix if (prefix := prefixes.get(uri, None)) else ((vocab + uri if vocab else None) if isKey else cls._resolveUri(uri, baseUri))

	@classmethod
	def _adaptLiteral(cls, node, prefixes = None, baseUri = None, literals = None, rawLiteral = False, **unused):
		prefixes = prefixes or {}
		if rawLiteral and all(map(lambda key : key not in node, ["@type", "@language", "@direction"])) and cls._isPrimitive(node["@value"]):
			return copy.deepcopy(node["@value"])
		rv = {}
		for key in ["@value", "@language", "@direction"]:
			if key in node:
				rv[key] = copy.deepcopy(node[key])
		if type(node.get("@type", None)) == str:
			rv["@type"] = cls._expandUri(node["@type"], False, prefixes=prefixes, baseUri=baseUri)
		if literals is not None:
			valueKey = json.dumps([rv["@value"], rv.get("@type", None), rv.get("@language", None)])
			if valueKey in literals:
				return literals.get(valueKey)
			literals[valueKey] = rv
		return rv

	@staticmethod
	def _isPrimitive(value):
		return type(value) not in [dict, list]

	@classmethod
	def _resolveContext(cls, baseUri, vocab, context, prefixes):
		baseUri = cls._resolveUri(context.get("@base", None) if context else None, baseUri)
		prefixes = cls._overlayPrefixes(prefixes, context, baseUri)
		vocab = cls._resolveVocab(context, vocab, baseUri)
		return baseUri, prefixes, vocab

	@staticmethod
	def _unique(iterable):
		seen = set()
		rv = []
		for each in iterable:
			if id(each) not in seen:
				seen.add(id(each))
				rv.append(each)
		return rv

	@staticmethod
	def _first(iterable):
		for i in iterable:
			return i
