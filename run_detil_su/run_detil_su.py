# ============================================================
#  run_detil_su.py  –  Auto-Paste DETIL Surat Ukur  (1 layar)
# ============================================================

import tkinter as tk
from tkinter import ttk, scrolledtext
import yaml, os, sys, threading, time
from datetime import datetime

def base_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

CONFIG_FILE = os.path.join(base_path(), "config_detil.yaml")
LOG_FILE    = os.path.join(base_path(), "laporan_detil.txt")
ASSETS_DIR  = os.path.join(base_path(), "assets")

BG      = "#1e1e2e"
BG2     = "#252538"
BG3     = "#2e2e48"
BG4     = "#363658"
ACCENT  = "#7c6af7"
ACCENT2 = "#5a9af7"
SUCCESS = "#4ade80"
WARNING = "#facc15"
DANGER  = "#f87171"
TEXT    = "#e2e8f0"
TEXT_DIM= "#94a3b8"
BORDER  = "#454568"
SEP     = "#3a3a5c"

def load_config():
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def save_config(cfg):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        yaml.dump(cfg, f, allow_unicode=True,
                  default_flow_style=False, sort_keys=False)

def write_log(msg):
    ts   = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}\n"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line)
    return line

# ── widget helpers ───────────────────────────────────────────
def frm(parent, bg=None, **kw):
    kw["bg"] = bg or BG2; kw.setdefault("bd", 0)
    return tk.Frame(parent, **kw)

def lbl(parent, text="", bold=False, color=TEXT, size=9, anchor="w", **kw):
    kw.setdefault("bg", parent.cget("bg"))
    return tk.Label(parent, text=text, anchor=anchor,
                    font=("Segoe UI", size, "bold" if bold else "normal"),
                    fg=color, **kw)

def ent(parent, var=None, w=10, **kw):
    return tk.Entry(parent, textvariable=var, width=w,
                    bg=BG4, fg=TEXT, insertbackground=TEXT,
                    relief="flat", bd=3, highlightthickness=1,
                    highlightcolor=ACCENT, highlightbackground=BORDER, **kw)

def txt_widget(parent, h=2, w=40, **kw):
    return tk.Text(parent, height=h, width=w,
                   bg=BG4, fg=TEXT, insertbackground=TEXT,
                   relief="flat", bd=3, wrap="word",
                   highlightthickness=1, highlightcolor=ACCENT,
                   highlightbackground=BORDER,
                   font=("Segoe UI", 9), **kw)

def chk(parent, text, var, **kw):
    kw.setdefault("bg", parent.cget("bg"))
    return tk.Checkbutton(parent, text=text, variable=var,
                          fg=TEXT, selectcolor=BG4,
                          activebackground=kw["bg"], activeforeground=TEXT,
                          font=("Segoe UI", 9), **kw)

def btn(parent, text, cmd, color=ACCENT, w=14, **kw):
    return tk.Button(parent, text=text, command=cmd,
                     bg=color, fg="white", activebackground=BG3,
                     activeforeground=TEXT, relief="flat", bd=0,
                     padx=6, pady=3, width=w, cursor="hand2",
                     font=("Segoe UI", 9, "bold"), **kw)

def section_bar(parent, title, bg=BG3):
    f = frm(parent, bg=bg)
    f.pack(fill="x", pady=(6, 1))
    lbl(f, f"  {title}", bold=True, color=ACCENT2, size=9,
        bg=bg).pack(side="left", padx=6, pady=3)
    return f


# ╔══════════════════════════════════════════════════════════╗
#  PANEL DAFTAR ISIAN
# ╚══════════════════════════════════════════════════════════╝
class PanelDaftarIsian(tk.Frame):
    def __init__(self, parent, kolom_data: list, **kw):
        kw.setdefault("bg", BG2)
        super().__init__(parent, **kw)
        self._kolom: list[dict] = []
        self._build_header()
        for k in kolom_data:
            self._add_kolom(k)

    def _build_header(self):
        h = frm(self, bg=BG3)
        h.pack(fill="x", padx=4, pady=(2,0))
        for t, w in [("✓",3),("ID",7),("Y",5),
                     ("X Nomor",7),("X Tahun",7),("X Tanggal",8),
                     ("Nomor",8),("Tahun",6),("Tanggal",10)]:
            lbl(h, t, bold=True, color=ACCENT2, bg=BG3,
                width=w).pack(side="left", padx=2, pady=3)

    def _add_kolom(self, data: dict):
        row = frm(self, bg=BG2)
        row.pack(fill="x", padx=4, pady=1)
        v: dict = {}
        en = tk.BooleanVar(value=data.get("enabled", True))
        v["enabled"] = en
        chk(row, "", en, bg=BG2).pack(side="left", padx=(4,2))
        for key, w in [("id",7),("y",5),
                       ("x_nomor",7),("x_tahun",7),("x_tanggal",8),
                       ("nomor",8),("tahun",6),("tanggal",10)]:
            sv = tk.StringVar(value=str(data.get(key, "")))
            v[key] = sv
            ent(row, var=sv, w=w).pack(side="left", padx=2)
        v["_row"] = row
        self._kolom.append(v)

    def get_data(self) -> list:
        result = []
        for k in self._kolom:
            d = {"id": k["id"].get(), "enabled": k["enabled"].get(),
                 "nomor": k["nomor"].get(), "tahun": k["tahun"].get(),
                 "tanggal": k["tanggal"].get()}
            for key in ("y","x_nomor","x_tahun","x_tanggal"):
                v = k[key].get().strip()
                if v:
                    try: d[key] = int(v)
                    except ValueError: pass
            result.append(d)
        return result


# ╔══════════════════════════════════════════════════════════╗
#  APLIKASI UTAMA  –  1 layar, kiri=config, kanan=log
# ╚══════════════════════════════════════════════════════════╝
class AppDetilSU(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Auto-Paste DETIL Surat Ukur · ATR/BPN")
        self.configure(bg=BG)
        self.resizable(True, True)
        self._center(1020, 640)
        self._cfg     = load_config()
        self._running = False
        self._paused  = False
        self._worker  = None
        self._build_ui()
        self._bind_keys()

    def _center(self, w, h):
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    # ── UI ───────────────────────────────────────────────────
    def _build_ui(self):
        # title bar
        bar = frm(self, bg=BG3)
        bar.pack(fill="x")
        lbl(bar, "  ⚙  Auto-Paste DETIL Surat Ukur",
            bold=True, color=ACCENT, size=11, bg=BG3).pack(side="left", pady=5)
        lbl(bar, "ATR/BPN  ", color=TEXT_DIM, size=9,
            bg=BG3).pack(side="right", pady=5)

        # status bar (bawah)
        sb = frm(self, bg=BG3)
        sb.pack(fill="x", side="bottom")
        self._sb_var = tk.StringVar(value="Siap.")
        lbl(sb, "", textvariable=self._sb_var,
            color=TEXT_DIM, bg=BG3, size=9).pack(side="left", padx=8, pady=2)

        # body: kiri (config) + kanan (log)
        body = frm(self, bg=BG)
        body.pack(fill="both", expand=True, padx=4, pady=4)
        body.columnconfigure(0, weight=3)
        body.columnconfigure(1, weight=2)
        body.rowconfigure(0, weight=1)

        self._build_kiri(body)
        self._build_kanan(body)

    # ══════════════════════════════════════════════════════════
    #  KIRI — KONFIGURASI + KONTROL
    # ══════════════════════════════════════════════════════════
    def _build_kiri(self, body):
        outer = frm(body, bg=BG)
        outer.grid(row=0, column=0, sticky="nsew", padx=(0,2))

        canvas = tk.Canvas(outer, bg=BG, highlightthickness=0)
        vsb    = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        inner = frm(canvas, bg=BG)
        win   = canvas.create_window((0,0), window=inner, anchor="nw")
        inner.bind("<Configure>",
                   lambda _: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>",
                    lambda e: canvas.itemconfig(win, width=e.width))
        canvas.bind_all("<MouseWheel>",
                        lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

        # ── KONTROL ──────────────────────────────────────────
        section_bar(inner, "KONTROL")
        cf = frm(inner, bg=BG2)
        cf.pack(fill="x", padx=4, pady=2)

        self._status_var   = tk.StringVar(value="⏸  Menunggu…")
        self._progress_var = tk.StringVar(value="Putaran: -")

        st_row = frm(cf, bg=BG2)
        st_row.pack(fill="x", padx=6, pady=(4,2))
        lbl(st_row, "", textvariable=self._status_var,
            bold=True, color=SUCCESS, bg=BG2, size=10).pack(side="left")
        lbl(st_row, "", textvariable=self._progress_var,
            color=WARNING, bg=BG2, size=9).pack(side="right", padx=6)

        br = frm(cf, bg=BG2)
        br.pack(fill="x", padx=6, pady=(2,6))
        btn(br, "▶ MULAI F1",  self._start_worker, color=SUCCESS, w=13).pack(side="left", padx=3)
        btn(br, "⏸ JEDA  \\",  self._toggle_pause, color=WARNING, w=13).pack(side="left", padx=2)
        btn(br, "↺ RESET F3",  self._reset_worker, color=ACCENT,  w=13).pack(side="left", padx=2)
        btn(br, "■ STOP ESC",  self._stop_worker,  color=DANGER,  w=13).pack(side="left", padx=2)

        dr = frm(cf, bg=BG2)
        dr.pack(fill="x", padx=6, pady=(0,4))
        self._debug_var = tk.BooleanVar(value=False)
        chk(dr, "🔴 Debug", self._debug_var, bg=BG2).pack(side="left")
        btn(dr, "🖱 Lacak Cursor", self._show_cursor_pos,
            color=BG3, w=15).pack(side="left", padx=6)
        btn(dr, "🔎 Cek Asset", self._cek_asset,
            color="#4a7a6f", w=12).pack(side="left", padx=2)
        btn(dr, "💾 Simpan", self._save_config,
            color="#2d6a4f", w=10).pack(side="left", padx=2)

        # ── PENOMORAN ─────────────────────────────────────────
        section_bar(inner, "PENOMORAN")
        pf = frm(inner, bg=BG2)
        pf.pack(fill="x", padx=4, pady=2)
        pen_cfg = self._cfg.get("penomoran", {})
        self._pen_en  = tk.BooleanVar(value=pen_cfg.get("tanggal_enabled", False))
        self._pen_val = tk.StringVar(value=str(pen_cfg.get("tanggal_nilai", "")))
        self._pen_x   = tk.StringVar(value=str(pen_cfg.get("tanggal_x", 370)))
        self._pen_y   = tk.StringVar(value=str(pen_cfg.get("tanggal_y", 612)))
        pr = frm(pf, bg=BG2)
        pr.pack(fill="x", padx=8, pady=4)
        chk(pr, "Tgl. Penemoran", self._pen_en,
            command=self._toggle_pen).pack(side="left")
        lbl(pr, "  Nilai:", color=TEXT_DIM, bg=BG2).pack(side="left", padx=(8,2))
        self._pen_entry = ent(pr, var=self._pen_val, w=14)
        self._pen_entry.pack(side="left")
        lbl(pr, "  X:", color=TEXT_DIM, bg=BG2).pack(side="left", padx=(8,2))
        ent(pr, var=self._pen_x, w=5).pack(side="left")
        lbl(pr, "  Y:", color=TEXT_DIM, bg=BG2).pack(side="left", padx=(6,2))
        ent(pr, var=self._pen_y, w=5).pack(side="left")
        self._toggle_pen()

        # ── PEMBUKUAN ─────────────────────────────────────────
        section_bar(inner, "PEMBUKUAN")
        pb_f = frm(inner, bg=BG2)
        pb_f.pack(fill="x", padx=4, pady=2)
        pb_cfg = self._cfg.get("pembukuan", {})
        self._pb_en   = tk.BooleanVar(value=pb_cfg.get("enabled", False))
        self._pb_nama = tk.StringVar(value=str(pb_cfg.get("nama", "")))
        self._pb_jab  = tk.StringVar(value=str(pb_cfg.get("jabatan_teks", "Kepala Seksi Survei dan Pemetaan")))
        pb_r = frm(pb_f, bg=BG2)
        pb_r.pack(fill="x", padx=8, pady=4)
        chk(pb_r, "Aktif", self._pb_en, bg=BG2).pack(side="left")
        lbl(pb_r, "  Jabatan:", color=TEXT_DIM, bg=BG2).pack(side="left", padx=(8,2))
        ent(pb_r, var=self._pb_jab, w=24).pack(side="left")
        lbl(pb_r, "  Nama:", color=TEXT_DIM, bg=BG2).pack(side="left", padx=(8,2))
        ent(pb_r, var=self._pb_nama, w=20).pack(side="left")

        # ── PENERBITAN SERTIFIKAT ─────────────────────────────
        section_bar(inner, "PENERBITAN SERTIFIKAT")
        ps_f = frm(inner, bg=BG2)
        ps_f.pack(fill="x", padx=4, pady=2)
        ps_cfg = self._cfg.get("penerbitan_sertifikat", {})
        self._ps_en   = tk.BooleanVar(value=ps_cfg.get("enabled", False))
        self._ps_nama = tk.StringVar(value=str(ps_cfg.get("nama", "")))
        self._ps_jab  = tk.StringVar(value=str(ps_cfg.get("jabatan_teks",  "Kepala Seksi Survei dan Pemetaan")))
        self._ps_jab2 = tk.StringVar(value=str(ps_cfg.get("jabatan2_teks", "Kepala Seksi Survei dan Pemetaan")))
        ps_r = frm(ps_f, bg=BG2)
        ps_r.pack(fill="x", padx=8, pady=4)
        chk(ps_r, "Aktif", self._ps_en, bg=BG2).pack(side="left")
        lbl(ps_r, "  Jabatan:", color=TEXT_DIM, bg=BG2).pack(side="left", padx=(8,2))
        ent(ps_r, var=self._ps_jab, w=28).pack(side="left")
        lbl(ps_r, "  Nama:", color=TEXT_DIM, bg=BG2).pack(side="left", padx=(8,2))
        ent(ps_r, var=self._ps_nama, w=20).pack(side="left")
        ps_r2 = frm(ps_f, bg=BG2)
        ps_r2.pack(fill="x", padx=8, pady=(0,4))
        lbl(ps_r2, "  Jabatan bawah:", color=TEXT_DIM, bg=BG2).pack(side="left")
        ent(ps_r2, var=self._ps_jab2, w=28).pack(side="left", padx=(2,0))

        # ── DAFTAR ISIAN ─────────────────────────────────────
        section_bar(inner, "DAFTAR ISIAN")
        df = frm(inner, bg=BG2)
        df.pack(fill="x", padx=4, pady=2)
        di_cfg = self._cfg.get("daftar_isian", {})
        self._di_en = tk.BooleanVar(value=di_cfg.get("enabled", True))
        dr2 = frm(df, bg=BG2)
        dr2.pack(fill="x", padx=8, pady=(4,2))
        chk(dr2, "Proses Daftar Isian", self._di_en).pack(side="left")
        self._panel_di = PanelDaftarIsian(df, kolom_data=di_cfg.get("kolom",[]))
        self._panel_di.pack(fill="x", padx=4, pady=(2,4))

        # ── DETAIL LAIN-LAIN ─────────────────────────────────
        section_bar(inner, "DETAIL LAIN-LAIN")
        dl = frm(inner, bg=BG2)
        dl.pack(fill="x", padx=4, pady=2)
        lbl(dl, "  ℹ️  Klik langsung ke koordinat (x,y) — tidak pakai Tab",
            color=TEXT_DIM, size=8, bg=BG2).pack(anchor="w", padx=8, pady=(2,4))
        dl_cfg = self._cfg.get("detail_lain", {})
        self._dl: dict[str, dict] = {}
        for key, lbl_text, ml in [
            ("keadaan_tanah",          "Keadaan Tanah",               False),
            ("tanda_tanda_batas",      "Tanda-Tanda Batas",           True),
            ("pengukuran_dan_pemetaan","Penunjukan & Penetapan Batas", True),
            ("hal_lain_lain",          "Hal Lain-Lain",               False),
        ]:
            sub = dl_cfg.get(key, {"enabled": True, "nilai": ""})
            self._build_dl_field(dl, key, lbl_text, sub, ml)

        # ── SIMPAN dihapus dari sini (sudah dipindah ke baris kontrol) ──

    # ══════════════════════════════════════════════════════════
    #  KANAN — LOG
    # ══════════════════════════════════════════════════════════
    def _build_kanan(self, body):
        rf = frm(body, bg=BG)
        rf.grid(row=0, column=1, sticky="nsew", padx=(2,0))
        rf.rowconfigure(1, weight=1)
        rf.columnconfigure(0, weight=1)

        section_bar(rf, "LOG PROSES").grid(row=0, column=0, sticky="ew")

        self._log_widget = scrolledtext.ScrolledText(
            rf, bg=BG4, fg=TEXT, font=("Consolas", 8),
            state="disabled", relief="flat", bd=0, wrap="word")
        self._log_widget.grid(row=1, column=0, sticky="nsew", padx=4, pady=4)

        br = frm(rf, bg=BG)
        br.grid(row=2, column=0, sticky="ew", padx=4, pady=4)
        btn(br, "🗑 Bersihkan", self._clear_log,
            color=BG3, w=14).pack(side="right")

    # ── Detail Lain-Lain field builder ───────────────────────
    def _build_dl_field(self, parent, key, label_text, sub, multiline):
        bg = BG2
        f  = frm(parent, bg=bg)
        f.pack(fill="x", padx=8, pady=1)
        en_var = tk.BooleanVar(value=sub.get("enabled", True))

        # baris atas: checkbox + label + X + Y
        top = frm(f, bg=bg)
        top.pack(fill="x")
        chk(top, label_text, en_var,
            command=lambda: self._toggle_dl(key), bg=bg).pack(side="left")
        lbl(top, " X:", color=TEXT_DIM, bg=bg, size=8).pack(side="left", padx=(8,1))
        xv = tk.StringVar(value=str(sub.get("x", "")))
        ent(top, var=xv, w=5).pack(side="left")
        lbl(top, " Y:", color=TEXT_DIM, bg=bg, size=8).pack(side="left", padx=(4,1))
        yv = tk.StringVar(value=str(sub.get("y", "")))
        ent(top, var=yv, w=5).pack(side="left")

        # baris bawah: input nilai / teks_tambah
        bot = frm(f, bg=bg)
        bot.pack(fill="x", pady=(1,2))

        # tentukan field nilai yang relevan
        # mode template_nama atau sisip_sebelum_kurung → tampilkan textarea template
        mode = sub.get("mode", "default")
        if mode in ("template_nama", "sisip_sebelum_kurung"):
            # tentukan key yang menyimpan nilai template/teks
            val_key = "template" if mode == "template_nama" else "teks_tambah"
            hint    = "Template  ({nama} = nama dari field):" if mode == "template_nama" \
                      else "Teks sisip:"
            lbl(bot, f"  {hint}", color=TEXT_DIM, bg=bg,
                size=8).pack(anchor="w", padx=2)
            w = txt_widget(bot, h=4, w=52)
            w.insert("1.0", str(sub.get(val_key, "")))
            w.pack(fill="x", expand=True)
            w._mode    = mode
            w._val_key = val_key
        elif multiline:
            w = txt_widget(bot, h=2, w=50)
            w.insert("1.0", sub.get("nilai", ""))
            w.pack(fill="x", expand=True)
            w._mode = "multiline"
        else:
            sv = tk.StringVar(value=str(sub.get("nilai", "")))
            w  = ent(bot, var=sv, w=52)
            w.pack(side="left", fill="x", expand=True)
            w._sv = sv
            w._mode = "single"

        self._dl[key] = {"en": en_var, "w": w, "ml": multiline,
                         "xv": xv, "yv": yv, "mode": mode}
        self._toggle_dl(key)

    def _toggle_dl(self, key):
        state = "normal" if self._dl[key]["en"].get() else "disabled"
        self._dl[key]["w"].config(state=state)

    def _toggle_pen(self):
        self._pen_entry.config(
            state="normal" if self._pen_en.get() else "disabled")

    def _toggle_seri(self):
        pass  # seri dihapus

    # ── save config ──────────────────────────────────────────
    def _save_config(self):
        cfg = dict(self._cfg)
        try:
            cfg["penomoran"] = {
                "tanggal_enabled": self._pen_en.get(),
                "tanggal_nilai":   self._pen_val.get(),
                "tanggal_x":       int(self._pen_x.get()),
                "tanggal_y":       int(self._pen_y.get()),
            }
        except (ValueError, AttributeError):
            pass
        cfg["daftar_isian"] = {"enabled": self._di_en.get(),
                               "kolom":   self._panel_di.get_data()}
        # pembukuan
        pb = self._cfg.get("pembukuan", {})
        pb.update({"enabled": self._pb_en.get(),
                   "nama":    self._pb_nama.get(),
                   "jabatan_teks": self._pb_jab.get()})
        cfg["pembukuan"] = pb
        # penerbitan sertifikat
        ps = self._cfg.get("penerbitan_sertifikat", {})
        ps.update({"enabled": self._ps_en.get(),
                   "nama":    self._ps_nama.get(),
                   "jabatan_teks":  self._ps_jab.get(),
                   "jabatan2_teks": self._ps_jab2.get()})
        cfg["penerbitan_sertifikat"] = ps
        dl_out = {}
        for key, d in self._dl.items():
            w = d["w"]
            m = getattr(w, "_mode", "single")
            if m in ("template_nama", "sisip_sebelum_kurung"):
                val_key = getattr(w, "_val_key", "template")
                entry = {"enabled": d["en"].get(),
                         val_key: w.get("1.0", "end-1c"),
                         "mode": m}
            elif m == "multiline":
                entry = {"enabled": d["en"].get(),
                         "nilai": w.get("1.0", "end-1c")}
            else:
                entry = {"enabled": d["en"].get(),
                         "nilai": w._sv.get()}
            try: entry["x"] = int(d["xv"].get())
            except (ValueError, KeyError): pass
            try: entry["y"] = int(d["yv"].get())
            except (ValueError, KeyError): pass
            dl_out[key] = entry
        cfg["detail_lain"] = dl_out
        save_config(cfg)
        self._cfg = cfg
        self._log("✅  Konfigurasi disimpan.")

    # ── log ──────────────────────────────────────────────────
    def _log(self, msg):
        line = write_log(msg)
        self._log_widget.config(state="normal")
        self._log_widget.insert("end", line)
        self._log_widget.see("end")
        self._log_widget.config(state="disabled")

    def _clear_log(self):
        self._log_widget.config(state="normal")
        self._log_widget.delete("1.0", "end")
        self._log_widget.config(state="disabled")

    # ── hotkeys global ───────────────────────────────────────
    def _bind_keys(self):
        import keyboard
        for k in ("f1","\\","f3","esc"):
            try: keyboard.remove_hotkey(k)
            except Exception: pass
        keyboard.add_hotkey("f1",   lambda: self.after(0, self._start_worker), suppress=False)
        keyboard.add_hotkey("\\",   lambda: self.after(0, self._toggle_pause), suppress=False)
        keyboard.add_hotkey("f3",   lambda: self.after(0, self._reset_worker), suppress=False)
        keyboard.add_hotkey("esc",  lambda: self.after(0, self._stop_worker),  suppress=False)

    def destroy(self):
        try:
            import keyboard; keyboard.unhook_all_hotkeys()
        except Exception: pass
        super().destroy()

    # ── status ───────────────────────────────────────────────
    def _set_status(self, msg, color=TEXT_DIM):
        self._sb_var.set(msg)
        self._status_var.set(msg)

    # ── worker controls ──────────────────────────────────────
    def _start_worker(self):
        if self._running: return
        self._set_status("💾  Menyimpan config…", TEXT_DIM)
        self._save_config()
        self._running = True
        self._paused  = False
        self._set_status("▶  Berjalan…", SUCCESS)
        self._log("▶  Memulai…")
        self._worker = threading.Thread(target=self._run_paste, daemon=True)
        self._worker.start()

    def _toggle_pause(self):
        if not self._running: return
        self._paused = not self._paused
        if self._paused:
            self._set_status("⏸  Dijeda…", WARNING)
            self._log("⏸  Dijeda.")
        else:
            self._set_status("▶  Melanjutkan…", SUCCESS)
            self._log("▶  Melanjutkan.")

    def _set_paused(self, val: bool):
        def _do():
            self._paused = val
            if val:
                self._set_status("⏸  Selesai isi — tekan F2 untuk lanjut", WARNING)
        self.after(0, _do)

    def _reset_worker(self):
        self._stop_worker()
        self._set_status("↺  Reset.", ACCENT)
        self._log("↺  Reset.")
        self._progress_var.set("Putaran: -")

    def _stop_worker(self):
        self._running = False
        self._paused  = False
        self._set_status("■  Dihentikan.", DANGER)

    def _show_cursor_pos(self):
        import pyautogui as _pg
        self._log("── Lacak Cursor 3 detik ──")
        def _t():
            for _ in range(15):
                x, y = _pg.position()
                self._log(f"   🖱  x={x}  y={y}")
                time.sleep(0.2)
            self._log("── selesai ──")
        threading.Thread(target=_t, daemon=True).start()

    def _cek_asset(self):
        def _run():
            try:
                from auto_paste_detil import cek_semua_asset
                cek_semua_asset(ASSETS_DIR, self._cfg, self._log)
            except Exception as ex:
                self._log(f"❌  Error: {ex}")
        threading.Thread(target=_run, daemon=True).start()
        self._log("🔎  Cek asset — buka halaman DETIL dulu…")

    def _run_paste(self):
        try:
            from auto_paste_detil import jalankan_paste
            jalankan_paste(
                cfg           = self._cfg,
                assets_dir    = ASSETS_DIR,
                is_running    = lambda: self._running,
                is_paused     = lambda: self._paused,
                log_fn        = self._log,
                progress_fn   = lambda m: self._progress_var.set(m),
                status_fn     = self._set_status,
                set_paused_fn = self._set_paused,
                debug         = self._debug_var.get(),
            )
        except ImportError:
            self._log("⚠️  auto_paste_detil.py tidak ditemukan.")
        except Exception as ex:
            self._log(f"❌  Error: {ex}")
        finally:
            self._running = False
            self._set_status("✅  Selesai.", SUCCESS)
            self._log("✅  Selesai.")


if __name__ == "__main__":
    app = AppDetilSU()
    app.mainloop()
