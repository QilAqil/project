# Panduan Auto-Paste DETIL Surat Ukur

Aplikasi ini mengotomatiskan pengisian form **Tab DETIL** pada halaman
Manajemen Dokumen – Surat Ukur di sistem ATR/BPN.  
Field yang bisa diisi / diganti otomatis:

| Bagian | Field |
|---|---|
| **Seri** | Dropdown/input seri di kiri atas |
| **Daftar Isian** | Tiap baris: Seri DI, Nomor, Luas, Tanggal |
| **Detail Lain-Lain** | Keadaan Tanah, Tanda-Tanda Batas, Pengukuran dan Pemetaan, Hal Lain-Lain |

---

## Struktur Folder

```
run_detil_su/
├── run_detil_su.py        ← jalankan ini (atau .exe setelah build)
├── auto_paste_detil.py    ← logika pyautogui (otomatis di-import)
├── config_detil.yaml      ← konfigurasi isian (edit sesuai data)
├── requirements.txt       ← dependensi Python
├── build.spec             ← spec PyInstaller untuk membuat .exe
├── PANDUAN.md             ← file ini
└── assets/                ← taruh screenshot label di sini (lihat bawah)
```

---

## Instalasi (mode script Python)

```powershell
pip install -r requirements.txt
python run_detil_su.py
```

---

## Build ke .exe

```powershell
pip install pyinstaller
pyinstaller build.spec
```

Hasil ada di `dist\run_detil_su\run_detil_su.exe`.  
Salin seluruh folder `dist\run_detil_su\` ke komputer tujuan.

---

## Cara Pakai

### 1. Edit `config_detil.yaml`

Buka GUI → tab **Konfigurasi**, atau edit file YAML langsung.

**Seri**
```yaml
seri:
  enabled: true    # true = isi/ganti, false = biarkan
  nilai: "-"
```

**Daftar Isian** — tambah/kurangi baris sesuai kebutuhan:
```yaml
daftar_isian:
  enabled: true
  baris:
    - di_seri:    "034"
      di_nomor:   ""          # kosong = biarkan isi yang sudah ada
      di_luas:    "1000"
      di_tanggal: "10/01/900"
```
> Kolom yang dikosongkan (`""`) akan di-skip (hanya Tab pindah field,
> tidak mengganti isi yang ada).

**Detail Lain-Lain** — tiap sub-field bisa diaktifkan sendiri:
```yaml
detail_lain:
  keadaan_tanah:
    enabled: true
    nilai: "Sebidang tanah bekas pertanian"

  tanda_tanda_batas:
    enabled: true
    nilai: "Telah terpasang sesuai dengan PP No. 24 Tahun 1997..."

  pengukuran_dan_pemetaan:
    enabled: false      # ← false = biarkan, tidak disentuh
    nilai: "MUHKSONI"

  hal_lain_lain:
    enabled: true
    nilai: "TIDAK ADA NOMOR GAMBAR UKUR 1871/2021"
```

### 2. Siapkan Image Assets (opsional tapi disarankan)

Letakkan screenshot **potongan kecil label/tombol** di folder `assets/`.  
Nama file yang dikenali:

| Nama File | Digunakan Untuk |
|---|---|
| `label_tab_detil.png` | Klik tab "DETIL" |
| `label_field_seri.png` | Klik field Seri |
| `label_tabel_di.png` | Anchor baris tabel Daftar Isian |
| `label_keadaan_tanah.png` | Klik area Keadaan Tanah |
| `label_tanda_batas.png` | Klik area Tanda-Tanda Batas |
| `label_pengukuran.png` | Klik area Pengukuran dan Pemetaan |
| `label_hal_lain.png` | Klik area Hal Lain-Lain |
| `label_tanda_seru.png` | Klik tombol Simpan / Tanda Seru |

> Jika file image **tidak ada**, aplikasi tetap berjalan dalam mode
> *no-image* (paste ke fokus aktif saat itu / urutan Tab).

**Tips ambil screenshot label:**
1. Buka form DETIL di browser
2. Screenshot bagian kecil teks label saja (±150×25 px)
3. Simpan sebagai `.png` dengan nama sesuai tabel di atas ke folder `assets/`

### 3. Jalankan Aplikasi

```powershell
python run_detil_su.py
# atau klik run_detil_su.exe
```

### 4. Mulai Proses

1. Buka browser → halaman DETIL Surat Ukur record pertama
2. Pastikan tab **DETIL** aktif di browser
3. Tekan **F9** atau klik tombol **▶ MULAI** di aplikasi
4. Aplikasi akan:
   - Klik tab DETIL (jika image tersedia)
   - Isi field Seri
   - Isi baris Daftar Isian sesuai urutan
   - Isi Detail Lain-Lain
   - Klik Simpan / Tanda Seru
5. Untuk record berikutnya: buka record di browser → tekan **F9** lagi

---

## Hotkey

| Tombol | Fungsi |
|---|---|
| **F9** | Mulai / lanjut satu record |
| **F10** | Jeda / lanjutkan |
| **F11** | Reset ke record pertama |
| **ESC** | Hentikan proses |

---

## Delay (dapat diubah di tab Kontrol)

| Setting | Default | Keterangan |
|---|---|---|
| `antar_field` | 0.4 dtk | Jeda setelah pindah field |
| `setelah_klik` | 0.5 dtk | Jeda setelah klik mouse |
| `setelah_ketik` | 0.3 dtk | Jeda setelah paste teks |
| `setelah_tab` | 0.2 dtk | Jeda setelah tekan Tab |

Naikkan nilai jika koneksi internet ke server lambat.

---

## Log

Semua kejadian dicatat di `laporan_detil.txt` di folder yang sama.  
Bisa dilihat real-time di tab **Log** dalam aplikasi.

---

## Troubleshooting

| Masalah | Solusi |
|---|---|
| Field tidak terisi | Pastikan browser ada di foreground saat F9 ditekan |
| Image tidak ditemukan | Ambil ulang screenshot label dengan resolusi layar yang sama |
| Teks terpotong | Naikkan delay `setelah_ketik` |
| Tabel DI meleset | Sesuaikan `row_height` di `auto_paste_detil.py` baris ~90 |
| Aplikasi crash saat build | Jalankan dulu mode script untuk debug error |
