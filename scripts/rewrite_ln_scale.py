#!/usr/bin/env python3
"""EXPERIMENT (FP16 overflow test): LayerNorm variance rescale. For each Pow(x-mean, 2) whose measured max exceeds --thresh
(from act_range.py json), replace var = mean(d^2) by var = mean((d*c)^2) * (1/c^2), c = 2^-k, k = ceil(log2(max|d|/64)).
Mathematically identical in exact arithmetic; keeps d^2 below the FP16 max (65504). usage: rewrite_ln_scale.py in.onnx out.onnx ranges.json [--thresh 2e4] [--lo 1.0] [--fold]"""
import sys, json, math, numpy as np, onnx
from onnx import helper as h, numpy_helper as nh
src, dst, rj = sys.argv[1:4]; thr = float(sys.argv[sys.argv.index("--thresh") + 1]) if "--thresh" in sys.argv else 2e4
FOLD = "--fold" in sys.argv
lo = float(sys.argv[sys.argv.index("--lo") + 1]) if "--lo" in sys.argv else 0.0   # also scale UP layers whose measured (x-mean)^2 max < lo (FP16 underflow)
m = onnx.load(src); r = json.load(open(rj)); g = m.graph
byout = {o: n for n in g.node for o in n.output}
new = []; done = []
nodes = list(g.node); idx = {id(n): i for i, n in enumerate(nodes)}
ins_before = {}  # id(node) -> list of nodes to insert before
for n in nodes:
    if n.op_type != "Pow": continue
    mx = r.get(n.output[0], {}).get("max", 0)
    if mx <= thr and not (lo and 0 < mx < lo): continue
    d = n.input[0]; maxd = math.sqrt(mx) * 1.5
    k = math.ceil(math.log2(maxd / 64)); k = max(0, k) if mx > thr else k; c = 2.0 ** -k   # k<0 => scale UP (underflow case, --lo)
    cname = n.name + "_lnscale_c"; g.initializer.append(nh.from_array(np.float32(c), cname))
    sc = h.make_node("Mul", [d, cname], [d + "_lnsc"], name=n.name + "_lnscale")
    n.input[0] = d + "_lnsc"
    addname = n.name[:-3] + "Add"
    add = next(a for a in nodes if a.name == addname)
    if FOLD:  # no un-scale constant (2^-2k can be FP16-subnormal => flushed to 0 on MDLA): use d'=c*d in the Div numerator and eps*c^2
        div = next(a for a in nodes if a.op_type == "Div" and a.input[0] == d); div.input[0] = d + "_lnsc"
        ec = {i.name: nh.to_array(i) for i in g.initializer}; ec.update({o: nh.to_array(a.attribute[0].t) for a in nodes if a.op_type == "Constant" for o in a.output})
        eps = float(ec[add.input[1]]); en = n.name + "_lnscale_eps"; g.initializer.append(nh.from_array(np.float32(eps * c * c), en)); add.input[1] = en
        ins_before.setdefault(id(n), []).append(sc); done.append((n.name, k)); continue
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
