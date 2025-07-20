// Copyright © 2025 Michael Thornburgh
// SPDX-License-Identifier: MIT
// A mix-in to com_zenomt_JSONLD_Terse to provide basic querying of the graph.

com_zenomt_JSONLD_Terse.prototype.select = function({s, p, o, literal, nodes, filter = (s,p,o) => true} = {}) {
	const rv = [];
	const allNodes = this.nodes;
	const querySubjectNode = this.get(s);
	const queryPredicateNode = this.get(p);
	const queryObjectNode = this.get(o);
	nodes = nodes ?? (s ? [querySubjectNode] : allNodes);
	literal = (literal != null) ? (this.constructor._isPrimitive(literal) ? { "@value": literal } : literal) : null;

	if((s && !querySubjectNode) || (p && !queryPredicateNode) || (o && !queryObjectNode))
		return rv;

	for(const subject of nodes)
	{
		if((querySubjectNode && (subject != querySubjectNode)) || (! subject in allNodes))
			continue;

		for(const [key, values] of Object.entries(subject))
		{
			if(key[0] != "@")
			{
				const predicate = this.get(key);
				if(queryPredicateNode && (predicate != queryPredicateNode))
					continue;

				for(const value of values)
				{
					if(queryObjectNode && (value != queryObjectNode))
						continue;

					if(literal)
						if((! "@value" in value) || ["@value", "@language", "@direction", "@type"].some(k => ((k in literal) && literal[k] != value[k])))
							continue;

					if(filter && !filter(subject, predicate, value))
						continue;

					rv.push({ subject, predicate, _object: value });
				}
			}
		}
	}

	return rv;
}

com_zenomt_JSONLD_Terse.subjects = triples => new Set(triples.map(each => each["subject"]));
com_zenomt_JSONLD_Terse.predicates = triples => new Set(triples.map(each => each["predicate"]));
com_zenomt_JSONLD_Terse.objects = triples => new Set(triples.map(each => each["_object"]));
