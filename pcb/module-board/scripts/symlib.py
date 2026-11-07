"""Read symbols from KiCad's stock libraries: flattened definitions (for lib_symbols) and pin geometry.

Pin geometry is taken from the library itself, so the schematic generator never carries a
hand-copied pin table that could drift from the symbol.
"""
import os, re

KICAD_SYM = r"C:/Program Files/KiCad/10.0/share/kicad/symbols"
HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_LIBS = {}          # nickname -> path, filled by the generator for project-local libs


def block_at(t, i):
    d = 0
    j = i
    while True:
        c = t[j]
        if c == '(':
            d += 1
        elif c == ')':
            d -= 1
            if d == 0:
                return t[i:j + 1]
        j += 1


def children(blk):
    """Top-level child blocks of an s-expression block (skips the head atoms)."""
    out, i, d = [], 1, 0
    while i < len(blk) - 1:
        if blk[i] == '(':
            b = block_at(blk, i)
            out.append(b)
            i += len(b)
        else:
            i += 1
    return out


_cache = {}


def _lib_text(nick):
    path = PROJECT_LIBS.get(nick) or os.path.join(KICAD_SYM, nick + ".kicad_sym")
    if path not in _cache:
        _cache[path] = open(path, encoding="utf-8").read()
    return _cache[path]


def raw_symbol(nick, name):
    t = _lib_text(nick)
    m = re.search(r'\n\t\(symbol "' + re.escape(name) + r'"\s', t)
    if not m:
        raise KeyError(f"{nick}:{name}")
    return block_at(t, m.start() + 2)


def flat_symbol(lib_id):
    """Symbol block named 'nick:name', with any (extends) resolved, ready for lib_symbols."""
    nick, name = lib_id.split(":", 1)
    blk = raw_symbol(nick, name)
    e = re.search(r'\(extends "([^"]+)"\)', blk)
    if e:
        base_name = e.group(1)
        base = raw_symbol(nick, base_name)
        derived_props = [c for c in children(blk) if c.startswith("(property")]
        kept = [c for c in children(base) if not c.startswith("(property")]
        head = re.match(r'\(symbol "[^"]+"', base).group(0)
        body = "\n\t\t".join(derived_props + kept)
        body = body.replace(f'(symbol "{base_name}_', f'(symbol "{name}_')
        blk = f'(symbol "{name}"\n\t\t{body}\n\t)'
    return blk.replace(f'(symbol "{name}"', f'(symbol "{lib_id}"', 1)


def pins(lib_id):
    """{number: (x, y, angle, name, type)} in library coordinates (Y up)."""
    blk = flat_symbol(lib_id)
    out = {}
    for m in re.finditer(r'\(pin (\w+) (\w+)\s*\(at ([-\d.]+) ([-\d.]+) (\d+)\)(.*?)\(number "([^"]*)"', blk, re.S):
        nm = re.search(r'\(name "([^"]*)"', m.group(6))
        num = m.group(7)
        if num in out:          # stacked pins: keep the first
            continue
        out[num] = (float(m.group(3)), float(m.group(4)), int(m.group(5)), nm.group(1) if nm else "", m.group(1))
    return out
