# ============================================================
#  auto_paste_detil.py  –  Logika Auto-Paste DETIL Surat Ukur
#  Versi akurat: klik langsung koordinat, triple-click clear,
#  grayscale matching, retry logic, verifikasi per-field
# ============================================================

import os
import sys
import time
import threading
import tkinter as tk
import pyautogui
import pyperclip

pyautogui.FAILSAFE = True
pyautogui.PAUSE    = 0.01   # lebih cepat


# ── path helper ──────────────────────────────────────────────
def base_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


# ════════════════════════════════════════════════════════════
#  DEBUG OVERLAY  –  lingkaran merah di titik klik
# ════════════════════════════════════════════════════════════

class _ClickMarker:
    @classmethod
    def show(cls, x, y, label="", duration=0.8):
        threading.Thread(
            target=cls._draw, args=(x, y, label, duration), daemon=True
        ).start()

    @staticmethod
    def _draw(x, y, label, duration):
        size = 44
        half = size // 2
        try:
            root = tk.Tk()
            root.overrideredirect(True)
            root.attributes("-topmost", True)
            root.attributes("-transparentcolor", "#000001")
            root.configure(bg="#000001")
            root.geometry(f"{size}x{size}+{x-half}+{y-half}")
            c = tk.Canvas(root, width=size, height=size,
                          bg="#000001", highlightthickness=0)
            c.pack()
            p = 4
            c.create_oval(p, p, size-p, size-p, outline="#ff2222", width=3)
            c.create_line(half, p+2, half, size-p-2, fill="#ff2222", width=2)
            c.create_line(p+2, half, size-p-2, half, fill="#ff2222", width=2)
            if label:
                t = tk.Toplevel(root)
                t.overrideredirect(True)
                t.attributes("-topmost", True)
                t.configure(bg="#111133")
                t.geometry(f"+{x-half}+{y-half-18}")
                tk.Label(t, text=label, bg="#111133", fg="#ffffff",
                         font=("Consolas", 7)).pack(padx=2)
            root.after(int(duration * 1000), root.destroy)
            root.mainloop()
        except Exception:
            pass


# ── state global ─────────────────────────────────────────────
_DEBUG  = False
_REGION = None   # (left, top, width, height) atau None = seluruh layar

# referensi is_running/is_paused dari jalankan_paste — diset saat mulai
_is_running_ref = None
_is_paused_ref  = None

def set_debug(val: bool):
    global _DEBUG
    _DEBUG = val

def set_region(region):
    global _REGION
    if region and len(region) == 4:
        _REGION = tuple(int(v) for v in region)
    else:
        _REGION = None

def _set_callbacks(is_running, is_paused):
    global _is_running_ref, _is_paused_ref
    _is_running_ref = is_running
    _is_paused_ref  = is_paused


# ════════════════════════════════════════════════════════════
#  UTILITAS DASAR
# ════════════════════════════════════════════════════════════

def _sleep(cfg: dict, key: str, default: float = 0.3):
    try:
        time.sleep(float(cfg.get("delay", {}).get(key, default)))
    except (ValueError, TypeError):
        time.sleep(default)


def _find_image(image_path: str, confidence: float = 0.75,
                region=None) -> object:
    """
    Cari gambar di layar dengan grayscale + confidence turun bertahap.
    region override: pakai parameter jika diberikan, else pakai _REGION global.
    Return Box atau None.
    """
    search_region = region if region is not None else _REGION
    # grayscale lebih akurat & lebih cepat daripada warna
    for conf in [confidence, confidence - 0.1, confidence - 0.2]:
        conf = max(conf, 0.5)
        try:
            loc = pyautogui.locateOnScreen(
                image_path,
                confidence=conf,
                region=search_region,
                grayscale=True
            )
            if loc:
                return loc
        except pyautogui.ImageNotFoundException:
            pass
        except Exception:
            pass
    return None


def _wait_image(image_path: str, confidence: float = 0.75,
                timeout: float = None, interval: float = 0.3,
                is_running=None, is_paused=None,
                log_fn=None) -> object:
    """
    Tunggu gambar muncul di layar.
    - timeout=None  → tunggu selamanya sampai ditemukan atau is_running() False
    - timeout=angka → berhenti setelah N detik
    Setiap 5 detik belum ketemu, log pesan tunggu.
    """
    img_name = os.path.basename(image_path)
    start    = time.time()
    last_log = start
    attempt  = 0

    while True:
        # cek apakah proses masih berjalan
        if is_running is not None and not is_running():
            return None
        # tunggu saat dijeda
        if is_paused is not None:
            while is_paused() and (is_running is None or is_running()):
                time.sleep(0.1)
            if is_running is not None and not is_running():
                return None

        attempt += 1
        loc = _find_image(image_path, confidence)
        if loc:
            elapsed = time.time() - start
            if attempt > 1 and log_fn:
                log_fn(f"    ✅  Ditemukan setelah {elapsed:.1f}s ({attempt} percobaan)")
            return loc

        now = time.time()
        # log setiap 5 detik
        if log_fn and (now - last_log) >= 5.0:
            elapsed = now - start
            log_fn(f"    ⏳  Menunggu '{img_name}'… {elapsed:.0f}s")
            last_log = now

        # cek timeout jika diset
        if timeout is not None and (now - start) >= timeout:
            return None

        time.sleep(interval)


def _klik(x: int, y: int, label: str = "", delay_after: float = 0.2):
    """Klik koordinat absolut. Tampilkan marker jika debug aktif."""
    # Batasi koordinat agar tidak klik di luar area konten browser
    # (header browser, taskbar, sidebar)
    if _REGION:
        batas_x_min = _REGION[0]
        batas_y_min = _REGION[1]
        batas_x_max = _REGION[0] + _REGION[2]
        batas_y_max = _REGION[1] + _REGION[3]
        if not (batas_x_min <= x <= batas_x_max and
                batas_y_min <= y <= batas_y_max):
            # Log warning tapi tetap klik — mungkin region kurang tepat
            pass

    if _DEBUG:
        _ClickMarker.show(x, y, label=f"({x},{y}) {label}", duration=0.6)
        time.sleep(0.5)
    pyautogui.click(x, y)
    time.sleep(delay_after)


def _isi_field(x: int, y: int, nilai: str, cfg: dict,
               label: str = "", log_fn=None):
    """
    Klik field di (x,y), triple-click select all isi field, lalu paste.
    Menggunakan klik 3x di posisi yang SAMA (bukan Ctrl+A) agar tidak
    menggeser fokus ke luar form.
    """
    # 1. Klik sekali untuk fokus ke field
    _klik(x, y, label=label, delay_after=0.1)
    # 2. Triple-click di posisi yang sama untuk select semua isi field
    pyautogui.click(x, y, clicks=3, interval=0.07)
    time.sleep(0.08)
    # 3. Paste via clipboard
    pyperclip.copy(str(nilai))
    pyautogui.hotkey("ctrl", "v")
    _sleep(cfg, "setelah_ketik", 0.3)
    if log_fn:
        log_fn(f"    → ({x},{y}) '{nilai}'")


def _tab(n: int = 1, delay: float = 0.2):
    """Tekan Tab n kali."""
    for _ in range(n):
        pyautogui.press("tab")
        time.sleep(delay)


def _fokus_ke_form(cfg: dict, log_fn):
    """
    Klik area kosong di dalam konten form untuk memastikan fokus
    ada di dalam halaman DETIL — bukan di header/breadcrumb browser.

    Koordinat bisa diset manual di config: fokus_form: [x, y]
    Jika tidak diset, otomatis hitung dari region pencarian.
    """
    manual = cfg.get("fokus_form")
    if manual and len(manual) == 2:
        fx, fy = int(manual[0]), int(manual[1])
    elif _REGION:
        # tengah horizontal, 40px dari atas region = area judul form
        fx = _REGION[0] + _REGION[2] // 2
        fy = _REGION[1] + 40
    else:
        fx, fy = 400, 180
    log_fn(f"  [FOKUS] ({fx},{fy})")
    pyautogui.click(fx, fy)
    time.sleep(float(cfg.get("delay", {}).get("setelah_klik", 0.25)))


# ════════════════════════════════════════════════════════════
#  IMAGE SEARCH HELPER
# ════════════════════════════════════════════════════════════

def _cari_dan_klik(image_path: str, offset_x: int = 0, offset_y: int = 0,
                   confidence: float = 0.75, timeout: float = None,
                   log_fn=None, label: str = "", delay_after: float = 0.4,
                   is_running=None, is_paused=None) -> tuple:
    """
    Tunggu gambar muncul (selamanya jika timeout=None), lalu klik tengah+offset.
    Return (cx, cy) jika berhasil, (None, None) jika berhenti.
    """
    loc = _wait_image(image_path, confidence, timeout=timeout,
                      is_running=is_running, is_paused=is_paused,
                      log_fn=log_fn)
    if loc is None:
        return None, None
    cx = loc.left + loc.width  // 2 + offset_x
    cy = loc.top  + loc.height // 2 + offset_y
    _klik(cx, cy, label=label or os.path.basename(image_path),
          delay_after=delay_after)
    return cx, cy


# ════════════════════════════════════════════════════════════
#  AKSI: SERI
# ════════════════════════════════════════════════════════════

def aksi_seri(cfg: dict, assets_dir: str, log_fn, nilai: str) -> bool:
    img = os.path.join(assets_dir, "label_field_seri.png")
    if not os.path.exists(img):
        log_fn("  [SERI] ℹ️  Image tidak ada, skip.")
        return False
    log_fn("  [SERI] ⏳  Menunggu field Seri…")
    cx, cy = _cari_dan_klik(img, offset_x=80, confidence=0.75,
                             timeout=None,
                             is_running=_is_running_ref,
                             is_paused=_is_paused_ref,
                             log_fn=log_fn, label="Seri input")
    if cx is None:
        log_fn("  [SERI] ■  Dihentikan.")
        return False
    _isi_field(cx, cy, nilai, cfg, label="Seri", log_fn=log_fn)
    log_fn(f"  [SERI] ✅  '{nilai}'")
    return True


# ════════════════════════════════════════════════════════════
#  AKSI: PENOMORAN  –  field Tgl. Penemoran
# ════════════════════════════════════════════════════════════

def aksi_penomoran(cfg: dict, log_fn) -> bool:
    """Isi field Tgl. Penemoran via koordinat absolut."""
    pen = cfg.get("penomoran", {})
    if not pen.get("tanggal_enabled", False):
        log_fn("  [PENOMORAN] ⏭  Dilewati.")
        return True

    nilai = str(pen.get("tanggal_nilai", ""))
    x     = int(pen.get("tanggal_x", 370))
    y     = int(pen.get("tanggal_y", 612))

    if not nilai.strip():
        log_fn("  [PENOMORAN] ⏭  Nilai kosong, lewati.")
        return True

    log_fn(f"  [PENOMORAN] Tgl. Penemoran ({x},{y}) → '{nilai}'")
    _isi_field(x, y, nilai, cfg, label="Tgl Penomoran", log_fn=log_fn)
    log_fn("  [PENOMORAN] ✅")
    return True
#
#  Layout per baris di browser:
#  [ DI 303 ] [ Nomor........... ] [ Tahun.. ] [ Tanggal......... ] [📅]
#
#  Strategi:
#  - Temukan label "DI 303" (gambar) → dapat posisi (cx, cy)
#  - Klik LANGSUNG ke (cx+off_nomor, cy) untuk field Nomor
#  - Klik LANGSUNG ke (cx+off_tahun, cy) untuk field Tahun
#  - Klik LANGSUNG ke (cx+off_tanggal, cy) untuk field Tanggal
#  - DI disabled → Tab 4x (lewati 3 field + 1 icon kalender)
# ════════════════════════════════════════════════════════════

_OFF_NOMOR   = 110
_OFF_TAHUN   = 250
_OFF_TANGGAL = 370


def _isi_dengan_klik(x: int, y: int, val: str, nama: str,
                     cfg: dict, col_id: str, log_fn):
    """Klik koordinat (x,y) lalu triple-click select-all dan paste."""
    if not val.strip():
        log_fn(f"    {nama}: (biarkan)")
        return
    _isi_field(x, y, val, cfg, label=f"{col_id} {nama}", log_fn=log_fn)


def aksi_satu_kolom_di(cfg: dict, assets_dir: str, log_fn,
                       kolom: dict) -> bool:
    col_id = kolom.get("id", "?")

    if not kolom.get("enabled", True):
        log_fn(f"  [{col_id}] ⏭  Skip (disabled).")
        return True

    nomor   = str(kolom.get("nomor",   ""))
    tahun   = str(kolom.get("tahun",   ""))
    tanggal = str(kolom.get("tanggal", ""))

    # ── MODE KOORDINAT PER-FIELD ──────────────────────────────
    # Tiap field diklik langsung ke koordinatnya — tidak pakai Tab sama sekali
    ky        = kolom.get("y")
    x_nomor   = kolom.get("x_nomor")
    x_tahun   = kolom.get("x_tahun")
    x_tanggal = kolom.get("x_tanggal")

    # Juga dukung format lama: x + y (pakai offset dari config)
    if ky is None:
        ky = kolom.get("y")
    if x_nomor is None and kolom.get("x") is not None:
        di_off  = cfg.get("di_offset", {})
        base_x  = int(kolom.get("x"))
        ky      = int(kolom.get("y", 0))
        x_nomor   = base_x + int(di_off.get("nomor",   _OFF_NOMOR))
        x_tahun   = base_x + int(di_off.get("tahun",   _OFF_TAHUN))
        x_tanggal = base_x + int(di_off.get("tanggal", _OFF_TANGGAL))

    if ky is not None and x_nomor is not None:
        ky        = int(ky)
        x_nomor   = int(x_nomor)
        x_tahun   = int(x_tahun)   if x_tahun   is not None else x_nomor + 140
        x_tanggal = int(x_tanggal) if x_tanggal is not None else x_nomor + 280

        log_fn(f"  [{col_id}] 📍 y={ky} | "
               f"Nomor x={x_nomor}  Tahun x={x_tahun}  Tanggal x={x_tanggal}")

        _isi_dengan_klik(x_nomor,   ky, nomor,   "Nomor",   cfg, col_id, log_fn)
        _isi_dengan_klik(x_tahun,   ky, tahun,   "Tahun",   cfg, col_id, log_fn)
        _isi_dengan_klik(x_tanggal, ky, tanggal, "Tanggal", cfg, col_id, log_fn)
        return True

    # ── MODE IMAGE ────────────────────────────────────────────
    di_off   = cfg.get("di_offset", {})
    off_nom  = int(di_off.get("nomor",   _OFF_NOMOR))
    off_thn  = int(di_off.get("tahun",   _OFF_TAHUN))
    off_tgl  = int(di_off.get("tanggal", _OFF_TANGGAL))
    img_name = kolom.get("image", "")
    img_path = os.path.join(assets_dir, img_name)

    if img_name and os.path.exists(img_path):
        try:
            from PIL import Image as _Im
            with _Im.open(img_path) as im:
                pw, ph = im.size
            px_info = f"{pw}×{ph}px"
        except Exception:
            px_info = "?"

        log_fn(f"  [{col_id}] 🔍 '{img_name}' ({px_info}) — menunggu…")
        loc = _wait_image(img_path, confidence=0.75, timeout=None,
                          is_running=_is_running_ref,
                          is_paused=_is_paused_ref, log_fn=log_fn)
        if loc is None:
            log_fn(f"  [{col_id}] ■  Dihentikan.")
            return False

        cx  = loc.left + loc.width  // 2
        cy  = loc.top  + loc.height // 2
        off_y = int(di_off.get("offset_y", 0))
        ky2   = cy + off_y
        log_fn(f"  [{col_id}] ✅ label=({cx},{cy}) → y={ky2}")

        _isi_dengan_klik(cx+off_nom, ky2, nomor,   "Nomor",   cfg, col_id, log_fn)
        _isi_dengan_klik(cx+off_thn, ky2, tahun,   "Tahun",   cfg, col_id, log_fn)
        _isi_dengan_klik(cx+off_tgl, ky2, tanggal, "Tanggal", cfg, col_id, log_fn)

    # ── MODE FALLBACK ─────────────────────────────────────────
    else:
        log_fn(f"  [{col_id}] ℹ️  Tidak ada koordinat/image.")
        delay_t = float(cfg.get("delay", {}).get("setelah_tab", 0.2))

        def _tab_isi(val, nama):
            if val.strip():
                pyautogui.click(clicks=3, interval=0.1)
                time.sleep(0.1)
                pyperclip.copy(val)
                pyautogui.hotkey("ctrl", "v")
                _sleep(cfg, "setelah_ketik", 0.3)
                log_fn(f"    {nama}: '{val}'")
            else:
                log_fn(f"    {nama}: (biarkan)")
            _tab(1, delay_t)

        _tab_isi(nomor,   "Nomor")
        _tab_isi(tahun,   "Tahun")
        _tab_isi(tanggal, "Tanggal")

    return True


# ════════════════════════════════════════════════════════════
#  AKSI: DETAIL LAIN-LAIN
#
#  Murni Tab — tidak pakai image.
#  Tiap field dilewati dengan Tab 1x (meski disabled),
#  agar posisi cursor selalu sinkron.
#
#  Urutan field di halaman:
#    Keadaan Tanah → Tanda-Tanda Batas → Pengukuran → Hal Lain-Lain
#
#  Asumsi masuk: cursor di field Tanggal baris DI terakhir yang diproses.
#  Dari sana ke Keadaan Tanah ada beberapa Tab — nilai di config:
#    tab_sebelum_detail  (default 1)
# ════════════════════════════════════════════════════════════

_URUTAN_DETAIL = [
    ("keadaan_tanah",          "Keadaan Tanah"),
    ("tanda_tanda_batas",      "Tanda-Tanda Batas"),
    ("pengukuran_dan_pemetaan","Penunjukan dan Penetapan Batas"),
    ("hal_lain_lain",          "Hal Lain-Lain"),
]


# ════════════════════════════════════════════════════════════
#  AKSI: PEMBUKUAN
# ════════════════════════════════════════════════════════════

def _ketik_dropdown(teks: str, cfg: dict, log_fn, label: str = ""):
    """
    Untuk field dropdown: klik field → ketik untuk filter → Enter untuk pilih.
    Berbeda dari _ketik biasa yang hanya paste.
    """
    # Clear field lalu ketik teks filter
    pyautogui.hotkey("ctrl", "a")
    time.sleep(0.05)
    pyperclip.copy(str(teks))
    pyautogui.hotkey("ctrl", "v")
    time.sleep(0.25)   # tunggu dropdown filter tampil
    # Enter untuk pilih item pertama dari dropdown
    pyautogui.press("enter")
    _sleep(cfg, "setelah_ketik", 0.3)
    if log_fn:
        log_fn(f"    {label}: '{teks}' (dropdown→Enter)")


def _ketik(teks: str, cfg: dict, log_fn, label: str = ""):
    """Triple-click select-all lalu paste teks biasa (bukan dropdown)."""
    pyautogui.click(clicks=3, interval=0.07)
    time.sleep(0.07)
    pyperclip.copy(str(teks))
    pyautogui.hotkey("ctrl", "v")
    _sleep(cfg, "setelah_ketik", 0.15)
    if log_fn:
        log_fn(f"    {label}: '{teks}'")


def aksi_pembukuan(cfg: dict, log_fn, cfg_key: str = "pembukuan") -> bool:
    """
    Isi section Pembukuan (SU atau BT via cfg_key).
    Alur:
      1. Centang checkbox
      2. Klik jabatan_x/y → paste jabatan
      3. Klik jabatan_klik2_x/y → paste jabatan (konfirmasi/pilih dropdown)
      4. Klik nama_x/y → paste nama
      5. Klik nama_klik2_x/y (konfirmasi)
    """
    pen = cfg.get(cfg_key, {})
    if not pen.get("enabled", False):
        log_fn(f"  [{cfg_key.upper()}] ⏭  Skip.")
        return True

    nama         = str(pen.get("nama", ""))
    jabatan_teks = str(pen.get("jabatan_teks", ""))
    cx,  cy   = int(pen.get("centang_x",       0)), int(pen.get("centang_y",       0))
    jx,  jy   = int(pen.get("jabatan_x",       0)), int(pen.get("jabatan_y",       0))
    jx2, jy2  = int(pen.get("jabatan_klik2_x", 0)), int(pen.get("jabatan_klik2_y", 0))
    nx,  ny   = int(pen.get("nama_x",          0)), int(pen.get("nama_y",          0))
    nx2, ny2  = int(pen.get("nama_klik2_x",    0)), int(pen.get("nama_klik2_y",    0))

    log_fn(f"  [{cfg_key.upper()}] Mulai…")

    # 1. Centang — hanya jika centang_enabled: true
    if pen.get("centang_enabled", False) and cx and cy:
        _klik(cx, cy, label="centang", delay_after=0.2)
        log_fn(f"    ✓ Centang ({cx},{cy})")
    else:
        log_fn(f"    ↷ Centang dilewati.")

    # 2. Klik jabatan → paste
    if jx and jy:
        _klik(jx, jy, label="jabatan klik1", delay_after=0.15)
        pyautogui.hotkey("ctrl", "a"); time.sleep(0.05)
        pyperclip.copy(jabatan_teks); pyautogui.hotkey("ctrl", "v")
        _sleep(cfg, "setelah_ketik", 0.15)
        log_fn(f"    Jabatan → '{jabatan_teks}'")

    # 3. Klik jabatan klik2 → paste (konfirmasi/pilih dari list)
    if jx2 and jy2:
        _klik(jx2, jy2, label="jabatan klik2", delay_after=0.15)
        pyautogui.hotkey("ctrl", "a"); time.sleep(0.05)
        pyperclip.copy(jabatan_teks); pyautogui.hotkey("ctrl", "v")
        _sleep(cfg, "setelah_ketik", 0.15)
        log_fn(f"    Jabatan klik2 → '{jabatan_teks}'")

    # 4. Klik nama → paste
    if nx and ny:
        _klik(nx, ny, label="nama klik1", delay_after=0.15)
        pyautogui.hotkey("ctrl", "a"); time.sleep(0.05)
        pyperclip.copy(nama); pyautogui.hotkey("ctrl", "v")
        _sleep(cfg, "setelah_ketik", 0.15)
        log_fn(f"    Nama → '{nama}'")

    # 5. Klik nama klik2 (konfirmasi)
    if nx2 and ny2:
        _klik(nx2, ny2, label="nama klik2", delay_after=0.15)
        pyautogui.hotkey("ctrl", "a"); time.sleep(0.05)
        pyperclip.copy(nama); pyautogui.hotkey("ctrl", "v")
        _sleep(cfg, "setelah_ketik", 0.15)
        log_fn(f"    Nama klik2 → '{nama}'")

    log_fn(f"  [{cfg_key.upper()}] ✅")
    return True


def aksi_penerbitan_sertifikat(cfg: dict, log_fn,
                                cfg_key: str = "penerbitan_sertifikat") -> bool:
    """
    Isi section Penerbitan Sertifikat (SU atau BT via cfg_key).
    Alur identik dengan Pembukuan — jabatan & nama masing-masing 2 klik.
    """
    pen = cfg.get(cfg_key, {})
    if not pen.get("enabled", False):
        log_fn(f"  [{cfg_key.upper()}] ⏭  Skip.")
        return True

    nama         = str(pen.get("nama", ""))
    jabatan_teks = str(pen.get("jabatan_teks", ""))
    cx,  cy   = int(pen.get("centang_x",       0)), int(pen.get("centang_y",       0))
    jx,  jy   = int(pen.get("jabatan_x",       0)), int(pen.get("jabatan_y",       0))
    jx2, jy2  = int(pen.get("jabatan_klik2_x", 0)), int(pen.get("jabatan_klik2_y", 0))
    nx,  ny   = int(pen.get("nama_x",          0)), int(pen.get("nama_y",          0))
    nx2, ny2  = int(pen.get("nama_klik2_x",    0)), int(pen.get("nama_klik2_y",    0))

    log_fn(f"  [{cfg_key.upper()}] Mulai…")

    if cx and cy:
        _klik(cx, cy, label="centang", delay_after=0.2)
        log_fn(f"    ✓ Centang ({cx},{cy})")

    if jx and jy:
        _klik(jx, jy, label="jabatan klik1", delay_after=0.15)
        pyautogui.hotkey("ctrl", "a"); time.sleep(0.05)
        pyperclip.copy(jabatan_teks); pyautogui.hotkey("ctrl", "v")
        _sleep(cfg, "setelah_ketik", 0.15)
        log_fn(f"    Jabatan → '{jabatan_teks}'")

    if jx2 and jy2:
        _klik(jx2, jy2, label="jabatan klik2", delay_after=0.15)
        pyautogui.hotkey("ctrl", "a"); time.sleep(0.05)
        pyperclip.copy(jabatan_teks); pyautogui.hotkey("ctrl", "v")
        _sleep(cfg, "setelah_ketik", 0.15)
        log_fn(f"    Jabatan klik2 → '{jabatan_teks}'")

    if nx and ny:
        _klik(nx, ny, label="nama klik1", delay_after=0.15)
        pyautogui.hotkey("ctrl", "a"); time.sleep(0.05)
        pyperclip.copy(nama); pyautogui.hotkey("ctrl", "v")
        _sleep(cfg, "setelah_ketik", 0.15)
        log_fn(f"    Nama → '{nama}'")

    if nx2 and ny2:
        _klik(nx2, ny2, label="nama klik2", delay_after=0.15)
        pyautogui.hotkey("ctrl", "a"); time.sleep(0.05)
        pyperclip.copy(nama); pyautogui.hotkey("ctrl", "v")
        _sleep(cfg, "setelah_ketik", 0.15)
        log_fn(f"    Nama klik2 → '{nama}'")

    log_fn(f"  [{cfg_key.upper()}] ✅")
    return True


def aksi_detail_lain(cfg: dict, assets_dir: str, log_fn,
                     detail_cfg: dict) -> bool:
    """
    Isi Detail Lain-Lain via koordinat absolut (klik langsung, tidak pakai Tab).

    Mode per-field di config:
      default             → klik (x,y) → triple-click → paste nilai
      sisip_sebelum_kurung → klik (x,y) → salin isi lama → sisipkan
                             teks_tambah di baris ke-2 sebelum karakter '('
    """
    for key, lbl_text in _URUTAN_DETAIL:
        sub = detail_cfg.get(key, {})
        if not sub.get("enabled", False):
            log_fn(f"  [{lbl_text}] ⏭  Skip.")
            continue

        x = int(sub.get("x", 0))
        y = int(sub.get("y", 0))
        if x == 0 or y == 0:
            log_fn(f"  [{lbl_text}] ⚠️  Koordinat belum diset, skip.")
            continue

        mode = sub.get("mode", "default")

        if mode == "template_nama":
            # ── Ambil nama dari field, susun teks dengan template ──
            template = str(sub.get("template", "{nama}"))

            # 1. Klik field
            _klik(x, y, label=lbl_text, delay_after=0.15)

            # 2. Ctrl+A → Ctrl+C ambil isi lama (nama saja, misal "ROMLI")
            pyautogui.hotkey("ctrl", "a")
            time.sleep(0.15)
            pyautogui.hotkey("ctrl", "c")
            time.sleep(0.25)
            isi_lama = pyperclip.paste().strip()

            # Jika isi lama sudah berupa teks panjang (bukan hanya nama),
            # coba ekstrak nama: ambil kata-kata sebelum '(' atau baris pertama
            nama = isi_lama
            if "(" in nama:
                # ambil teks sebelum '(' di baris yang mengandung '('
                for baris in nama.splitlines():
                    if "(" in baris:
                        nama = baris[:baris.index("(")].strip()
                        break
            elif "\n" in nama:
                # ambil baris pertama yang tidak kosong
                for baris in nama.splitlines():
                    if baris.strip():
                        nama = baris.strip()
                        break

            log_fn(f"  [{lbl_text}] Nama diambil: {nama!r}")

            # 3. Susun teks baru dari template
            teks_baru = template.replace("{nama}", nama)
            log_fn(f"  [{lbl_text}] Teks baru:\n{teks_baru}")

            # 4. Paste teks baru
            pyperclip.copy(teks_baru)
            pyautogui.hotkey("ctrl", "a")
            time.sleep(0.05)
            pyautogui.hotkey("ctrl", "v")
            _sleep(cfg, "setelah_ketik", 0.4)
            log_fn(f"  [{lbl_text}] ✅  Template selesai.")

        elif mode == "sisip_sebelum_kurung":
            # ── Mode lama — masih didukung ──────────────────
            teks_tambah = str(sub.get("teks_tambah", ""))
            _klik(x, y, label=lbl_text, delay_after=0.15)
            pyautogui.hotkey("ctrl", "a")
            time.sleep(0.15)
            pyautogui.hotkey("ctrl", "c")
            time.sleep(0.25)
            isi_lama = pyperclip.paste()
            idx_kurung = isi_lama.find("(")
            if idx_kurung == -1:
                idx_nl = isi_lama.find("\n")
                idx_sisip = idx_nl + 1 if idx_nl != -1 else len(isi_lama)
                teks_baru = (isi_lama[:idx_sisip] + teks_tambah + "\n"
                             + isi_lama[idx_sisip:])
            else:
                idx_awal = isi_lama.rfind("\n", 0, idx_kurung)
                idx_awal = idx_awal + 1 if idx_awal != -1 else 0
                teks_baru = (isi_lama[:idx_awal] + teks_tambah + "\n"
                             + isi_lama[idx_awal:])
            pyperclip.copy(teks_baru)
            pyautogui.hotkey("ctrl", "a")
            time.sleep(0.05)
            pyautogui.hotkey("ctrl", "v")
            _sleep(cfg, "setelah_ketik", 0.4)
            log_fn(f"  [{lbl_text}] ✅  Sisip selesai.")

        else:
            # ── Mode default: klik → triple-click → paste ────
            nilai = str(sub.get("nilai", ""))
            if not nilai.strip():
                log_fn(f"  [{lbl_text}] ⏭  Nilai kosong, skip.")
                continue
            _isi_field(x, y, nilai, cfg, label=lbl_text, log_fn=log_fn)
            log_fn(f"  [{lbl_text}] ✅  Diisi.")

    return True


# ════════════════════════════════════════════════════════════
#  DIAGNOSTIK ASSET
# ════════════════════════════════════════════════════════════

def cek_semua_asset(assets_dir: str, cfg: dict, log_fn):
    """Cek setiap image DI: ada file? ukuran cukup? ditemukan di layar?"""
    set_region(cfg.get("search_region", None))
    sw, sh = pyautogui.size()
    log_fn(f"═══ DIAGNOSTIK  |  Layar: {sw}×{sh}  |  "
           f"Region: {_REGION or 'seluruh layar'} ═══")

    kolom_list = cfg.get("daftar_isian", {}).get("kolom", [])
    ok = err = 0

    for k in kolom_list:
        lid      = k.get("id", "?")
        img_name = k.get("image", "")
        if not img_name:
            log_fn(f"  ➖  [{lid}] image kosong — skip.")
            continue

        img_path = os.path.join(assets_dir, img_name)
        if not os.path.exists(img_path):
            log_fn(f"  ❌  [{lid}] '{img_name}' — FILE TIDAK ADA di assets/")
            err += 1
            continue

        sz = os.path.getsize(img_path)
        try:
            from PIL import Image as _Im
            with _Im.open(img_path) as im:
                pw, ph = im.size
            px_info = f"{pw}×{ph}px / {sz}B"
            kecil = pw < 30 or ph < 10
        except Exception:
            px_info = f"{sz}B"
            kecil = sz < 500

        if kecil:
            log_fn(f"  ❌  [{lid}] '{img_name}' ({px_info}) "
                   f"— TERLALU KECIL, crop ulang lebih besar (min 30×10px)")
            err += 1
            continue

        loc = _find_image(img_path, confidence=0.7)
        if loc:
            cx = loc.left + loc.width  // 2
            cy = loc.top  + loc.height // 2
            log_fn(f"  ✅  [{lid}] '{img_name}' ({px_info}) "
                   f"— ditemukan ({loc.left},{loc.top}) "
                   f"{loc.width}×{loc.height}px  tengah=({cx},{cy})")
            ok += 1
        else:
            log_fn(f"  ⚠️  [{lid}] '{img_name}' ({px_info}) "
                   f"— TIDAK DITEMUKAN di region. "
                   f"Zoom browser 100%? Warna UI berubah? Crop ulang?")
            err += 1

    log_fn(f"═══ {ok} OK  |  {err} GAGAL ═══")

    if ok > 0:
        log_fn("💡 TIP offset: dari koordinat tengah label, "
               f"tambah offset nomor/tahun/tanggal dari config di_offset.")


# ════════════════════════════════════════════════════════════
#  AKSI: SIMPAN
# ════════════════════════════════════════════════════════════

def aksi_simpan(cfg: dict, assets_dir: str, log_fn) -> bool:
    for img_name in ["label_tanda_seru.png", "Validasi_button.png",
                     "validasiBT.png"]:
        img = os.path.join(assets_dir, img_name)
        if not os.path.exists(img):
            continue
        cx, cy = _cari_dan_klik(img, confidence=0.75, timeout=5.0,
                                 log_fn=log_fn, label="Simpan")
        if cx is not None:
            log_fn(f"  [SIMPAN] ✅  '{img_name}'")
            _sleep(cfg, "setelah_klik", 0.5)
            return True
    log_fn("  [SIMPAN] ⚠️  Tombol tidak ditemukan.")
    return False


# ════════════════════════════════════════════════════════════
#  FUNGSI UTAMA
# ════════════════════════════════════════════════════════════

def jalankan_paste(cfg, assets_dir, is_running, is_paused,
                   log_fn, progress_fn, status_fn,
                   set_paused_fn=None, debug=False):
    """Loop auto-paste DETIL SU. Berhenti saat ESC atau is_running() False."""

    set_debug(debug)
    set_region(cfg.get("search_region", None))
    _set_callbacks(is_running, is_paused)

    if debug:
        log_fn("🔴  MODE DEBUG — tanda merah di tiap klik")

    log_fn("═" * 52)
    log_fn("  AUTO-PASTE DETIL SU  |  F2=Jeda  ESC=Stop")
    log_fn("═" * 52)

    seri_cfg    = cfg.get("seri",         {})
    di_cfg      = cfg.get("daftar_isian", {})
    detail_cfg  = cfg.get("detail_lain",  {})
    kolom_list  = di_cfg.get("kolom", []) if di_cfg.get("enabled", True) else []
    delay_loop  = float(cfg.get("delay", {}).get("antar_putaran", 1.0))
    rec_idx     = 0

    while is_running():

        # jeda
        if is_paused():
            status_fn("⏸  Dijeda…")
            while is_paused() and is_running():
                time.sleep(0.2)
            if not is_running():
                break

        rec_idx += 1
        progress_fn(f"Putaran ke-{rec_idx}")
        log_fn(f"\n── Putaran {rec_idx} ─────────────────────────────")
        status_fn(f"▶  Putaran {rec_idx}…")

        # 1. Tab DETIL
        img_tab = os.path.join(assets_dir, "label_tab_detil.png")
        if os.path.exists(img_tab):
            log_fn("  [TAB] ⏳  Menunggu tab DETIL…")
            cx, cy = _cari_dan_klik(img_tab, confidence=0.75,
                                    timeout=None,
                                    is_running=is_running,
                                    is_paused=is_paused,
                                    log_fn=log_fn, label="Tab DETIL")
            if cx:
                log_fn("  [TAB] ✅")
                _sleep(cfg, "setelah_klik", 0.5)
            else:
                log_fn("  [TAB] ■  Dihentikan.")
                break
        if not is_running(): break

        # Pastikan fokus ada di dalam konten form, bukan di header browser
        _fokus_ke_form(cfg, log_fn)

        # 2. Seri — dihapus
        if not is_running(): break

        # 2b. Tgl. Penemoran
        aksi_penomoran(cfg, log_fn)
        if not is_running(): break

        # 2c. Pembukuan
        aksi_pembukuan(cfg, log_fn)
        if not is_running(): break

        # 2d. Penerbitan Sertifikat
        aksi_penerbitan_sertifikat(cfg, log_fn)
        if not is_running(): break

        # 3. Daftar Isian
        if di_cfg.get("enabled", True) and kolom_list:
            for kolom in kolom_list:
                if not is_running(): break
                while is_paused() and is_running():
                    time.sleep(0.2)
                aksi_satu_kolom_di(cfg, assets_dir, log_fn, kolom)
                _sleep(cfg, "antar_field", 0.4)
        else:
            log_fn("  [DI] ⏭")
        if not is_running(): break

        # 4. Detail Lain-Lain
        aksi_detail_lain(cfg, assets_dir, log_fn, detail_cfg)
        if not is_running(): break

        # 5. Simpan
        aksi_simpan(cfg, assets_dir, log_fn)

        log_fn(f"✅  Putaran {rec_idx} selesai.")

        # ── Otomatis jeda setelah selesai isi ────────────────
        log_fn("⏸  Selesai isi — tekan \\ untuk lanjut ke record berikutnya…")
        status_fn("⏸  Selesai isi — tekan \\ untuk lanjut")
        if set_paused_fn:
            set_paused_fn(True)
        # Tunggu sampai di-unpause (is_paused() False) atau di-stop
        while is_paused() and is_running():
            time.sleep(0.1)
        if not is_running():
            break

        log_fn("▶  Melanjutkan ke record berikutnya…")

    log_fn(f"\n■  Berhenti. Total putaran: {rec_idx}")


# ════════════════════════════════════════════════════════════
#  BUKU TANAH (BT) — loop auto-paste
# ════════════════════════════════════════════════════════════

def jalankan_paste_bt(cfg, assets_dir, is_running, is_paused,
                      log_fn, progress_fn, status_fn,
                      set_paused_fn=None, debug=False):
    """
    Loop auto-paste Buku Tanah.
    Hanya mengisi Daftar Isian BT (DI 301 dst) via koordinat absolut.
    """
    set_debug(debug)
    set_region(cfg.get("search_region", None))
    _set_callbacks(is_running, is_paused)

    log_fn("═" * 52)
    log_fn("  AUTO-PASTE BUKU TANAH (BT)  |  \\=Jeda  ESC=Stop")
    log_fn("═" * 52)

    bt_cfg      = cfg.get("bt", {})
    di_cfg      = bt_cfg.get("daftar_isian", {})
    kolom_list  = di_cfg.get("kolom", []) if di_cfg.get("enabled", True) else []
    delay_loop  = float(cfg.get("delay", {}).get("antar_putaran", 1.0))
    rec_idx     = 0

    while is_running():

        if is_paused():
            status_fn("⏸  Dijeda…")
            while is_paused() and is_running():
                time.sleep(0.2)
            if not is_running():
                break

        rec_idx += 1
        progress_fn(f"Putaran ke-{rec_idx}")
        log_fn(f"\n── BT Putaran {rec_idx} ──────────────────────────")
        status_fn(f"▶  BT Putaran {rec_idx}…")

        # Fokus ke form
        _fokus_ke_form(cfg, log_fn)
        if not is_running(): break

        # Pembukuan BT
        aksi_pembukuan(cfg, log_fn, cfg_key="pembukuan_bt")
        if not is_running(): break

        # Penerbitan Sertifikat BT
        aksi_penerbitan_sertifikat(cfg, log_fn, cfg_key="penerbitan_sertifikat_bt")
        if not is_running(): break

        # Isi semua kolom DI BT
        if di_cfg.get("enabled", True) and kolom_list:
            for kolom in kolom_list:
                if not is_running(): break
                while is_paused() and is_running():
                    time.sleep(0.2)
                aksi_satu_kolom_di(cfg, assets_dir, log_fn, kolom)
                _sleep(cfg, "antar_field", 0.4)
        else:
            log_fn("  [BT DI] ⏭  Dilewati.")
        if not is_running(): break

        # Simpan
        aksi_simpan(cfg, assets_dir, log_fn)
        log_fn(f"✅  BT Putaran {rec_idx} selesai.")

        # Otomatis jeda
        log_fn("⏸  BT Selesai isi — tekan ` untuk lanjut ke record berikutnya…")
        status_fn("⏸  BT Selesai — tekan ` untuk lanjut")
        if set_paused_fn:
            set_paused_fn(True)
        # Tunggu sampai di-unpause atau di-stop
        while is_paused() and is_running():
            time.sleep(0.1)
        if not is_running():
            break

        log_fn("▶  BT Melanjutkan ke record berikutnya…")

    log_fn(f"\n■  BT Berhenti. Total putaran: {rec_idx}")
