// Copyright © 2024 Michael Thornburgh
// SPDX-License-Identifier: MIT

class com_zenomt_JSONLD_Terse {
	constructor(node, { documentUri, vocab, fallbackContext, maxDepth=64 } = {}) {
		this._nodes = new Map();
		this._literals = new Map();
		this._root = this.get(node ? this.merge(node, { documentUri, vocab, maxDepth, fallbackContext }) : null) ?? this._nodes.values().next().value;
	}

	merge(node, { documentUri, vocab, fallbackContext, maxDepth=64 } = {}) {
		let baseUri, prefixes;
		({ baseUri, prefixes, vocab } = this.constructor._resolveContext(documentUri, vocab, fallbackContext, {}));
		return this._basicMerge(node, { depth: 0, visited: new Map(), blankNodes: new Map(), prefixes, baseUri, vocab, maxDepth, literals: this._literals });
	}

	get(uriOrNode) { return this._nodes.get(uriOrNode) ?? (uriOrNode ? this._nodes.get(uriOrNode["@id"]) : null); }

	get nodes() { return new Set(this._nodes.values()) ; }

	get root() { return this._root; }
	set root(uriOrNode) { this._root = this.get(uriOrNode); }

	asTriples() {
		let nextBlank = 0;
		const blanks = new Map();
		const getId = node => node["@id"] ?? blanks.get(node) ?? blanks.set(node, "_:b" + nextBlank++).get(node);
		const valueObject = node => {
			if(Array.isArray(node))
				return node.map(valueObject);
			if("@list" in node)
				return { "@list": node["@list"].map(valueObject) };
			if("@value" in node)
				return this.constructor._adaptLiteral(node);
			return { "@id": getId(node) };
		}

		const rv = [];
		for(const node of this.nodes)
		{
			const subject = getId(node);
			for(const [predicate, values] of Object.entries(node))
				if(predicate[0] != "@")
					for(const value of values)
						rv.push({ subject, predicate, _object: valueObject(value) });
		}

		return rv;
	}

	asTree(root, { noArray, base, rawLiteral } = {}) {
		root = root ? this.get(root) : this.root;
		base = base ? (new URL("", base)) : null;
		const basePath = base ? (new URL(".", base)) : null;
		const baseRoot = base ? (new URL("/", base)) : null;
		const context = { visited: new Map(), nextBlank: 0, noArray, base, basePath, baseRoot, rawLiteral };

		const rv =  root ? this._basicAsTree(root, context) : {};

		const included = [];
		for(const node of this.nodes)
			if(!context.visited.has(node))
				included.push(this._basicAsTree(node, context));
		if(included.length > 0)
			rv["@included"] = included;

		return rv;
	}

	asJSON(root, { noArray, indent, base, rawLiteral } = {}) { return JSON.stringify(this.asTree(root, { noArray, base, rawLiteral }), null, indent); }

	static effectiveRootContext(node, { documentUri, vocab, fallbackContext } = {}) {
		let baseUri, prefixes;
		({ baseUri, prefixes, vocab } = this._resolveContext(documentUri, vocab, fallbackContext, {}));
		({ baseUri, prefixes, vocab } = this._resolveContext(baseUri, vocab, node?.["@context"], prefixes));
		prefixes["@base"] = baseUri?.href ?? baseUri;
		prefixes["@vocab"] = vocab;
		return prefixes;
	}

	_makeRelative(uri, { base, basePath, baseRoot }) {
		if((!base) || (base.origin != uri.origin))
			return uri.href;
		if((new URL("", uri)).href == base.href)
			return uri.hash;
		if((new URL(".", uri)).href.startsWith(basePath.href))
			return uri.href.substring(basePath.href.length) || ".";
		return uri.href.substring(baseRoot.href.length - 1);
	}

	_basicAsTree(node, context) {
		if(Array.isArray(node))
			return ((node.length == 1) && context.noArray) ? this._basicAsTree(node[0], context) : node.map(v => this._basicAsTree(v, context));
		if("@list" in node)
			return { "@list": node["@list"].map(v => this._basicAsTree(v, context)) };
		if("@value" in node)
			return this.constructor._adaptLiteral(node, { rawLiteral: context.rawLiteral } );

		const item = context.visited.get(node);
		if(item)
		{
			if(!("@id" in item))
				item["@id"] = "_:b" + context.nextBlank++;
			return { "@id": item["@id"] };
		}

		const rv = {};
		context.visited.set(node, rv);

		for(const [key, value] of Object.entries(node))
			rv[key] = "@id" == key ? this._makeRelative(new URL(value), context) : this._basicAsTree(value, context);

		return rv;
	}

	_basicMerge(node, { depth, visited, blankNodes, prefixes, baseUri, vocab, maxDepth, literals }) {
		if(++depth > maxDepth)
			throw new RangeError("nested too deep");

		({ baseUri, prefixes, vocab } = this.constructor._resolveContext(baseUri, vocab, node?.["@context"], prefixes));
		const context = { depth, visited, blankNodes, prefixes, baseUri, vocab, maxDepth, literals };

		if(Array.isArray(node))
			return node.map(v => this._basicMerge(v, context));
		if(this.constructor._isPrimitive(node))
			return this.constructor._adaptLiteral({ "@value": node ?? null }, context);
		if("@list" in node)
			return { "@list": Array.isArray(node["@list"]) ? node["@list"].map(v => this._basicMerge(v, context)) : [] };
		if("@value" in node)
			return this.constructor._adaptLiteral(node, context);
		if(visited.has(node))
			return visited.get(node);

		const uri = this.constructor._expandUri(node["@id"], false, context);
		const isBlank = (typeof(uri) != "string") || uri.substring(0, 2) == "_:";
		const rv = (isBlank ? blankNodes.get(uri) : this._nodes.get(uri)) ?? {};
		if(!isBlank)
			rv["@id"] = uri;
		else if(uri)
			blankNodes.set(uri, rv);
		this._nodes.set(isBlank ? rv : uri, rv);
		visited.set(node, rv);

		for(let [key, value] of Object.entries(node))
		{
			if("@type" == key)
			{
				key = "http://www.w3.org/1999/02/22-rdf-syntax-ns#type";
				value = (Array.isArray(value) ? value : [value]).map(v => ({ "@id": this.constructor._expandUri(v, !!context.vocab, context) }));
			}

			if("@included" == key)
				this._basicMerge(value, context);
			else if(key[0] != "@")
			{
				key = this.constructor._expandUri(key, true, context);
				if(key)
					rv[key] = Array.from(new Set((rv[key] ?? []).concat((Array.isArray(value) ? value : [value]).map(v => this._basicMerge(v, context)))));
			}
		}

		return rv;
	}

	static _resolveUri(uri, baseUri) { return uri ? (new URL(uri, baseUri)) : baseUri; }

	static _resolveVocab(context, vocab, baseUri) {
		vocab = context?.["@vocab"] ?? vocab;
		return (vocab != null) ? (new URL(vocab, baseUri)).href : null;
	}

	static _overlayPrefixes(base, overlay, baseUri) {
		if(overlay == null)
			return base;
		const rv = {};
		for(const [key, value] of Object.entries(base))
			rv[key] = value;
		for(const [key, value] of Object.entries(overlay ?? {}))
			if(key[0] != "@")
				rv[key] = (typeof(value) == "string") ? (new URL(value, baseUri)).href : null;
		return rv;
	}

	static _expandUri(uri, isKey, { prefixes, vocab, baseUri }) {
		if(typeof(uri) != "string")
			return null;
		if(uri == "@json")
			return "http://www.w3.org/1999/02/22-rdf-syntax-ns#JSON";
		const colonPosition = uri.indexOf(":");
		if(colonPosition >= 0)
		{
			const prefix = uri.substring(0, colonPosition);
			return (typeof(prefixes[prefix]) == "string") ? prefixes[prefix] + uri.substring(colonPosition + 1) : uri;
		}
		return prefixes[uri] ?? (isKey ? (vocab ? vocab + uri : null) : (new URL(uri, baseUri)).href);
	}

	static _adaptLiteral(node, { prefixes = {}, baseUri, literals, rawLiteral } = {}) {
		if(rawLiteral && ["@type", "@language", "@direction"].every(key => !(key in node)) && this._isPrimitive(node["@value"]))
			return structuredClone(node["@value"]);
		const rv = {};
		[ "@value", "@language", "@direction" ].forEach(key => { if(key in node) rv[key] = structuredClone(node[key]) });
		if(typeof(node["@type"]) == "string")
			rv["@type"] = this._expandUri(node["@type"], false, { prefixes, baseUri });
		const valueKey = JSON.stringify([rv["@value"], rv["@type"], rv["@language"]]);
		return literals ? literals.get(valueKey) ?? (literals.set(valueKey, rv), rv) : rv;
	}

	static _isPrimitive(value) { return (typeof(value) != "object") || (null == value); }

	static _resolveContext(baseUri, vocab, context, prefixes) {
		baseUri = this._resolveUri(context?.["@base"], baseUri);
		prefixes = this._overlayPrefixes(prefixes, context, baseUri);
		vocab = this._resolveVocab(context, vocab, baseUri);
		return { baseUri, prefixes, vocab };
	}
}
