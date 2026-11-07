#!/usr/bin/env python3
"""Exact algebraic ReduceMean replacements (for the Mali-G57 GpuAcc MEAN fault, see reports/gpu_armnn.md):
  NCHW mean over C (axes=[1], keepdims)  -> Conv 1x1 (C->1, weight 1/C)
  NHWC mean over C (axes=[-1], keepdims) -> Reshape[H*W,C] -> MatMul([C,1] = 1/C) -> Reshape[1,H,W,1]
  [1,C] mean over C (axes=[-1], keepdims)-> MatMul([C,1] = 1/C)
  NCHW mean over (H,W), keepdims=0       -> GlobalAveragePool -> Reshape[1,C]
Every rewrite is printed; ORT parity vs the input model is checked."""
import sys, numpy as np, onnx, onnxruntime as ort
from onnx import helper as h, numpy_helper as nh, shape_inference
BC = "--broadcast" in sys.argv   # materialise the mean at full width (C outputs) so later Sub/Div have same-shape operands
ONLY = None   # --only nchw_c,nhwc_c,flat_c,gap : rewrite just these kinds, keep the other ReduceMean nodes untouched (ablation)
if "--only" in sys.argv:
    i = sys.argv.index("--only"); ONLY = set(sys.argv[i + 1].split(",")); del sys.argv[i:i + 2]
EXCL = None   # --exclude SUBSTR : keep (do not rewrite) ReduceMean nodes whose name contains SUBSTR (leave-one-out ablation)
if "--exclude" in sys.argv:
    i = sys.argv.index("--exclude"); EXCL = sys.argv[i + 1]; del sys.argv[i:i + 2]
sys.argv = [a for a in sys.argv if a != "--broadcast"]
src, dst = sys.argv[1], sys.argv[2]
m = shape_inference.infer_shapes(onnx.load(src))
sh = {v.name: [d.dim_value for d in v.type.tensor_type.shape.dim] for v in list(m.graph.value_info) + list(m.graph.input)}
out, cnt = [], {}
def add_init(name, arr): m.graph.initializer.append(nh.from_array(arr, name))
for n in m.graph.node:
    if n.op_type != "ReduceMean": out.append(n); continue
    s = sh[n.input[0]]; ax = next((list(a.ints) for a in n.attribute if a.name == "axes"), None)
    kd = next((a.i for a in n.attribute if a.name == "keepdims"), 1); x, y, nm = n.input[0], n.output[0], n.name
    kind = ("nchw_c" if len(s) == 4 and ax == [1] and kd == 1 else "nhwc_c" if len(s) == 4 and ax == [-1] and kd == 1 else
            "flat_c" if len(s) == 2 and ax == [-1] and kd == 1 else "gap" if len(s) == 4 and sorted(ax) == [-2, -1] and kd == 0 else None)
    if (ONLY is not None and kind not in ONLY) or (EXCL is not None and EXCL in nm):
        out.append(n); cnt["kept_" + str(kind)] = cnt.get("kept_" + str(kind), 0) + 1; continue
    if len(s) == 4 and ax == [1] and kd == 1:
        C = s[1]; add_init(nm + "_w", np.full((C if BC else 1, C, 1, 1), 1.0 / C, np.float32))
        out.append(h.make_node("Conv", [x, nm + "_w"], [y], name=nm, kernel_shape=[1, 1])); k = "nchw_c"
    elif len(s) == 4 and ax == [-1] and kd == 1:
        _, H, W, C = s; add_init(nm + "_w", np.full((C, C if BC else 1), 1.0 / C, np.float32))
        add_init(nm + "_s1", np.array([H * W, C], np.int64)); add_init(nm + "_s2", np.array([1, H, W, C if BC else 1], np.int64))
        out += [h.make_node("Reshape", [x, nm + "_s1"], [nm + "_a"], name=nm + "_pre"),
                h.make_node("MatMul", [nm + "_a", nm + "_w"], [nm + "_b"], name=nm),
                h.make_node("Reshape", [nm + "_b", nm + "_s2"], [y], name=nm + "_post")]; k = "nhwc_c"
    elif len(s) == 2 and ax == [-1] and kd == 1:
        C = s[1]; add_init(nm + "_w", np.full((C, C if BC else 1), 1.0 / C, np.float32))
        out.append(h.make_node("MatMul", [x, nm + "_w"], [y], name=nm)); k = "flat_c"
    elif len(s) == 4 and sorted(ax) == [-2, -1] and kd == 0:
        add_init(nm + "_s", np.array([1, s[1]], np.int64))
        out += [h.make_node("GlobalAveragePool", [x], [nm + "_g"], name=nm), h.make_node("Reshape", [nm + "_g", nm + "_s"], [y], name=nm + "_post")]; k = "gap"
    else:
        sys.exit(f"unhandled ReduceMean {nm} shape={s} axes={ax} keepdims={kd}")
    cnt[k] = cnt.get(k, 0) + 1
del m.graph.node[:]; m.graph.node.extend(out)
for vi in list(m.graph.value_info): m.graph.value_info.remove(vi)
onnx.checker.check_model(m); onnx.save(m, dst); print("rewritten ReduceMean:", cnt)
x = np.random.RandomState(0).randn(1, 3, 224, 224).astype(np.float32)
sa, sb = [ort.InferenceSession(p, providers=["CPUExecutionProvider"]) for p in (src, dst)]
ya = sa.run(None, {sa.get_inputs()[0].name: x})[0]; yb = sb.run(None, {sb.get_inputs()[0].name: x})[0]
print(f"parity: max_abs={np.abs(ya-yb).max():.3g} cosine={float((ya*yb).sum()/(np.linalg.norm(ya)*np.linalg.norm(yb))):.8f} top1_same={ya.argmax()==yb.argmax()}")
