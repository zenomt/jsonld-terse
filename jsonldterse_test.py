#! /usr/bin/env python3 --

from jsonldterse import JSONLD_Terse
import json
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('-r', '--raw', default=False, action="store_true", help="show raw input")
parser.add_argument('-t', '--triples', default=False, action="store_true", help="show triples of parsed graph")
parser.add_argument('-j', '--json', default=False, action="store_true", help="show JSON tree of parsed graph")
parser.add_argument('-f', '--only', default=None, help="only parse this test file")
parser.add_argument('--relative', default=False, action="store_true", help="generate relative URIs in JSON tree")
parser.add_argument('-v', '--verbose', default=0, action='count')

args = parser.parse_args()

def test_example(graph):
	assert (me := graph.get("https://zenomt.github.io/jsonld-terse/card#me"))
	assert graph.root == me
	assert len(me['http://www.w3.org/1999/02/22-rdf-syntax-ns#type']) == 2
	assert len(me['http://xmlns.com/foaf/0.1/name']) == 1
	assert len(me['http://xmlns.com/foaf/0.1/name'][0]) == 2
	assert len(me) == 6
	assert (up := graph.get("https://zenomt.github.io/"))
	assert up["http://www.example.com/http-ns#bif"][0]["@value"] == "my subject is relative up"
	assert (down := graph.get("https://zenomt.github.io/jsonld-terse/subdir/foo#"))
	assert down["http://www.example.com/http-ns#bif"][0]["@value"] == "my subject is relative down"
	tree = graph.asTree(root=up, noArray = True, rawLiteral = True, base = "https://zenomt.github.io/jsonld-terse/example.jsonld")
	assert tree["@id"] == "/"
	assert tree["http://www.example.com/http-ns#bif"] == "my subject is relative up"
	tree = graph.asTree(root=down, noArray = True, rawLiteral = True, base = "https://zenomt.github.io/jsonld-terse/example.jsonld")
	assert tree["@id"] == "subdir/foo#"

def test_example2(graph):
	assert (person := graph.root)
	assert person['https://schema.org/name']
	assert person['https://schema.org/name'][0]["@value"] == "Manu Sporny"
	assert graph.get(person['https://schema.org/url'][0])
	assert graph.get(person['https://schema.org/url'][0]) == graph.get(person['https://schema.org/url'][0]["@id"])

def test_example3(graph):
	assert (node := graph.get("https://zenomt.github.io/jsonld-terse/example3.jsonld#test"))
	assert (five := node['http://example.com/ns#five'])
	assert len(five) == 1
	assert len(five[0]["@list"]) == 3
	assert (prims := node["http://example.com/ns#primitives"])
	# order should be preserved even though that's not a thing in RDF, including through a uniquing merge
	assert len(prims) == 6
	assert prims[0]["@value"] is None
	assert prims[1]["@value"] is True
	assert prims[2]["@value"] is False
	assert prims[3]["@value"] == 3
	assert prims[4]["@value"] == "literal"
	assert prims[5]["@value"] == -4

def test_example4(graph):
	assert (node := graph.root)
	assert len(node["http://example.com/ns#one"]) == 2
	assert len(node["http://example.com/ns#one"][0]) == 2
	assert len(node["http://example.com/ns#one"][0][0]) == 2
	assert len(node["http://example.com/ns#one"][1]) == 4
	assert len(node["three:"]) == 1
	assert (two := node["http://example.com/ns#two"])
	assert two[0]["@type"] == "http://www.w3.org/1999/02/22-rdf-syntax-ns#JSON"
	assert len(two[0]["@value"]) == 5
	assert two[2]["@value"]["@id"] == "#not-a-uri"

def test_example5(graph):
	assert (node := graph.get("https://zenomt.github.io/jsonld-terse/example5.jsonld#1"))
	assert node["urn:private:pred"][0]["urn:private:pred"][0] == node
	assert (priv1 := graph.get("urn:private:name:1"))
	assert priv1["urn:private:pred"][0] == graph.get("urn:private:name:2")
	assert priv1["urn:private:pred"][0]["urn:private:pred"][0]["urn:private:pred"][0] == priv1
	assert priv1 != graph.get("urn:private:name:2")

def test_example6(graph):
	assert (node := graph.get("https://zenomt.github.io/jsonld-terse/example6.jsonld#test"))
	assert node == graph.root
	assert (blanks := node["http://example.com/ns#blanks"][0]["@list"])
	assert len(blanks) == 5
	assert blanks[0]["http://example.com/ns#knows"][0] == blanks[1]
	blankReg = blanks[3]
	assert blankReg["http://example.com/ns#knows"][1] == blankReg
	assert blankReg["http://example.com/ns#knows"][2] == blanks[1]
	assert "@id" not in blankReg
	assert graph.get(blankReg) == blankReg
	assert graph.get(dict(blankReg)) != blankReg

def test_example8(graph):
	assert (node := graph.get("http://example.com/ns"))
	assert node["http://www.w3.org/1999/02/22-rdf-syntax-ns#type"][0]["@id"] == "http://www.w3.org/2002/07/owl#Ontology"
	assert (res := graph.get("http://example.com/ns#Resource"))
	assert res["http://www.w3.org/1999/02/22-rdf-syntax-ns#type"][0]["@id"] == "http://www.w3.org/2000/01/rdf-schema#Class"
	assert res["http://www.w3.org/2000/01/rdf-schema#subClassOf"][0] == graph.get("http://zenomt.com/ns/terse-api#Resource")
	assert (item := graph.get("http://example.com/ns#Item"))
	assert item["http://www.w3.org/2000/01/rdf-schema#subClassOf"][0] == res

def run_file_tests():
	"""try the samples to make sure they don't cause a crash"""
	test_files = [
		( "example.jsonld", "https://zenomt.github.io/jsonld-terse/example.jsonld", test_example ),
		( "example2.jsonld", "https://zenomt.github.io/jsonld-terse/example2.jsonld", test_example2 ),
		( "example3.jsonld", "https://zenomt.github.io/jsonld-terse/example3.jsonld", test_example3 ),
		( "example4.jsonld", "https://zenomt.github.io/jsonld-terse/example4.jsonld", test_example4 ),
		( "example5.jsonld", "https://zenomt.github.io/jsonld-terse/example5.jsonld", test_example5 ),
		( "example6.jsonld", "https://zenomt.github.io/jsonld-terse/example6.jsonld", test_example6 ),
		( "example8.jsonld", "https://zenomt.github.io/jsonld-terse/example8.jsonld", test_example8 ),
		( "example9.jsonld", "https://zenomt.github.io/jsonld-terse/example9.jsonld", None ),
		( "api.jsonld", "http://zenomt.com/ns/terse-api", None )
	]
	for name, baseUri, tester in test_files:
		with open(name, "r", encoding="utf-8") as f:
			if args.only is not None and name != args.only:
				continue
			print(f"file:{name}  base:{baseUri}")
			raw = f.read()
			if args.verbose or args.raw: print("raw", raw)
			node = json.loads(raw)
			if args.verbose > 1: print("node", node)
			graph = JSONLD_Terse(node, documentUri=baseUri)
			if args.verbose > 1: print(f"graph: {graph._nodes}")
			if tester:
				tester(graph)
			tree_json = graph.asJSON(indent=4, noArray=True, rawLiteral=True, base=(baseUri if args.relative else None))
			triples = graph.asTriples()
			if args.verbose or args.json:
				print("tree\n", tree_json)
			if args.verbose or args.triples:
				print("triples:")
				for each in triples:
					print(f"{each['subject']}  {each['predicate']}  {json.dumps(each['_object'])}")

def test_effectiveRootContext():
	name = "example.jsonld"
	if args.only is not None and name != args.only:
		return
	print("\ntest_effectiveRootContext example.jsonld")
	with open(name, "r", encoding="utf-8") as f:
		raw = f.read()
		doc = json.loads(raw)
		effectiveRootContext = JSONLD_Terse.effectiveRootContext(doc, documentUri="https://zenomt.github.io/jsonld-terse/example.jsonld")
		if args.verbose: print("raw", raw, "\n", "effectiveRootContext", json.dumps(effectiveRootContext, indent=4))
		graph = JSONLD_Terse(doc["@metadata"], fallbackContext=effectiveRootContext)
		if args.verbose: print("metadata graph", graph.asJSON(indent=4, noArray=True, rawLiteral=True))
		assert (node := graph.get("https://zenomt.github.io/jsonld-terse/example.jsonld?cursor=2"))
		assert node["http://www.w3.org/1999/02/22-rdf-syntax-ns#type"][0]["@id"] == "http://zenomt.com/ns/terse-api#Page"
		assert node["http://zenomt.com/ns/terse-api#prevPage"][0] == graph.get("https://zenomt.github.io/jsonld-terse/example.jsonld?cursor=1")
		assert node["http://zenomt.com/ns/terse-api#nextPage"][0] == graph.get("https://zenomt.github.io/jsonld-terse/example.jsonld?cursor=3")
		assert node["http://zenomt.com/ns/terse-api#pageOf"][0] == graph.get("https://zenomt.github.io/jsonld-terse/example.jsonld")

def test_select():
	name = "example.jsonld"
	if args.only is not None and name != args.only:
		return
	print("\ntest_select example.jsonld")
	with open(name, "r", encoding="utf-8") as f:
		raw = f.read()
		doc = json.loads(raw)
		graph = JSONLD_Terse(doc, documentUri="https://zenomt.github.io/jsonld-terse/example.jsonld")
		assert len(graph.select(s="https://zenomt.github.io/jsonld-terse/card#me")) == 6
		assert len(graph.select(s=graph.get("https://zenomt.github.io/jsonld-terse/card#me"))) == 6
		assert len(graph.select(p="http://www.w3.org/1999/02/22-rdf-syntax-ns#type")) == 4
		assert len(graph.select(p=graph.get("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"))) == 4
		assert len(graph.select(s="https://zenomt.github.io/jsonld-terse/card#me", p="http://www.w3.org/1999/02/22-rdf-syntax-ns#type")) == 2
		assert len(graph.select(s="http://www.w3.org/1999/02/22-rdf-syntax-ns#type")) == 0
		assert len(graph.select(s="http://www.notfound")) == 0
		assert graph.select(literal={"@language": "en-us"}, column="subject")[0] == graph.get("https://zenomt.github.io/jsonld-terse/card#me")
		assert graph.select(o="http://xmlns.com/foaf/0.1/PersonalProfileDocument", column="subject")[0] == graph.get("https://zenomt.github.io/jsonld-terse/example.jsonld")
		assert graph.select(p="http://xmlns.com/foaf/0.1/depiction")[0]["_object"]["@id"] == "https://zenomt.zenomt.com/mike-2017.jpg"
		assert graph.select(o=graph.get("https://schema.org/Person"), column="subject")[0] == graph.get("https://zenomt.github.io/jsonld-terse/card#me")
		assert graph.select(p="http://www.w3.org/1999/02/22-rdf-syntax-ns#type", o="https://schema.org/Corporation")[0]["subject"]["https://schema.org/name"][0]["@value"] == "Example Corp."
		assert graph.select(p="http://www.w3.org/1999/02/22-rdf-syntax-ns#type", o="https://schema.org/Corporation")[0]["subject"] == graph.select(literal="Example Corp.", column="subject")[0]
		assert len(graph.select(filter=(lambda s,p,o: o.get("@value", None) == "Mike"))) == 1

if __name__ == "__main__":
	run_file_tests()
	test_effectiveRootContext()
	test_select()
