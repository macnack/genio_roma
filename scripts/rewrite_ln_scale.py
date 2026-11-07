#!/usr/bin/env python3
"""EXPERIMENT (FP16 overflow test): LayerNorm variance rescale. For each Pow(x-mean, 2) whose measured max exceeds --thresh
(from act_range.py json), replace var = mean(d^2) by var = mean((d*c)^2) * (1/c^2), c = 2^-k, k = ceil(log2(max|d|/64)).
Mathematically identical in exact arithmetic; keeps d^2 below the FP16 max (65504). usage: rewrite_ln_scale.py in.onnx out.onnx ranges.json [--thresh 2e4]"""
import sys, json, math, numpy as np, onnx
from onnx import helper as h, numpy_helper as nh
src, dst, rj = sys.argv[1:4]; thr = float(sys.argv[sys.argv.index("--thresh") + 1]) if "--thresh" in sys.argv else 2e4
m = onnx.load(src); r = json.load(open(rj)); g = m.graph
byout = {o: n for n in g.node for o in n.output}
new = []; done = []
nodes = list(g.node); idx = {id(n): i for i, n in enumerate(nodes)}
ins_before = {}  # id(node) -> list of nodes to insert before
for n in nodes:
    if n.op_type != "Pow": continue
    mx = r.get(n.output[0], {}).get("max", 0)
    if mx <= thr: continue
    d = n.input[0]; maxd = math.sqrt(mx) * 1.5
    k = max(0, math.ceil(math.log2(maxd / 64))); c = 2.0 ** -k
    cname = n.name + "_lnscale_c"; g.initializer.append(nh.from_array(np.float32(c), cname))
    sc = h.make_node("Mul", [d, cname], [d + "_lnsc"], name=n.name + "_lnscale")
    n.input[0] = d + "_lnsc"
    addname = n.name[:-3] + "Add"
    add = next(a for a in nodes if a.name == addname)
    var = add.input[0]; iname = n.name + "_lnscale_ic"; g.initializer.append(nh.from_array(np.float32(1 / c / c), iname))
    inv = h.make_node("Mul", [var, iname], [var + "_lnun"], name=n.name + "_lnunscale"); add.input[0] = var + "_lnun"
    ins_before.setdefault(id(n), []).append(sc); ins_before.setdefault(id(add), []).append(inv)
    done.append((n.name, k))
out = []
for n in nodes:
    out += ins_before.get(id(n), []); out.append(n)
del g.node[:]; g.node.extend(out)
onnx.checker.check_model(m); onnx.save(m, dst)
print("rescaled:", done)
