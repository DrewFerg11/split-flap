"""Minimal s-expression reader for KiCad netlists (kicadsexpr format)."""
import re

_TOK = re.compile(r'\s*(\(|\)|"(?:[^"\\]|\\.)*"|[^\s()"]+)')


def parse(text):
    stack, cur = [], []
    for m in _TOK.finditer(text):
        tok = m.group(1)
        if tok == "(":
            stack.append(cur)
            cur = []
        elif tok == ")":
            done = cur
            cur = stack.pop()
            cur.append(done)
        elif tok.startswith('"'):
            cur.append(tok[1:-1].replace('\\"', '"').replace("\\\\", "\\"))
        else:
            cur.append(tok)
    return cur[0]


def find(node, key):
    """First child list whose head is key."""
    for c in node[1:]:
        if isinstance(c, list) and c and c[0] == key:
            return c
    return None


def find_all(node, key):
    return [c for c in node[1:] if isinstance(c, list) and c and c[0] == key]


def val(node, key, default=None):
    c = find(node, key)
    return c[1] if c and len(c) > 1 else default


def read_netlist(path):
    """Return (components, nets).

    components: {ref: {"value", "footprint", "fields": {name: value}, "dnp": bool}}
    nets: {net_name: [(ref, pin), ...]}
    """
    root = parse(open(path, encoding="utf-8").read())
    comps = {}
    for c in find_all(find(root, "components"), "comp"):
        ref = val(c, "ref")
        fields = {}
        fl = find(c, "fields")
        if fl:
            for f in find_all(fl, "field"):
                name = val(f, "name")
                fields[name] = f[-1] if isinstance(f[-1], str) else ""
        dnp = any(val(p, "name") == "dnp" for p in find_all(c, "property"))
        comps[ref] = {"value": val(c, "value", ""), "footprint": val(c, "footprint", ""),
                      "fields": fields, "dnp": dnp, "uuid": val(c, "tstamps", "")}
    nets = {}
    for n in find_all(find(root, "nets"), "net"):
        name = val(n, "name")
        nets[name] = [(val(nd, "ref"), val(nd, "pin")) for nd in find_all(n, "node")]
    return comps, nets
