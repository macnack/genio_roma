#!/usr/bin/env python3
"""Enumerate ONNX ops/attributes and compare op names with DX-COM operator tables.

Usage: python scripts/inspect_onnx.py model.onnx --table NAME=path/to/03_Building_Models.md [--table ...]
Reports (never modifies the model):
  * op type counts, input/output shapes, dynamic dims
  * Conv configs (kernel/stride/pad/dilation/group, depthwise yes/no)
  * ops absent from each table (by name)
  * explicit checks of the documented Conv constraints that matter for ConvNeXt
Table rule parsing is limited to op NAME presence plus the Conv depthwise-kernel rule, which
is encoded below from the doc text; everything else must be read from the doc by a human.
"""
import argparse, collections, json, re, sys
from pathlib import Path

import onnx
from onnx import numpy_helper


def table_ops(md: Path) -> set:
    ops = set()
    for line in md.read_text().splitlines():
        m = re.match(r"^\|\s*([A-Za-z0-9_]+)\s*\|", line)
        if m and m.group(1).lower() not in {"operator", "operation", "op", "name"}:
            ops.add(m.group(1))
    return ops


def dims(vi):
    return [d.dim_value if d.HasField("dim_value") else (d.dim_param or "?") for d in vi.type.tensor_type.shape.dim]


def attr(n, name, default=None):
    for a in n.attribute:
        if a.name == name:
            return list(a.ints) if a.ints else (a.i if a.HasField("i") else (a.s.decode() if a.s else default))
    return default


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("onnx")
    ap.add_argument("--table", action="append", default=[], help="NAME=path")
    ap.add_argument("--json", help="write JSON report here")
    a = ap.parse_args()

    m = onnx.load(a.onnx)
    g = m.graph
    init = {i.name: i for i in g.initializer}
    shapes = {v.name: dims(v) for v in list(g.input) + list(g.value_info) + list(g.output)}
    # shape inference to know conv input channels
    sm = onnx.shape_inference.infer_shapes(m)
    for v in list(sm.graph.value_info):
        shapes[v.name] = dims(v)

    counts = collections.Counter(n.op_type for n in g.node)
    rep = {"file": a.onnx, "opsets": {o.domain or "ai.onnx": o.version for o in m.opset_import},
           "inputs": {i.name: dims(i) for i in g.input}, "outputs": {o.name: dims(o) for o in g.output},
           "op_counts": dict(sorted(counts.items())), "n_nodes": len(g.node)}
    dyn = [k for k, v in {**rep["inputs"], **rep["outputs"]}.items() if any(not isinstance(x, int) or x <= 0 for x in v)]
    rep["dynamic_io"] = dyn

    convs = collections.Counter()
    dw_bad = []
    for n in g.node:
        if n.op_type != "Conv":
            continue
        k = tuple(attr(n, "kernel_shape", []) or [])
        w = init.get(n.input[1])
        if not k and w is not None:
            k = tuple(w.dims[2:])
        grp = attr(n, "group", 1) or 1
        cin = shapes.get(n.input[0], [None, None])[1]
        dw = grp > 1 and cin is not None and grp == cin
        cfg = (f"{'depthwise' if dw else ('grouped' if grp > 1 else 'standard')} k={k} "
               f"s={tuple(attr(n, 'strides', []) or [])} p={tuple(attr(n, 'pads', []) or [])} "
               f"d={tuple(attr(n, 'dilations', []) or [])} g={grp}")
        convs[cfg] += 1
        if dw and k not in {(3, 3), (5, 5)}:
            dw_bad.append(n.name or n.output[0])
    rep["conv_configs"] = dict(convs)
    rep["depthwise_not_3x3_or_5x5"] = {"count": len(dw_bad), "examples": dw_bad[:3]}

    rep["tables"] = {}
    for t in a.table:
        name, path = t.split("=", 1)
        ops = table_ops(Path(path))
        rep["tables"][name] = {"table": path, "ops_in_table": len(ops),
                               "model_ops_not_named_in_table": sorted(set(counts) - ops)}

    # LayerNorm / GELU forms
    rep["forms"] = {"LayerNormalization_nodes": counts.get("LayerNormalization", 0),
                    "ReduceMean": counts.get("ReduceMean", 0), "Erf(gelu chain)": counts.get("Erf", 0),
                    "Gelu_nodes": counts.get("Gelu", 0), "Transpose": counts.get("Transpose", 0),
                    "Reshape": counts.get("Reshape", 0)}

    print(json.dumps(rep, indent=2))
    if a.json:
        Path(a.json).write_text(json.dumps(rep, indent=2))


if __name__ == "__main__":
    main()
