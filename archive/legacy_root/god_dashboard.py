"""
god_dashboard.py — Full desktop dashboard for the god-engine.

Panels:
  Top:    Prompt input + buttons (Invoke, Voice, Append to Doc)
  Left:   Streaming output + Angel debug log
  Right:  Angel control toggles
  Bottom: Memory viewer | Canon editor | Scene timeline | Character web

Run:
  python god_dashboard.py
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import time
import json

from core   import divine_core
from memory import load_memory, save_memory
from utils  import auto_detect_characters
from canon  import CANON, GLYPH_RULES, STRAIN_THRESHOLD

try:
    from gdocs import get_document_text, append_text as doc_append
    GDOCS_AVAILABLE = True
except Exception:
    GDOCS_AVAILABLE = False

try:
    from voice import speak as _speak
    TTS_AVAILABLE = True
except Exception:
    TTS_AVAILABLE = False

try:
    from stt import listen_once
    STT_AVAILABLE = True
except Exception:
    STT_AVAILABLE = False

try:
    import matplotlib
    matplotlib.use("TkAgg")
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    import networkx as nx
    VIZ_AVAILABLE = True
except Exception:
    VIZ_AVAILABLE = False

DOC_ID = ""  # set your Google Doc ID here or pass via env


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def stream_to_widget(widget: tk.Text, text: str, delay: float = 0.02) -> None:
    widget.config(state="normal")
    widget.delete("1.0", tk.END)
    for line in text.splitlines():
        widget.insert(tk.END, line + "\n")
        widget.see(tk.END)
        widget.update_idletasks()
        time.sleep(delay)
    widget.config(state="disabled")


def append_to_log(widget: tk.Text, msg: str) -> None:
    widget.config(state="normal")
    widget.insert(tk.END, msg + "\n")
    widget.see(tk.END)
    widget.config(state="disabled")


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

class GodEngineDashboard(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("Fallen Veil — God-Engine Dashboard")
        self.geometry("1400x900")
        self.configure(bg="#1a1a1a")

        self._angel_vars: dict[str, tk.BooleanVar] = {}
        self._build_layout()
        self._refresh_memory()

    # ────────────────────────────────────────────────────────────────────────
    # Layout
    # ────────────────────────────────────────────────────────────────────────

    def _build_layout(self) -> None:
        # ── Top: prompt + controls ──────────────────────────────────────────
        top = tk.Frame(self, bg="#1a1a1a")
        top.pack(fill="x", padx=8, pady=(8, 0))

        tk.Label(top, text="Prompt:", bg="#1a1a1a", fg="#ccc",
                 font=("Helvetica", 11)).pack(anchor="w")

        self.prompt_box = tk.Text(top, height=4, bg="#2a2a2a", fg="#eee",
                                  insertbackground="white", font=("Helvetica", 11))
        self.prompt_box.pack(fill="x")

        btn_row = tk.Frame(top, bg="#1a1a1a")
        btn_row.pack(fill="x", pady=4)

        self._btn(btn_row, "⚡ Invoke (Memory)",     lambda: self._run(use_gdocs=False))
        self._btn(btn_row, "📄 Invoke (Google Doc)",  lambda: self._run(use_gdocs=True))
        self._btn(btn_row, "🎙 Voice Prompt",          self._voice_prompt)
        self._btn(btn_row, "📎 Append to Doc",         self._append_to_doc)
        self._btn(btn_row, "🔄 Refresh Memory",        self._refresh_memory)

        # ── Middle: output + debug + angel toggles ──────────────────────────
        mid = tk.PanedWindow(self, orient="horizontal", bg="#1a1a1a",
                             sashwidth=5, sashrelief="flat")
        mid.pack(fill="both", expand=True, padx=8, pady=4)

        # Output
        out_frame = tk.Frame(mid, bg="#1a1a1a")
        tk.Label(out_frame, text="God-Engine Output (streaming):",
                 bg="#1a1a1a", fg="#aaa").pack(anchor="w")
        self.output_box = tk.Text(out_frame, state="disabled", bg="#111",
                                  fg="#e8d5b0", font=("Georgia", 12),
                                  wrap="word")
        sb1 = tk.Scrollbar(out_frame, command=self.output_box.yview)
        self.output_box.configure(yscrollcommand=sb1.set)
        sb1.pack(side="right", fill="y")
        self.output_box.pack(fill="both", expand=True)
        mid.add(out_frame)

        # Debug log
        debug_frame = tk.Frame(mid, bg="#1a1a1a")
        tk.Label(debug_frame, text="Angel Debug Log:", bg="#1a1a1a", fg="#aaa").pack(anchor="w")
        self.debug_box = scrolledtext.ScrolledText(
            debug_frame, state="disabled", bg="#0d0d0d",
            fg="#7acc7a", font=("Courier", 10), height=20,
        )
        self.debug_box.pack(fill="both", expand=True)
        mid.add(debug_frame)

        # Angel toggles
        angel_frame = tk.LabelFrame(mid, text="Angel Controls",
                                    bg="#1a1a1a", fg="#ccc", font=("Helvetica", 10))
        self._build_angel_panel(angel_frame)
        mid.add(angel_frame)

        # ── Bottom: tabs ─────────────────────────────────────────────────────
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        self._build_memory_tab(notebook)
        self._build_canon_tab(notebook)
        self._build_timeline_tab(notebook)
        self._build_glyph_tab(notebook)
        if VIZ_AVAILABLE:
            self._build_viz_tab(notebook)

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _btn(self, parent, label, cmd):
        tk.Button(parent, text=label, command=cmd,
                  bg="#333", fg="#eee", activebackground="#555",
                  relief="flat", padx=8, pady=4).pack(side="left", padx=2)

    # ────────────────────────────────────────────────────────────────────────
    # Angel control panel
    # ────────────────────────────────────────────────────────────────────────

    ANGELS = [
        "LoreAngel", "CombatAngel", "DialogueAngel",
        "EmotionAngel", "ContinuityAngel", "PacingAngel", "ToneAngel",
    ]

    def _build_angel_panel(self, parent) -> None:
        for angel in self.ANGELS:
            row  = tk.Frame(parent, bg="#1a1a1a")
            var  = tk.BooleanVar(value=True)
            self._angel_vars[angel] = var
            tk.Checkbutton(row, text=angel, variable=var,
                           bg="#1a1a1a", fg="#ccc", selectcolor="#333",
                           activebackground="#1a1a1a").pack(anchor="w")
            row.pack(fill="x", pady=1)

    def _active_angels(self) -> list[str]:
        return [a for a, v in self._angel_vars.items() if v.get()]

    # ────────────────────────────────────────────────────────────────────────
    # Bottom tabs
    # ────────────────────────────────────────────────────────────────────────

    def _build_memory_tab(self, nb) -> None:
        frame = tk.Frame(nb, bg="#1a1a1a")
        nb.add(frame, text="Memory")
        self.mem_box = scrolledtext.ScrolledText(
            frame, state="disabled", bg="#111", fg="#ccc",
            font=("Courier", 10),
        )
        self.mem_box.pack(fill="both", expand=True)

    def _build_canon_tab(self, nb) -> None:
        frame = tk.Frame(nb, bg="#1a1a1a")
        nb.add(frame, text="Canon Editor")
        self.canon_box = scrolledtext.ScrolledText(
            frame, bg="#111", fg="#e8d5b0", font=("Courier", 10),
        )
        self.canon_box.insert("1.0", CANON)
        self.canon_box.pack(fill="both", expand=True)
        tk.Button(frame, text="Save Canon to File", command=self._save_canon,
                  bg="#333", fg="#eee", relief="flat").pack(anchor="e", padx=4, pady=2)

    def _build_timeline_tab(self, nb) -> None:
        frame = tk.Frame(nb, bg="#1a1a1a")
        nb.add(frame, text="Scene Timeline")
        self.timeline_box = scrolledtext.ScrolledText(
            frame, state="disabled", bg="#111", fg="#ccc",
            font=("Courier", 10),
        )
        self.timeline_box.pack(fill="both", expand=True)

    def _build_glyph_tab(self, nb) -> None:
        frame = tk.Frame(nb, bg="#1a1a1a")
        nb.add(frame, text="Glyph Simulator")

        tk.Label(frame, text="Glyphs (comma-separated):",
                 bg="#1a1a1a", fg="#ccc").pack(anchor="w", padx=4, pady=(4, 0))
        self.glyph_entry = tk.Entry(frame, bg="#2a2a2a", fg="#eee",
                                    insertbackground="white")
        self.glyph_entry.insert(0, "Sight, Bind")
        self.glyph_entry.pack(fill="x", padx=4)

        tk.Button(frame, text="Simulate", command=self._run_glyph_sim,
                  bg="#333", fg="#eee", relief="flat").pack(anchor="w", padx=4, pady=4)

        self.glyph_output = scrolledtext.ScrolledText(
            frame, height=10, bg="#111", fg="#ccc", font=("Courier", 10),
        )
        self.glyph_output.pack(fill="both", expand=True, padx=4, pady=4)

    def _build_viz_tab(self, nb) -> None:
        frame = tk.Frame(nb, bg="#1a1a1a")
        nb.add(frame, text="Visualizations")
        tk.Button(frame, text="Character Relationship Graph",
                  command=self._show_relationship_graph,
                  bg="#333", fg="#eee", relief="flat").pack(pady=8)

    # ────────────────────────────────────────────────────────────────────────
    # Actions
    # ────────────────────────────────────────────────────────────────────────

    def _debug(self, msg: str) -> None:
        append_to_log(self.debug_box, msg)

    def _run(self, use_gdocs: bool = False) -> None:
        def worker():
            self._debug("[GUI] Starting pipeline...")

            # context
            if use_gdocs and GDOCS_AVAILABLE and DOC_ID:
                try:
                    full = get_document_text(DOC_ID)
                    context = full[-4000:]
                    self._debug("[GUI] Context from Google Doc.")
                except Exception as e:
                    self._debug(f"[GUI] Doc error: {e} — using memory.")
                    context = self._context_from_memory()
            else:
                context = self._context_from_memory()
                if not use_gdocs:
                    self._debug("[GUI] Context from memory.")

            prompt = self.prompt_box.get("1.0", tk.END).strip()
            if not prompt:
                self._debug("[GUI] No prompt entered.")
                return

            chars = auto_detect_characters(context)
            self._debug(f"[GUI] Characters: {chars}")

            result = divine_core(
                user_prompt    = prompt,
                context        = context,
                location       = "Unknown",
                characters     = chars,
                debug_callback = self._debug,
            )

            stream_to_widget(self.output_box, result)
            self._refresh_memory()

            if TTS_AVAILABLE:
                _speak(result)

        threading.Thread(target=worker, daemon=True).start()

    def _context_from_memory(self) -> str:
        mem    = load_memory()
        scenes = mem["timeline"]["scenes"]
        return "".join(s["text_excerpt"] for s in scenes[-5:]) if scenes else ""

    def _voice_prompt(self) -> None:
        if not STT_AVAILABLE:
            self._debug("[STT not available]")
            return
        text = listen_once()
        if text:
            self.prompt_box.delete("1.0", tk.END)
            self.prompt_box.insert("1.0", text)

    def _append_to_doc(self) -> None:
        if not GDOCS_AVAILABLE or not DOC_ID:
            self._debug("[Google Docs not configured]")
            return
        text = self.output_box.get("1.0", tk.END).strip()
        if text:
            try:
                doc_append(DOC_ID, text)
                self._debug("[GUI] Appended to Google Doc.")
            except Exception as e:
                self._debug(f"[GUI] Doc error: {e}")

    def _save_canon(self) -> None:
        text = self.canon_box.get("1.0", tk.END)
        with open("canon_custom.txt", "w", encoding="utf-8") as f:
            f.write(text)
        self._debug("[GUI] Canon saved to canon_custom.txt")

    def _run_glyph_sim(self) -> None:
        raw    = self.glyph_entry.get()
        glyphs = [g.strip() for g in raw.split(",") if g.strip()]
        result = {
            "glyphs":            glyphs,
            "total_strain":      0,
            "total_cost":        [],
            "side_effects":      [],
            "resonance_events":  [],
            "overload":          False,
            "warnings":          [],
        }
        for g in glyphs:
            rule = GLYPH_RULES.get(g)
            if not rule:
                result["warnings"].append(f"Unknown glyph: {g}")
                continue
            result["total_strain"] += rule["strain"]
            result["total_cost"].append(rule["cost"])
            result["side_effects"].append(rule["side_effect"])
            for r2 in rule.get("resonates_with", []):
                if r2 in glyphs:
                    result["resonance_events"].append(f"{g} ↔ {r2}")

        if result["total_strain"] > STRAIN_THRESHOLD:
            result["overload"] = True
            result["warnings"].append(
                f"OVERLOAD — strain {result['total_strain']} > {STRAIN_THRESHOLD}"
            )

        self.glyph_output.delete("1.0", tk.END)
        self.glyph_output.insert("1.0", json.dumps(result, indent=2))

    def _refresh_memory(self) -> None:
        mem = load_memory()

        # memory tab
        self.mem_box.config(state="normal")
        self.mem_box.delete("1.0", tk.END)
        self.mem_box.insert("1.0", json.dumps(mem, indent=2, ensure_ascii=False))
        self.mem_box.config(state="disabled")

        # timeline tab
        self.timeline_box.config(state="normal")
        self.timeline_box.delete("1.0", tk.END)
        for s in mem["timeline"]["scenes"]:
            line = f"Scene {s['id']:>3}  [{s['location']}]  {s['summary']}\n"
            self.timeline_box.insert(tk.END, line)
        self.timeline_box.config(state="disabled")

    def _show_relationship_graph(self) -> None:
        if not VIZ_AVAILABLE:
            return
        mem  = load_memory()
        G    = nx.Graph()
        for name, data in mem["characters"].items():
            G.add_node(name)
            for other, status in data["current_state"]["relationships"].items():
                G.add_edge(name, other, label=status)

        win    = tk.Toplevel(self)
        win.title("Character Relationship Graph")
        fig, ax = plt.subplots(figsize=(7, 5))
        pos    = nx.spring_layout(G, k=0.9, seed=42)
        nx.draw(G, pos, with_labels=True, node_color="#4a90d9",
                font_color="white", ax=ax)
        labels = nx.get_edge_attributes(G, "label")
        nx.draw_networkx_edge_labels(G, pos, edge_labels=labels, ax=ax)
        ax.set_title("Character Relationships")
        canvas = FigureCanvasTkAgg(fig, master=win)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app = GodEngineDashboard()
    app.mainloop()
