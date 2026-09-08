# ============================================================
#  run_detil_su.py  –  GUI Konfigurasi Auto-Paste DETIL SU
#  Manajemen Dokumen > Surat Ukur > Tab DETIL
# ============================================================

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import yaml
import os
import sys
import threading
import time
from datetime import datetime

# ── path helper ──────────────────────────────────────────────
def base_path():
    """Return folder tempat .exe atau script berada."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

CONFIG_FILE  = os.path.join(base_path(), "config_detil.yaml")
LOG_FILE     = os.path.join(base_path(), "laporan_detil.txt")
ASSETS_DIR   = os.path.join(base_path(), "assets")

# ── warna tema ───────────────────────────────────────────────
BG          = "#1e1e2e"
BG2         = "#2a2a3e"
BG3         = "#313150"
ACCENT      = "#7c6af7"
ACCENT2     = "#5a9af7"
SUCCESS     = "#4ade80"
WARNING     = "#facc15"
DANGER      = "#f87171"
TEXT        = "#e2e8f0"
TEXT_DIM    = "#94a3b8"
BORDER      = "#404060"

# ── load / save config ───────────────────────────────────────
def load_config():
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def save_config(cfg):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        yaml.dump(cfg, f, allow_unicode=True, default_flow_style=False,
                  sort_keys=False)

# ── log helper ───────────────────────────────────────────────
def write_log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}\n"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line)
    return line


# ╔══════════════════════════════════════════════════════════╗
#  WIDGET HELPERS
# ╚══════════════════════════════════════════════════════════╝
def styled_frame(parent, **kw):
    kw.setdefault("bg", BG2)
    kw.setdefault("bd", 0)
    return tk.Frame(parent, **kw)

def styled_label(parent, text, bold=False, color=TEXT, size=10, **kw):
    font = ("Segoe UI", size, "bold" if bold else "normal")
    kw.setdefault("bg", parent.cget("bg"))
    return tk.Label(parent, text=text, font=font, fg=color, **kw)

def styled_entry(parent, textvariable=None, width=30, **kw):
    e = tk.Entry(parent, textvariable=textvariable, width=width,
                 bg=BG3, fg=TEXT, insertbackground=TEXT,
                 relief="flat", bd=4,
                 highlightthickness=1, highlightcolor=ACCENT,
                 highlightbackground=BORDER, **kw)
    return e

def styled_text(parent, height=3, width=50, **kw):
    t = tk.Text(parent, height=height, width=width,
                bg=BG3, fg=TEXT, insertbackground=TEXT,
                relief="flat", bd=4, wrap="word",
                highlightthickness=1, highlightcolor=ACCENT,
                highlightbackground=BORDER, **kw)
    return t

def styled_check(parent, text, variable, **kw):
    kw.setdefault("bg", parent.cget("bg"))
    return tk.Checkbutton(parent, text=text, variable=variable,
                          fg=TEXT, selectcolor=BG3, activebackground=BG2,
                          activeforeground=TEXT, font=("Segoe UI", 9), **kw)

def styled_button(parent, text, command, color=ACCENT, w=14, **kw):
    return tk.Button(parent, text=text, command=command,
                     bg=color, fg="white", activebackground=BG3,
                     activeforeground=TEXT, relief="flat", bd=0,
                     padx=8, pady=4, width=w, cursor="hand2",
                     font=("Segoe UI", 9, "bold"), **kw)

def section_header(parent, title):
    f = styled_frame(parent, bg=BG3)
    f.pack(fill="x", pady=(10, 2))
    styled_label(f, f"  {title}", bold=True, color=ACCENT2, size=10,
                 bg=BG3).pack(side="left", padx=4, pady=4)
    return f


# ╔══════════════════════════════════════════════════════════╗
#  PANEL DAFTAR ISIAN (tabel baris dinamis)
# ╚══════════════════════════════════════════════════════════╝
class PanelDaftarIsian(tk.Frame):
    KOLOM = ["di_seri", "di_nomor", "di_luas", "di_tanggal"]
    HEADER = ["Seri DI", "Nomor", "Luas", "Tanggal"]

    def __init__(self, parent, baris_data: list, **kw):
        kw.setdefault("bg", BG2)
        super().__init__(parent, **kw)
        self._rows: list[dict] = []   # list of {key: StringVar}
        self._build_header()
        self._scroll_frame()
        for b in baris_data:
            self._add_row(b)
        self._build_footer()

    # ── header kolom ─────────────────────────────────────────
    def _build_header(self):
        hdr = styled_frame(self, bg=BG3)
        hdr.pack(fill="x")
        widths = [8, 10, 10, 12]
        for i, (h, w) in enumerate(zip(self.HEADER, widths)):
            styled_label(hdr, h, bold=True, color=ACCENT2, bg=BG3
                         ).grid(row=0, column=i, padx=6, pady=4, sticky="w")
            hdr.columnconfigure(i, minsize=w*9)
        styled_label(hdr, "Aksi", bold=True, color=ACCENT2, bg=BG3
                     ).grid(row=0, column=4, padx=6, pady=4)

    # ── canvas scrollable ─────────────────────────────────────
    def _scroll_frame(self):
        container = tk.Frame(self, bg=BG2)
        container.pack(fill="both", expand=True)

        self._canvas = tk.Canvas(container, bg=BG2, highlightthickness=0,
                                  height=160)
        sb = ttk.Scrollbar(container, orient="vertical",
                            command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)

        self._inner = tk.Frame(self._canvas, bg=BG2)
        self._win_id = self._canvas.create_window(
            (0, 0), window=self._inner, anchor="nw")
        self._inner.bind("<Configure>", self._on_inner_config)
        self._canvas.bind("<Configure>", self._on_canvas_config)

    def _on_inner_config(self, _e):
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _on_canvas_config(self, e):
        self._canvas.itemconfig(self._win_id, width=e.width)

    # ── footer tombol tambah ──────────────────────────────────
    def _build_footer(self):
        ft = styled_frame(self, bg=BG2)
        ft.pack(fill="x", pady=4)
        styled_button(ft, "+ Tambah Baris", self._add_row,
                      color=ACCENT2, w=16).pack(side="left", padx=6)

    # ── satu baris ───────────────────────────────────────────
    def _add_row(self, data: dict | None = None):
        if data is None:
            data = {}
        idx = len(self._rows)
        row_vars = {}
        row_frame = styled_frame(self._inner, bg=BG2)
        row_frame.pack(fill="x", pady=1)

        widths = [8, 10, 10, 12]
        for i, (key, w) in enumerate(zip(self.KOLOM, widths)):
            sv = tk.StringVar(value=str(data.get(key, "")))
            row_vars[key] = sv
            e = styled_entry(row_frame, textvariable=sv, width=w)
            e.grid(row=0, column=i, padx=4, pady=2, sticky="w")

        # tombol hapus baris
        btn_del = tk.Button(row_frame, text="✕", command=lambda f=row_frame: self._del_row(f),
                            bg=DANGER, fg="white", relief="flat", bd=0,
                            width=3, cursor="hand2", font=("Segoe UI", 9))
        btn_del.grid(row=0, column=4, padx=4)

        row_vars["_frame"] = row_frame
        self._rows.append(row_vars)

    def _del_row(self, frame):
        self._rows = [r for r in self._rows if r["_frame"] is not frame]
        frame.destroy()

    # ── baca data ─────────────────────────────────────────────
    def get_data(self) -> list:
        result = []
        for r in self._rows:
            result.append({k: r[k].get() for k in self.KOLOM})
        return result


# ╔══════════════════════════════════════════════════════════╗
#  PANEL SATU FIELD DETAIL LAIN-LAIN
# ╚══════════════════════════════════════════════════════════╝
class PanelFieldDetail(tk.Frame):
    def __init__(self, parent, label: str, data: dict, multiline=False, **kw):
        kw.setdefault("bg", BG2)
        super().__init__(parent, **kw)
        self._enabled = tk.BooleanVar(value=data.get("enabled", True))
        self._multiline = multiline

        top = styled_frame(self, bg=BG2)
        top.pack(fill="x")
        styled_check(top, f"  {label}", self._enabled,
                     command=self._toggle).pack(side="left", padx=6, pady=2)

        body = styled_frame(self, bg=BG2)
        body.pack(fill="x", padx=10, pady=(0, 4))

        if multiline:
            self._widget = styled_text(body, height=3, width=70)
            self._widget.insert("1.0", data.get("nilai", ""))
            self._widget.pack(fill="x")
        else:
            sv = tk.StringVar(value=str(data.get("nilai", "")))
            self._sv = sv
            self._widget = styled_entry(body, textvariable=sv, width=55)
            self._widget.pack(side="left", fill="x", expand=True)

        self._toggle()

    def _toggle(self):
        state = "normal" if self._enabled.get() else "disabled"
        self._widget.config(state=state)

    def get_data(self) -> dict:
        if self._multiline:
            v = self._widget.get("1.0", "end-1c")
        else:
            v = self._sv.get()
        return {"enabled": self._enabled.get(), "nilai": v}


# ╔══════════════════════════════════════════════════════════╗
#  APLIKASI UTAMA
# ╚══════════════════════════════════════════════════════════╝
class AppDetilSU(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Auto-Paste DETIL Surat Ukur  ·  ATR/BPN")
        self.configure(bg=BG)
        self.resizable(True, True)
        self.minsize(780, 600)
        self._center(900, 720)

        self._cfg = load_config()
        self._running = False
        self._paused  = False
        self._worker  = None

        self._build_titlebar()
        self._build_body()
        self._build_statusbar()
        self._bind_keys()

    # ── utilitas ─────────────────────────────────────────────
    def _center(self, w, h):
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    # ── title bar ────────────────────────────────────────────
    def _build_titlebar(self):
        bar = styled_frame(self, bg=BG3)
        bar.pack(fill="x")
        styled_label(bar, "  ⚙  Auto-Paste DETIL Surat Ukur",
                     bold=True, color=ACCENT, size=12, bg=BG3
                     ).pack(side="left", pady=8)
        styled_label(bar, "ATR/BPN  ",
                     color=TEXT_DIM, size=9, bg=BG3
                     ).pack(side="right", pady=8)

    # ── body (notebook) ──────────────────────────────────────
    def _build_body(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Dark.TNotebook",
                        background=BG, borderwidth=0, tabmargins=[2,4,0,0])
        style.configure("Dark.TNotebook.Tab",
                        background=BG3, foreground=TEXT_DIM,
                        padding=[14, 5], font=("Segoe UI", 9))
        style.map("Dark.TNotebook.Tab",
                  background=[("selected", BG2)],
                  foreground=[("selected", ACCENT)])

        nb = ttk.Notebook(self, style="Dark.TNotebook")
        nb.pack(fill="both", expand=True, padx=8, pady=6)

        self._tab_config  = self._build_tab_config(nb)
        self._tab_kontrol = self._build_tab_kontrol(nb)
        self._tab_log     = self._build_tab_log(nb)

        nb.add(self._tab_config,  text="  Konfigurasi  ")
        nb.add(self._tab_kontrol, text="  Kontrol & Jalankan  ")
        nb.add(self._tab_log,     text="  Log  ")

    # ─────────────────────────────────────────────────────────
    #  TAB 1 – KONFIGURASI
    # ─────────────────────────────────────────────────────────
    def _build_tab_config(self, nb):
        outer = styled_frame(nb, bg=BG)
        canvas = tk.Canvas(outer, bg=BG, highlightthickness=0)
        sb = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        inner = styled_frame(canvas, bg=BG)
        win = canvas.create_window((0, 0), window=inner, anchor="nw")

        def on_inner(_e):
            canvas.configure(scrollregion=canvas.bbox("all"))
        def on_canvas(e):
            canvas.itemconfig(win, width=e.width)
        inner.bind("<Configure>", on_inner)
        canvas.bind("<Configure>", on_canvas)

        # bind mousewheel
        def _scroll(e):
            canvas.yview_scroll(int(-1*(e.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _scroll)

        # ── Seri ─────────────────────────────────────────────
        section_header(inner, "SERI")
        seri_frame = styled_frame(inner, bg=BG2)
        seri_frame.pack(fill="x", padx=8, pady=2)

        seri_cfg = self._cfg.get("seri", {})
        self._seri_enabled = tk.BooleanVar(value=seri_cfg.get("enabled", True))
        self._seri_nilai   = tk.StringVar(value=str(seri_cfg.get("nilai", "-")))

        row = styled_frame(seri_frame, bg=BG2)
        row.pack(fill="x", padx=8, pady=6)
        styled_check(row, "Ganti nilai Seri", self._seri_enabled,
                     command=self._toggle_seri).pack(side="left")
        styled_label(row, "  Nilai:", bg=BG2).pack(side="left")
        self._seri_entry = styled_entry(row, textvariable=self._seri_nilai, width=20)
        self._seri_entry.pack(side="left", padx=6)
        self._toggle_seri()

        # ── Daftar Isian ─────────────────────────────────────
        section_header(inner, "DAFTAR ISIAN")
        di_frame = styled_frame(inner, bg=BG2)
        di_frame.pack(fill="x", padx=8, pady=2)

        di_cfg = self._cfg.get("daftar_isian", {})
        self._di_enabled = tk.BooleanVar(value=di_cfg.get("enabled", True))
        row2 = styled_frame(di_frame, bg=BG2)
        row2.pack(fill="x", padx=8, pady=(6,2))
        styled_check(row2, "Proses tabel Daftar Isian",
                     self._di_enabled).pack(side="left")

        self._panel_di = PanelDaftarIsian(
            di_frame,
            baris_data=di_cfg.get("baris", [])
        )
        self._panel_di.pack(fill="x", padx=8, pady=4)

        # ── Detail Lain-Lain ─────────────────────────────────
        section_header(inner, "DETAIL LAIN-LAIN")
        dl_cfg = self._cfg.get("detail_lain", {})

        fields = [
            ("keadaan_tanah",         "Keadaan Tanah",                False),
            ("tanda_tanda_batas",     "Tanda-Tanda Batas",            True),
            ("pengukuran_dan_pemetaan","Pengukuran dan Pemetaan Nama", False),
            ("hal_lain_lain",         "Hal Lain-Lain",                False),
        ]
        self._detail_panels: dict[str, PanelFieldDetail] = {}
        for key, label, ml in fields:
            pf = PanelFieldDetail(inner, label,
                                  dl_cfg.get(key, {"enabled": True, "nilai": ""}),
                                  multiline=ml, bg=BG)
            pf.pack(fill="x", padx=8, pady=2)
            self._detail_panels[key] = pf

        # ── Tombol simpan config ──────────────────────────────
        btn_row = styled_frame(inner, bg=BG)
        btn_row.pack(fill="x", padx=8, pady=10)
        styled_button(btn_row, "💾  Simpan Config",
                      self._save_config, color=SUCCESS, w=20
                      ).pack(side="right", padx=6)

        return outer

    def _toggle_seri(self):
        s = "normal" if self._seri_enabled.get() else "disabled"
        self._seri_entry.config(state=s)

    def _save_config(self):
        cfg = self._cfg.copy()

        cfg["seri"] = {
            "enabled": self._seri_enabled.get(),
            "nilai":   self._seri_nilai.get(),
        }
        cfg["daftar_isian"] = {
            "enabled": self._di_enabled.get(),
            "baris":   self._panel_di.get_data(),
        }
        cfg["detail_lain"] = {
            k: self._detail_panels[k].get_data()
            for k in self._detail_panels
        }
        save_config(cfg)
        self._cfg = cfg
        self._log("✅  Konfigurasi disimpan.")
        messagebox.showinfo("Simpan", "Konfigurasi berhasil disimpan!", parent=self)

    # ─────────────────────────────────────────────────────────
    #  TAB 2 – KONTROL & JALANKAN
    # ─────────────────────────────────────────────────────────
    def _build_tab_kontrol(self, nb):
        f = styled_frame(nb, bg=BG)

        # info hotkey
        section_header(f, "HOTKEY")
        hk_frame = styled_frame(f, bg=BG2)
        hk_frame.pack(fill="x", padx=8, pady=4)
        keys = [
            ("F9",  "Mulai / Lanjutkan satu record"),
            ("F10", "Jeda / Lanjutkan"),
            ("F11", "Reset ke awal"),
            ("ESC", "Hentikan & keluar proses"),
        ]
        for k, v in keys:
            row = styled_frame(hk_frame, bg=BG2)
            row.pack(fill="x", padx=10, pady=2)
            styled_label(row, k, bold=True, color=WARNING, bg=BG2,
                         width=5).pack(side="left")
            styled_label(row, v, color=TEXT_DIM, bg=BG2).pack(side="left", padx=6)

        # delay config
        section_header(f, "DELAY (detik)")
        dl_frame = styled_frame(f, bg=BG2)
        dl_frame.pack(fill="x", padx=8, pady=4)
        delay_cfg = self._cfg.get("delay", {})
        self._delay_vars: dict[str, tk.StringVar] = {}
        delay_labels = {
            "antar_field":   "Antar Field",
            "setelah_klik":  "Setelah Klik",
            "setelah_ketik": "Setelah Ketik",
            "setelah_tab":   "Setelah Tab",
        }
        for i, (k, lbl) in enumerate(delay_labels.items()):
            row = styled_frame(dl_frame, bg=BG2)
            row.pack(fill="x", padx=10, pady=2)
            styled_label(row, lbl, bg=BG2, width=18).pack(side="left")
            sv = tk.StringVar(value=str(delay_cfg.get(k, 0.4)))
            self._delay_vars[k] = sv
            styled_entry(row, textvariable=sv, width=8).pack(side="left")

        # status & kontrol
        section_header(f, "KONTROL PROSES")
        ctrl = styled_frame(f, bg=BG2)
        ctrl.pack(fill="x", padx=8, pady=8)

        self._status_var = tk.StringVar(value="⏸  Menunggu…")
        self._progress_var = tk.StringVar(value="Record: -")

        styled_label(ctrl, "", textvariable=self._status_var,
                     bold=True, color=SUCCESS, bg=BG2, size=11
                     ).pack(pady=6)
        styled_label(ctrl, "", textvariable=self._progress_var,
                     color=TEXT_DIM, bg=BG2
                     ).pack(pady=2)

        btn_row = styled_frame(ctrl, bg=BG2)
        btn_row.pack(pady=10)

        self._btn_start = styled_button(btn_row, "▶  MULAI (F9)",
                                        self._start_worker, color=SUCCESS, w=18)
        self._btn_start.pack(side="left", padx=6)

        self._btn_pause = styled_button(btn_row, "⏸  JEDA (F10)",
                                        self._toggle_pause, color=WARNING, w=18)
        self._btn_pause.pack(side="left", padx=6)

        self._btn_reset = styled_button(btn_row, "↺  RESET (F11)",
                                        self._reset_worker, color=ACCENT, w=18)
        self._btn_reset.pack(side="left", padx=6)

        self._btn_stop = styled_button(btn_row, "■  STOP",
                                       self._stop_worker, color=DANGER, w=14)
        self._btn_stop.pack(side="left", padx=6)

        return f

    # ─────────────────────────────────────────────────────────
    #  TAB 3 – LOG
    # ─────────────────────────────────────────────────────────
    def _build_tab_log(self, nb):
        f = styled_frame(nb, bg=BG)
        section_header(f, "LOG PROSES")

        self._log_widget = scrolledtext.ScrolledText(
            f, bg=BG3, fg=TEXT, font=("Consolas", 9),
            state="disabled", relief="flat", bd=4,
            wrap="word", height=20
        )
        self._log_widget.pack(fill="both", expand=True, padx=8, pady=4)

        btn_row = styled_frame(f, bg=BG)
        btn_row.pack(fill="x", padx=8, pady=4)
        styled_button(btn_row, "🗑  Bersihkan Log", self._clear_log,
                      color=BG3, w=18).pack(side="right")
        return f

    def _log(self, msg: str):
        line = write_log(msg)
        self._log_widget.config(state="normal")
        self._log_widget.insert("end", line)
        self._log_widget.see("end")
        self._log_widget.config(state="disabled")

    def _clear_log(self):
        self._log_widget.config(state="normal")
        self._log_widget.delete("1.0", "end")
        self._log_widget.config(state="disabled")

    # ─────────────────────────────────────────────────────────
    #  STATUS BAR
    # ─────────────────────────────────────────────────────────
    def _build_statusbar(self):
        sb = styled_frame(self, bg=BG3)
        sb.pack(fill="x", side="bottom")
        self._sb_var = tk.StringVar(value="Siap.")
        styled_label(sb, "", textvariable=self._sb_var,
                     color=TEXT_DIM, bg=BG3, size=9
                     ).pack(side="left", padx=8, pady=3)

    def _set_status(self, msg: str, color=TEXT_DIM):
        self._sb_var.set(msg)
        self._status_var.set(msg)

    # ─────────────────────────────────────────────────────────
    #  HOTKEY BINDINGS
    # ─────────────────────────────────────────────────────────
    def _bind_keys(self):
        self.bind_all("<F9>",  lambda _e: self._start_worker())
        self.bind_all("<F10>", lambda _e: self._toggle_pause())
        self.bind_all("<F11>", lambda _e: self._reset_worker())
        self.bind_all("<Escape>", lambda _e: self._stop_worker())

    # ─────────────────────────────────────────────────────────
    #  WORKER THREAD
    # ─────────────────────────────────────────────────────────
    def _start_worker(self):
        if self._running:
            self._log("ℹ️  Proses sudah berjalan.")
            return
        self._save_config()      # simpan dulu sebelum jalankan
        self._running = True
        self._paused  = False
        self._set_status("▶  Berjalan…", SUCCESS)
        self._log("▶  Memulai proses auto-paste DETIL SU…")
        self._worker = threading.Thread(target=self._run_paste, daemon=True)
        self._worker.start()

    def _toggle_pause(self):
        if not self._running:
            return
        self._paused = not self._paused
        if self._paused:
            self._set_status("⏸  Dijeda…", WARNING)
            self._log("⏸  Dijeda.")
        else:
            self._set_status("▶  Melanjutkan…", SUCCESS)
            self._log("▶  Melanjutkan.")

    def _reset_worker(self):
        self._stop_worker()
        self._set_status("↺  Reset.", ACCENT)
        self._log("↺  Proses direset.")
        self._progress_var.set("Record: -")

    def _stop_worker(self):
        self._running = False
        self._paused  = False
        self._set_status("■  Dihentikan.", DANGER)
        self._log("■  Proses dihentikan.")

    # ─────────────────────────────────────────────────────────
    #  LOGIKA PASTE  (diimpor dari auto_paste_detil.py)
    # ─────────────────────────────────────────────────────────
    def _run_paste(self):
        try:
            from auto_paste_detil import jalankan_paste
            jalankan_paste(
                cfg          = self._cfg,
                assets_dir   = ASSETS_DIR,
                is_running   = lambda: self._running,
                is_paused    = lambda: self._paused,
                log_fn       = self._log,
                progress_fn  = lambda msg: self._progress_var.set(msg),
                status_fn    = self._set_status,
            )
        except ImportError:
            self._log("⚠️  auto_paste_detil.py tidak ditemukan. Mode simulasi.")
            self._run_simulasi()
        except Exception as ex:
            self._log(f"❌  Error: {ex}")
        finally:
            self._running = False
            self._set_status("✅  Selesai.", SUCCESS)
            self._log("✅  Proses selesai.")

    def _run_simulasi(self):
        """Simulasi tanpa pyautogui — untuk testing GUI."""
        baris = self._cfg.get("daftar_isian", {}).get("baris", [])
        for i, b in enumerate(baris, 1):
            while self._paused and self._running:
                time.sleep(0.2)
            if not self._running:
                break
            self._progress_var.set(f"Record: {i}/{len(baris)}")
            self._log(f"[SIM] Baris {i}: {b}")
            time.sleep(0.8)


# ── main ──────────────────────────────────────────────────────
if __name__ == "__main__":
    app = AppDetilSU()
    app.mainloop()
