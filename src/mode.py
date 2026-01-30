# -*- coding: utf-8 -*-
from __future__ import annotations
import time, csv, re, os, threading
from collections import defaultdict
from typing import Dict, Iterable, List, Optional
from pathlib import Path
from datetime import datetime
from binding import BindingManager
import tkinter as tk
from tkinter import ttk


# ---------------- 基础工具 ----------------
def _safe(s: str, default: str = "session") -> str:
    if not s: return default
    return re.sub(r'[^A-Za-z0-9_\-\u4e00-\u9fa5]+', '_', s.strip()) or default


def _make_data_dir(mode_type: str) -> Path:
    today = datetime.now().strftime("%Y%m%d")
    base_dir = Path("data") / today
    if mode_type == "line_infinite":
        sub_dir = "line_mode_infinite"
    elif mode_type == "line_timed":
        sub_dir = "line_mode_timed"
    elif mode_type == "point":
        sub_dir = "point_mode"
    else:
        sub_dir = "others"
    full_path = base_dir / sub_dir
    full_path.mkdir(parents=True, exist_ok=True)
    return full_path


def _simple_path(out_dir: str | Path, stem: str, mode_label: str | None, action_name: str | None,
                 mode_type: Optional[str] = None) -> str:
    if mode_type:
        out_dir = _make_data_dir(mode_type)
    else:
        out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    parts = [stem]
    if mode_label: parts.append(_safe(mode_label))
    if action_name: parts.append(_safe(action_name))
    base = "_".join(parts)
    path = out_dir / f"{base}.csv"
    if not path.exists(): return str(path)
    i = 2
    while True:
        cand = out_dir / f"{base}_v{i}.csv"
        if not cand.exists(): return str(cand)
        i += 1


def _make_tri_headers(epcs: List[str], binder: BindingManager, subcols: List[str], is_point_mode: bool = False) -> \
tuple[list, list, list]:
    header_epc, header_name, header_sub = [], [], []
    if is_point_mode:
        header_epc.append("次数")
        header_name.append("")
        header_sub.append("#")

    for i, epc in enumerate(epcs):
        display_name = binder.get_name(epc)
        header_epc.append(epc)
        header_epc.extend([""] * (len(subcols) - 1))
        header_name.append(display_name if display_name != epc else "")
        header_name.extend([""] * (len(subcols) - 1))
        header_sub.extend(subcols)

        if i != len(epcs) - 1:
            header_epc.append("")
            header_name.append("")
            header_sub.append("")

    return header_epc, header_name, header_sub


# ---------------- 线形采集模式 ----------------
def run_line_mode(
        stream: Iterable[dict],
        out_dir: str | Path,
        stop_after_seconds: Optional[float] = None,
        *,
        action_name: Optional[str] = None,
        frame_span: float = 0.1,
        binder: BindingManager,
) -> str | None:
    if stream is None: raise ValueError("stream=None: DataCollector.stream() 必须是生成器。")
    from queue import Queue, Empty
    q: Queue = Queue(maxsize=10000);
    stop = object()

    def feeder():
        try:
            for raw in stream: q.put(raw)
        finally:
            try:
                q.put_nowait(stop)
            except Exception:
                pass

    threading.Thread(target=feeder, daemon=True).start()

    start_t = time.time();
    last_ts = start_t
    buckets: Dict[str, Dict[int, List[float]]] = defaultdict(lambda: defaultdict(list))

    try:
        while True:
            if stop_after_seconds is not None and (time.time() - start_t) >= stop_after_seconds: break
            try:
                item = q.get(timeout=0.1)
            except Empty:
                continue
            if item is stop: break
            ts = float(item.get("ts", time.time()));
            epc = str(item["epc"])
            rssi = float(item.get("rssi", item.get("intensity", 0)))
            last_ts = ts;
            idx = int((ts - start_t) / frame_span)
            if idx < 0: idx = 0
            buckets[epc][idx].append(rssi)
    except KeyboardInterrupt:
        pass

    if not buckets: return None

    total_span = stop_after_seconds if stop_after_seconds is not None else max(0.0, last_ts - start_t)
    end_idx = max(1, int(total_span / frame_span))

    per_epc_rows = {};
    epc_order = list(buckets.keys())
    for epc in epc_order:
        rows = [];
        table = buckets[epc]
        for fidx in range(end_idx):
            vals = table.get(fidx, [])
            t_rel = round((fidx + 1) * frame_span, 6)
            if vals:
                sv = sorted(vals);
                n = len(sv)
                median = sv[n // 2] if n % 2 == 1 else 0.5 * (sv[n // 2 - 1] + sv[n // 2])
                cnt, vmax, mean = n, max(vals), sum(vals) / n
            else:
                median = cnt = vmax = mean = 0.0
            rows.append((t_rel, median, cnt, vmax, mean))
        per_epc_rows[epc] = rows

    subcols = ["time_s", "median", "count", "max", "mean"]
    header_epc, header_name, header_sub = _make_tri_headers(epc_order, binder, subcols)

    mode_label = "infinite" if stop_after_seconds is None else "timed"
    mode_type = f"line_{mode_label}"
    out = _simple_path(out_dir, "line_mode", mode_label, action_name, mode_type=mode_type)

    with open(out, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(header_epc)
        w.writerow(header_name)
        w.writerow(header_sub)
        for r in range(end_idx):
            row = []
            for i, epc in enumerate(epc_order):
                row.extend(list(per_epc_rows[epc][r]))
                if i != len(epc_order) - 1: row.append("")
            w.writerow(row)

    print(f"[INFO] 数据已保存至: {out}")
    return out


# ---------------- 点形采集模式 ----------------
def run_point_mode(
        stream: Iterable[dict],
        out_dir: str | Path,
        trigger_prompt: str = "按回车采集，输入 q 退出并保存：",
        timeout_per_trigger: float = 3.0,
        *,
        action_name: Optional[str] = None,
        binder: BindingManager,
) -> str | None:
    import sys, re
    from queue import Queue, Empty
    import threading, time, csv
    from collections import defaultdict

    class _LineFilterIO:
        def __init__(self, underlying, patterns):
            self._u = underlying;self._buf = "";self._pat = [re.compile(p, re.I) for p in patterns]

        def write(self, s):
            self._buf += s;
            out = [];
            while True:
                i = self._buf.find("\n");
                if i < 0: break
                line = self._buf[:i + 1];
                self._buf = self._buf[i + 1:]
                if any(p.match(line) for p in self._pat): continue
                out.append(line)
            if out: return self._u.write("".join(out))
            return len(s)

        def flush(self):
            if self._buf:
                line = self._buf;
                self._buf = ""
                if not any(p.match(line) for p in self._pat): self._u.write(line)
            self._u.flush()

        def isatty(self):
            return getattr(self._u, "isatty", lambda: False)()

        def fileno(self):
            return getattr(self._u, "fileno", lambda: 1)()

    _orig_out, _orig_err = sys.stdout, sys.stderr
    _patterns = [r"^\s*send\s*->", r"^\s*recv\s*<-", r"^\s*send->", r"^\s*recv<-"]
    sys.stdout = _LineFilterIO(_orig_out, _patterns);
    sys.stderr = _LineFilterIO(_orig_err, _patterns)

    try:
        if stream is None: raise ValueError("stream=None: DataCollector.stream() 必须是生成器。")
        try:
            import msvcrt; _HAS_MSVCRT = True
        except Exception:
            _HAS_MSVCRT = False

        def _wait_for_trigger() -> bool:
            print(trigger_prompt, end="", flush=True)
            if not _HAS_MSVCRT: cmd = input().strip().lower();return cmd != 'q'
            while msvcrt.kbhit(): msvcrt.getwch()
            while True:
                ch = msvcrt.getwch()
                if ch in ("\r", "\n"): print();return True
                if ch in ("q", "Q"): print("q");return False

        q: Queue = Queue(maxsize=20000);
        stop = object()

        def feeder():
            try:
                for raw in stream: q.put(raw)
            finally:
                try:
                    q.put_nowait(stop)
                except Exception:
                    pass

        threading.Thread(target=feeder, daemon=True).start()

        known_epcs: List[str] = [];
        rows_by_epc = defaultdict(list)
        labels: List[str] = [];
        triggers = 0

        def _show_edit_window(current_labels):
            editable_labels = list(current_labels);
            root = tk.Tk();
            root.title("编辑Label")
            container = ttk.Frame(root);
            container.pack(expand=True, fill="both")
            cols = ["#", *known_epcs, "Label"]
            tree = ttk.Treeview(container, columns=cols, show="headings")
            x_scrollbar = ttk.Scrollbar(container, orient="horizontal", command=tree.xview)
            tree.configure(xscrollcommand=x_scrollbar.set)

            tree.heading("#", text="行号");
            tree.column("#", width=50, anchor="center", stretch=False)
            for epc in known_epcs:
                display_name = binder.get_name(epc)

                # --- 【核心修正】在这里实现EPC缩写 ---
                abbreviated_epc = f"{epc[:8]}...{epc[-4:]}"

                if display_name != epc:
                    # 如果绑定了名称，显示 "名称 (缩写EPC)"
                    header_text = f"{display_name} ({abbreviated_epc})"
                else:
                    # 如果没绑定，只显示缩写的EPC
                    header_text = abbreviated_epc

                tree.heading(epc, text=header_text)
                tree.column(epc, width=220, anchor="center", stretch=True)  # 稍微调整宽度

            tree.heading("Label", text="Label");
            tree.column("Label", width=150, anchor="w", stretch=False)

            for r in range(triggers):
                row_data = [r + 1]
                for epc in known_epcs:
                    avg_val = f"{rows_by_epc[epc][r][3]:.1f}" if r < len(rows_by_epc[epc]) else "-"
                    row_data.append(avg_val)
                row_data.append(editable_labels[r])
                tree.insert("", "end", values=row_data, iid=str(r))

            tree.grid(row=0, column=0, sticky="nsew")
            x_scrollbar.grid(row=1, column=0, sticky="ew")
            container.grid_rowconfigure(0, weight=1)
            container.grid_columnconfigure(0, weight=1)

            def on_double_click(event):
                item_id = tree.focus()
                if not item_id or tree.identify_column(event.x) != f"#{len(cols)}": return
                x, y, width, height = tree.bbox(item_id, column=f"#{len(cols)}")
                entry = ttk.Entry(root);
                entry.place(x=x, y=y, width=width, height=height)
                entry.insert(0, tree.item(item_id, "values")[-1]);
                entry.focus_force()

                def save_edit(event):
                    new_val = entry.get();
                    row_index = int(item_id)
                    current_values = list(tree.item(item_id, "values"));
                    current_values[-1] = new_val
                    tree.item(item_id, values=current_values)
                    editable_labels[row_index] = new_val;
                    entry.destroy()

                entry.bind("<Return>", save_edit);
                entry.bind("<FocusOut>", save_edit)

            tree.bind("<Double-1>", on_double_click)
            btn = ttk.Button(root, text="保存并继续采集", command=root.destroy);
            btn.pack(pady=10)
            root.wait_window()
            return editable_labels

        def _write_final_csv():
            out_path = Path(_simple_path(out_dir, "point_mode", None, action_name, mode_type="point"))
            subcols = ["v1", "v2", "v3", "avg"]
            header_epc, header_name, header_sub = _make_tri_headers(known_epcs, binder, subcols, is_point_mode=True)
            header_epc.append("");
            header_name.append("");
            header_sub.append("label")
            with open(out_path, "w", newline="", encoding="utf-8-sig") as f:
                w = csv.writer(f)
                w.writerow(header_epc)
                w.writerow(header_name)
                w.writerow(header_sub)
                for r in range(triggers):
                    row = [r + 1]
                    for i, epc in enumerate(known_epcs):
                        lst = rows_by_epc[epc]
                        row.extend(lst[r] if r < len(lst) else ["", "", "", ""])
                        if i != len(known_epcs) - 1: row.append("")
                    lbl = labels[r] if r < len(labels) else ""
                    row.append(lbl)
                    w.writerow(row)
            print(f"\n[成功] 数据已全部保存至: {out_path}")
            return str(out_path)

        while True:
            if not _wait_for_trigger(): break
            win_start = time.time();
            collected = defaultdict(list);
            quit_flag = False
            print("采集中...", end='\r')
            while time.time() - win_start <= timeout_per_trigger:
                try:
                    item = q.get(timeout=0.05)
                    if item is stop: quit_flag = True;break
                    epc = str(item.get("epc", "")).strip()
                    if not epc: continue
                    rssi = float(item.get("rssi", item.get("intensity", 0)))
                    if len(collected[epc]) < 3: collected[epc].append(rssi)
                except Empty:
                    continue
            print(" " * 20, end='\r')
            if quit_flag: break
            if not collected: print("[提示] 本轮未采到有效 EPC"); time.sleep(1); continue
            triggers += 1
            for epc in collected.keys():
                if epc not in known_epcs:
                    known_epcs.append(epc)
                    for _ in range(triggers - 1): rows_by_epc[epc].append([0, 0, 0, 0])
            for epc in known_epcs:
                if epc in collected:
                    v = (collected[epc] + [0, 0, 0])[:3];
                    avg = sum(v) / 3
                    rows_by_epc[epc].append([v[0], v[1], v[2], avg])
                elif len(rows_by_epc[epc]) < triggers:
                    rows_by_epc[epc].append([0, 0, 0, 0])
            if len(labels) < triggers: labels.append(f"Sample_{triggers}")
            print("请在弹出的窗口中编辑Labels...")
            updated_labels = _show_edit_window(labels)
            labels = updated_labels
            print("编辑完成，已保存修改。")

        if triggers > 0:
            return _write_final_csv()
        else:
            print("\n未采集到任何数据，已跳过文件保存。"); return None
    finally:
        sys.stdout.flush();
        sys.stderr.flush()
        sys.stdout, sys.stderr = _orig_out, _orig_err