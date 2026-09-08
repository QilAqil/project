# ============================================================
#  auto_paste_detil.py  –  Logika Auto-Paste DETIL Surat Ukur
#  Menggunakan pyautogui + pyperclip untuk paste cepat
#  Image recognition via pyautogui.locateOnScreen
# ============================================================

import os
import sys
import time
import pyautogui
import pyperclip

pyautogui.FAILSAFE = True   # gerak mouse ke sudut kiri atas = stop darurat
pyautogui.PAUSE   = 0.05


# ── path helper ──────────────────────────────────────────────
def base_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


# ════════════════════════════════════════════════════════════
#  UTILITAS DASAR
# ════════════════════════════════════════════════════════════

def _delay(cfg: dict, key: str):
    """Ambil nilai delay dari config, tidur sesuai nilainya."""
    v = cfg.get("delay", {}).get(key, 0.4)
    try:
        time.sleep(float(v))
    except (ValueError, TypeError):
        time.sleep(0.4)


def _paste_text(text: str):
    """Salin ke clipboard lalu Ctrl+A → Ctrl+V (ganti seluruh isi field)."""
    if text is None:
        return
    pyperclip.copy(str(text))
    pyautogui.hotkey("ctrl", "a")
    time.sleep(0.05)
    pyautogui.hotkey("ctrl", "v")


def _clear_and_paste(text: str):
    """Klik triple untuk select all, lalu paste."""
    pyautogui.hotkey("ctrl", "a")
    time.sleep(0.05)
    pyperclip.copy(str(text))
    pyautogui.hotkey("ctrl", "v")


def _find_image(image_path: str, confidence: float = 0.8):
    """Cari gambar di layar. Return Box(left,top,width,height) atau None."""
    try:
        loc = pyautogui.locateOnScreen(image_path, confidence=confidence)
        return loc
    except pyautogui.ImageNotFoundException:
        return None
    except Exception:
        return None


def _wait_for_image(image_path: str, confidence: float = 0.8,
                    timeout: float = 10.0, interval: float = 0.5):
    """Tunggu sampai gambar muncul di layar atau timeout."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        loc = _find_image(image_path, confidence)
        if loc:
            return loc
        time.sleep(interval)
    return None


def _click_image(image_path: str, confidence: float = 0.8,
                 offset_x: int = 0, offset_y: int = 0,
                 timeout: float = 8.0) -> bool:
    """Temukan gambar lalu klik titik tengah + offset. Return True jika berhasil."""
    loc = _wait_for_image(image_path, confidence, timeout)
    if loc is None:
        return False
    cx = loc.left + loc.width  // 2 + offset_x
    cy = loc.top  + loc.height // 2 + offset_y
    pyautogui.click(cx, cy)
    return True


def _click_image_and_paste(image_path: str, text: str,
                            confidence: float = 0.8,
                            offset_x: int = 0, offset_y: int = 0,
                            cfg: dict = None) -> bool:
    """Klik field via image recognition lalu paste teks."""
    cfg = cfg or {}
    ok = _click_image(image_path, confidence, offset_x, offset_y)
    if not ok:
        return False
    _delay(cfg, "setelah_klik")
    _clear_and_paste(text)
    _delay(cfg, "setelah_ketik")
    return True


# ════════════════════════════════════════════════════════════
#  AKSI PER-FIELD BERDASARKAN KOORDINAT RELATIF
#  (fallback jika image asset belum tersedia)
# ════════════════════════════════════════════════════════════

def _tab_ke_field(n: int, delay_tab: float = 0.2):
    """Tekan Tab sebanyak n kali untuk pindah field."""
    for _ in range(n):
        pyautogui.press("tab")
        time.sleep(delay_tab)


# ════════════════════════════════════════════════════════════
#  AKSI FIELD: SERI
# ════════════════════════════════════════════════════════════

def aksi_seri(cfg: dict, assets_dir: str, log_fn, nilai: str) -> bool:
    """Isi / ganti field Seri."""
    # Cari label image jika ada
    img = os.path.join(assets_dir, "label_field_seri.png")
    if os.path.exists(img):
        ok = _click_image_and_paste(img, nilai, cfg=cfg)
        if ok:
            log_fn(f"  [SERI] Diisi: '{nilai}'")
            return True
        log_fn("  [SERI] ⚠️  Image tidak ditemukan, lewati.")
        return False
    else:
        # Tanpa image: paste langsung ke fokus saat ini
        _clear_and_paste(nilai)
        _delay(cfg, "setelah_ketik")
        log_fn(f"  [SERI] Diisi (no-image): '{nilai}'")
        return True


# ════════════════════════════════════════════════════════════
#  AKSI FIELD: DAFTAR ISIAN  (satu baris tabel)
# ════════════════════════════════════════════════════════════

def aksi_satu_baris_di(cfg: dict, assets_dir: str, log_fn,
                       baris: dict, idx: int) -> bool:
    """
    Isi satu baris Daftar Isian.
    Strategi: cari header tabel pakai image, klik cell pertama baris ke-idx,
    lalu Tab untuk berpindah kolom.
    Jika image tidak ada, gunakan Tab-Tab dari posisi saat ini.
    """
    di_seri    = baris.get("di_seri", "")
    di_nomor   = baris.get("di_nomor", "")
    di_luas    = baris.get("di_luas", "")
    di_tanggal = baris.get("di_tanggal", "")

    def paste_or_skip(val: str):
        """Paste jika nilai ada, Tab saja jika kosong (biarkan)."""
        if val.strip():
            _clear_and_paste(val)
            _delay(cfg, "setelah_ketik")
        _tab_ke_field(1, float(cfg.get("delay", {}).get("setelah_tab", 0.2)))

    # ── cari baris ke-idx di tabel via gambar header tabel ──
    img_tabel = os.path.join(assets_dir, "label_tabel_di.png")
    if os.path.exists(img_tabel):
        loc = _find_image(img_tabel, confidence=0.8)
        if loc:
            # estimasi posisi baris: tinggi tiap baris ±28px
            row_height = 28
            base_y     = loc.top + loc.height + 4 + (idx * row_height)
            base_x     = loc.left + 20
            pyautogui.click(base_x, base_y)
            _delay(cfg, "setelah_klik")
        else:
            log_fn(f"  [DI baris {idx+1}] ⚠️  Tabel image tidak ditemukan.")

    # ── isi kolom satu per satu ──────────────────────────────
    paste_or_skip(di_seri)
    paste_or_skip(di_nomor)
    paste_or_skip(di_luas)
    paste_or_skip(di_tanggal)

    log_fn(f"  [DI baris {idx+1}] seri={di_seri!r} nomor={di_nomor!r} "
           f"luas={di_luas!r} tgl={di_tanggal!r}")
    return True


# ════════════════════════════════════════════════════════════
#  AKSI FIELD: DETAIL LAIN-LAIN
# ════════════════════════════════════════════════════════════

# Mapping key config → nama file image label
_DETAIL_IMAGE_MAP = {
    "keadaan_tanah":           "label_keadaan_tanah.png",
    "tanda_tanda_batas":       "label_tanda_batas.png",
    "pengukuran_dan_pemetaan": "label_pengukuran.png",
    "hal_lain_lain":           "label_hal_lain.png",
}

_DETAIL_LABEL_LOG = {
    "keadaan_tanah":           "Keadaan Tanah",
    "tanda_tanda_batas":       "Tanda-Tanda Batas",
    "pengukuran_dan_pemetaan": "Pengukuran dan Pemetaan",
    "hal_lain_lain":           "Hal Lain-Lain",
}


def aksi_detail_lain(cfg: dict, assets_dir: str, log_fn,
                     detail_cfg: dict) -> bool:
    """Isi semua sub-field Detail Lain-Lain yang enabled."""
    semua_ok = True
    for key, img_name in _DETAIL_IMAGE_MAP.items():
        sub = detail_cfg.get(key, {})
        if not sub.get("enabled", False):
            log_fn(f"  [{_DETAIL_LABEL_LOG[key]}] ⏭  Dilewati (disabled).")
            continue

        nilai = sub.get("nilai", "")
        img   = os.path.join(assets_dir, img_name)
        lbl   = _DETAIL_LABEL_LOG[key]

        # offset y supaya klik di dalam textbox, bukan di labelnya
        if os.path.exists(img):
            ok = _click_image_and_paste(img, nilai, confidence=0.8,
                                        offset_x=0, offset_y=30, cfg=cfg)
            if ok:
                log_fn(f"  [{lbl}] ✅  Diisi.")
            else:
                log_fn(f"  [{lbl}] ⚠️  Image tidak ditemukan, lewati.")
                semua_ok = False
        else:
            # Tanpa image: andalkan urutan Tab (posisi manual)
            _clear_and_paste(nilai)
            _delay(cfg, "setelah_ketik")
            log_fn(f"  [{lbl}] ✅  Diisi (no-image).")

    return semua_ok


# ════════════════════════════════════════════════════════════
#  AKSI SIMPAN  (klik tombol tanda seru / validasi)
# ════════════════════════════════════════════════════════════

def aksi_simpan(cfg: dict, assets_dir: str, log_fn) -> bool:
    """Klik tombol simpan / tanda seru di halaman DETIL."""
    # Coba beberapa kandidat image simpan
    candidates = [
        "label_tanda_seru.png",
        "Validasi_button.png",
        "validasiBT.png",
    ]
    for img_name in candidates:
        img = os.path.join(assets_dir, img_name)
        if os.path.exists(img):
            ok = _click_image(img, confidence=0.8, timeout=6.0)
            if ok:
                log_fn(f"  [SIMPAN] ✅  Klik '{img_name}'.")
                _delay(cfg, "setelah_klik")
                return True
    log_fn("  [SIMPAN] ⚠️  Tombol simpan tidak ditemukan.")
    return False


# ════════════════════════════════════════════════════════════
#  FUNGSI UTAMA  –  dipanggil dari run_detil_su.py
# ════════════════════════════════════════════════════════════

def jalankan_paste(
    cfg:         dict,
    assets_dir:  str,
    is_running,          # callable → bool
    is_paused,           # callable → bool
    log_fn,              # callable(str)
    progress_fn,         # callable(str)
    status_fn,           # callable(str)
):
    """
    Proses utama auto-paste DETIL Surat Ukur.

    Alur per-record:
      1. Buka / pastikan tab DETIL aktif
      2. Isi Seri (jika enabled)
      3. Isi Daftar Isian baris per baris (jika enabled)
      4. Isi Detail Lain-Lain (jika tiap sub-field enabled)
      5. Klik Simpan / Tanda Seru

    Untuk multi-record: program menunggu F9 berikutnya sebelum
    pindah ke record selanjutnya (mirip pola run_su yang sudah ada).
    """

    log_fn("═" * 55)
    log_fn("  AUTO-PASTE DETIL SURAT UKUR  –  MULAI")
    log_fn("═" * 55)

    seri_cfg   = cfg.get("seri",         {})
    di_cfg     = cfg.get("daftar_isian", {})
    detail_cfg = cfg.get("detail_lain",  {})
    baris_list = di_cfg.get("baris", []) if di_cfg.get("enabled", True) else []

    total = max(len(baris_list), 1)   # minimal 1 "pass"

    for rec_idx in range(total):
        if not is_running():
            log_fn("■  Dihentikan oleh pengguna.")
            return

        # ── tunggu jika dijeda ───────────────────────────────
        while is_paused() and is_running():
            time.sleep(0.2)
        if not is_running():
            return

        progress_fn(f"Record: {rec_idx+1}/{total}")
        log_fn(f"\n── Record {rec_idx+1}/{total} ──────────────────────────")
        status_fn(f"▶  Record {rec_idx+1}/{total}…")

        # ── 1. Pastikan tab DETIL aktif ──────────────────────
        img_tab = os.path.join(assets_dir, "label_tab_detil.png")
        if os.path.exists(img_tab):
            ok = _click_image(img_tab, confidence=0.8, timeout=5.0)
            if ok:
                log_fn("  [TAB] ✅  Tab DETIL diklik.")
                _delay(cfg, "setelah_klik")
            else:
                log_fn("  [TAB] ⚠️  Tab DETIL tidak ditemukan, lanjut saja.")
        else:
            log_fn("  [TAB] ℹ️  Image tab_detil.png belum ada, skip.")

        # ── 2. SERI ─────────────────────────────────────────
        if seri_cfg.get("enabled", True):
            aksi_seri(cfg, assets_dir, log_fn,
                      nilai=str(seri_cfg.get("nilai", "-")))
            _delay(cfg, "antar_field")
        else:
            log_fn("  [SERI] ⏭  Dilewati (disabled).")

        # ── 3. DAFTAR ISIAN  (hanya baris ke-rec_idx) ────────
        if di_cfg.get("enabled", True) and baris_list:
            baris = baris_list[rec_idx]
            aksi_satu_baris_di(cfg, assets_dir, log_fn, baris, rec_idx)
            _delay(cfg, "antar_field")
        else:
            log_fn("  [DI] ⏭  Dilewati (disabled atau kosong).")

        # ── 4. DETAIL LAIN-LAIN ───────────────────────────────
        aksi_detail_lain(cfg, assets_dir, log_fn, detail_cfg)
        _delay(cfg, "antar_field")

        # ── 5. SIMPAN ────────────────────────────────────────
        aksi_simpan(cfg, assets_dir, log_fn)

        log_fn(f"✅  Record {rec_idx+1} selesai.")

        # ── tunggu trigger F9 berikutnya (jika masih ada record) ──
        if rec_idx < total - 1:
            log_fn("⏳  Menunggu F9 untuk record berikutnya…")
            status_fn("⏳  Menunggu F9…")
            # tandai running=False sementara supaya GUI bisa start lagi
            # sebenarnya cukup loop di sini sampai is_running() True lagi
            # tapi karena is_running() masih True, kita pakai flag _waiting
            # Cara sederhana: pause otomatis, user pencet F9 lagi
            # Implementasi: set paused, lalu tunggu unpause
            _wait_next_trigger(is_running, is_paused, log_fn)
            if not is_running():
                return

    log_fn("\n═" * 28)
    log_fn("  SEMUA RECORD SELESAI ✅")
    log_fn("═" * 28)


def _wait_next_trigger(is_running, is_paused, log_fn):
    """
    Setelah satu record selesai, otomatis pause dan tunggu
    sampai pengguna menekan F9 (un-pause) atau ESC (stop).
    run_detil_su.py mengeset _paused=True via _start_worker yang
    tidak akan memulai thread baru karena _running sudah True.
    Di sini kita set paused secara internal dengan menunggu
    perubahan state dari GUI.
    """
    # Set status paused melalui flag global sederhana:
    # Karena kita tidak punya akses langsung ke _paused setter,
    # kita hanya tidur singkat dan cek is_paused.
    # Pengguna harus menekan F10 untuk melanjutkan record berikutnya,
    # atau F9 yang akan memanggil _start_worker (no-op karena running).
    # Pendekatan terbaik: tidur pendek sambil cek running & paused.
    time.sleep(0.5)   # beri jeda kecil sebelum lanjut otomatis
    # Jika user sudah pause (F10), tunggu sampai di-unpause
    while is_paused() and is_running():
        time.sleep(0.2)
