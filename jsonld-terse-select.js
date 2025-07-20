// Copyright © 2025 Michael Thornburgh
// SPDX-License-Identifier: MIT
// A mix-in for com_zenomt_JSONLD_Terse to provide basic querying of the graph.

com_zenomt_JSONLD_Terse.prototype.select = function({s, p, o, literal, nodes, column, filter} = {}) {
	const rv = [];
	const querySubjectNode = this.get(s);
	const queryObjectNode = this.get(o);
	nodes = nodes ?? (s ? [querySubjectNode] : this.nodes);
	literal = (literal != null) ? (this.constructor._isPrimitive(literal) ? { "@value": literal } : literal) : null;

	if((s && !querySubjectNode) || (p && !this.get(p)) || (o && !queryObjectNode))
		return rv;

	for(const subject of nodes)
	{
		if((querySubjectNode && (subject != querySubjectNode)))
			continue;

		for(const [key, values] of (p ? (subject[p] ? [[p, subject[p] ?? []]] : []) : Object.entries(subject)))
		{
			if(key[0] != "@")
			{
				const predicate = this.get(key);

				for(const _object of values)
				{
					if(queryObjectNode && (_object != queryObjectNode))
						continue;

					if(literal)
						if((! "@value" in _object) || ["@value", "@language", "@direction", "@type"].some(k => ((k in literal) && literal[k] != _object[k])))
							continue;

					if(filter && !filter(subject, predicate, _object))
						continue;

					rv.push({ subject, predicate, _object });
				}
			}
		}
	}

	return column ? Array.from(new Set(rv.map(each => each[column]))) : rv;
}
