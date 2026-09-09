# Panduan Auto-Paste DETIL Surat Ukur

Aplikasi ini mengotomatiskan pengisian form **Tab DETIL** pada halaman
Manajemen Dokumen – Surat Ukur di sistem ATR/BPN.

Field yang bisa diisi / diganti otomatis:

| Bagian | Field |
|---|---|
| **Seri** | Dropdown/input seri di kiri atas |
| **Daftar Isian** | 3 kolom (DI 382, DI 383, DI 307) × 3 field (Nomor, Tahun, Tanggal) |
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

## Instalasi

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

### 1. Edit Konfigurasi

Buka GUI → tab **Konfigurasi**, atau edit `config_detil.yaml` langsung.

#### Seri
```yaml
seri:
  enabled: true    # true = isi/ganti, false = biarkan
  nilai: "-"
```

#### Daftar Isian

Tiap baris di layar tampilannya seperti ini:

```
[ DI 382 ] [ Nomor...     ] [ Tahun... ] [ Tanggal...  ] [📅]
[ DI 383 ] [ Nomor...     ] [ Tahun... ] [ Tanggal...  ] [📅]
[ DI 307 ] [ Nomor...     ] [ Tahun... ] [ Tanggal...  ] [📅]
```

Konfigurasi per kolom di YAML:
```yaml
daftar_isian:
  enabled: true
  kolom:
    - id:      "DI 382"
      enabled: true
      image:   "label_di_382.png"   # screenshot header kolom
      nomor:   "034"
      tahun:   "2020"
      tanggal: "25/03/2023"

    - id:      "DI 383"
      enabled: true
      image:   "label_di_383.png"
      nomor:   "0"
      tahun:   "1000"
      tanggal: "01/01/900"

    - id:      "DI 307"
      enabled: true
      image:   "label_di_307.png"
      nomor:   "120510"
      tahun:   "2021"
      tanggal: "03/10/2021"
```

> Nilai yang dikosongkan (`nomor: ""`) = **biarkan isi yang sudah ada**,
> program hanya Tab ke field berikutnya tanpa mengganti.

Di GUI, tiap kolom DI tampil sebagai kartu dengan field:
**Aktif** · **ID Kolom** · **Image** · **Nomor** · **Tahun** · **Tanggal**

Bisa tambah / hapus kolom sesuai kebutuhan dengan tombol **+ Tambah Kolom DI**.

#### Detail Lain-Lain

Tiap sub-field punya toggle sendiri:
```yaml
detail_lain:
  keadaan_tanah:
    enabled: true
    nilai: "Sebidang tanah bekas pertanian"

  tanda_tanda_batas:
    enabled: true
    nilai: "Telah terpasang sesuai dengan PP No. 24 Tahun 1997..."

  pengukuran_dan_pemetaan:
    enabled: false      # false = biarkan, tidak disentuh
    nilai: "MUHKSONI"

  hal_lain_lain:
    enabled: true
    nilai: "TIDAK ADA NOMOR GAMBAR UKUR 1871/2021"
```

---

### 2. Siapkan Image Assets

Letakkan screenshot **potongan kecil label** di folder `assets/`.
Total file yang dibutuhkan: **10 file**.

#### Navigasi & Seri (2 file)
| Nama File | Ambil Screenshot Dari |
|---|---|
| `label_tab_detil.png` | Teks tab "DETIL" di bagian atas halaman |
| `label_field_seri.png` | Label teks "Seri" di form bagian atas |

#### Daftar Isian — Label Baris (3 file)

Tiap baris Daftar Isian tampilannya seperti ini di layar:

```
[ DI 303 ] [ Nomor...          ] [ Tahun...    ] [ Tanggal...   ] [📅]
```

`DI 303` adalah **label di sisi kiri** baris — itulah yang di-screenshot.
Aplikasi mendeteksi label tersebut, lalu otomatis klik input **Nomor** di sebelah kanannya,
kemudian Tab ke **Tahun** → Tab ke **Tanggal**.

| Nama File | Ambil Screenshot Dari |
|---|---|
| `label_di_382.png` | Teks **"DI 382"** di sisi kiri baris |
| `label_di_383.png` | Teks **"DI 383"** di sisi kiri baris |
| `label_di_307.png` | Teks **"DI 307"** di sisi kiri baris |

> Cukup **3 file** untuk Daftar Isian — satu per baris DI, bukan 9.

#### Detail Lain-Lain (4 file)
| Nama File | Ambil Screenshot Dari |
|---|---|
| `label_keadaan_tanah.png` | Label "Keadaan Tanah" |
| `label_tanda_batas.png` | Label "Tanda-Tanda Batas" |
| `label_pengukuran.png` | Label "Pengukuran dan Pemetaan" |
| `label_hal_lain.png` | Label "Hal Lain-Lain" |

#### Tombol Simpan (1 file)
| Nama File | Ambil Screenshot Dari |
|---|---|
| `label_tanda_seru.png` | Tombol **!** / Simpan di halaman DETIL |

#### Tips ambil screenshot label
1. Buka form DETIL di browser
2. Screenshot bagian kecil teks label saja (sekitar 150×25 px)
3. Simpan sebagai `.png` dengan nama sesuai tabel di atas ke folder `assets/`
4. Gunakan resolusi layar yang sama setiap kali menjalankan aplikasi

> Jika file image **tidak ada**, aplikasi tetap berjalan dalam mode
> *no-image* — paste ke field yang sedang aktif / urutan Tab manual.

---

### 3. Jalankan Aplikasi

```powershell
py run_detil_su.py
```

atau klik `run_detil_su.exe`

### 4. Mulai Proses

1. Buka browser → buka record Surat Ukur → pastikan tab **DETIL** aktif
2. Tekan **F9** atau klik tombol **▶ MULAI** di aplikasi
3. Aplikasi akan mengerjakan urutan ini secara otomatis:
   - Klik tab DETIL (jika image tersedia)
   - Isi field **Seri**
   - Isi kolom **DI 382** → klik header → Nomor, Tahun, Tanggal
   - Isi kolom **DI 383** → klik header → Nomor, Tahun, Tanggal
   - Isi kolom **DI 307** → klik header → Nomor, Tahun, Tanggal
   - Isi **Keadaan Tanah**, **Tanda-Tanda Batas**, **Pengukuran**, **Hal Lain-Lain**
   - Klik tombol **Simpan / Tanda Seru**
4. Untuk record berikutnya: buka record di browser → tekan **F9** lagi

---

## Hotkey

| Tombol | Fungsi |
|---|---|
| **F1** | Mulai / lanjut satu record |
| **F2** | Jeda / lanjutkan |
| **F3** | Reset |
| **ESC** | Hentikan proses |

---

## Delay

Dapat diubah di tab **Kontrol** atau langsung di `config_detil.yaml`:

| Setting | Default | Keterangan |
|---|---|---|
| `antar_field` | 0.4 dtk | Jeda setelah pindah antar field/kolom |
| `setelah_klik` | 0.5 dtk | Jeda setelah klik mouse |
| `setelah_ketik` | 0.3 dtk | Jeda setelah paste teks |
| `setelah_tab` | 0.2 dtk | Jeda setelah tekan Tab |

Naikkan nilai jika koneksi ke server lambat atau field belum siap menerima input.

---

## Log

Semua kejadian dicatat di `laporan_detil.txt`.
Bisa dilihat real-time di tab **Log** dalam aplikasi.

---

## Troubleshooting

| Masalah | Solusi |
|---|---|
| Field tidak terisi | Pastikan browser ada di foreground saat F9 ditekan |
| Header kolom DI tidak ditemukan | Ambil ulang screenshot dengan resolusi layar yang sama |
| Nomor/Tahun/Tanggal meleset ke field lain | Sesuaikan `_DI_OFFSET_NOMOR/TAHUN/TANGGAL` di `auto_paste_detil.py` baris ~55 |
| Teks terpotong / tidak lengkap | Naikkan delay `setelah_ketik` |
| Build .exe gagal | Jalankan dulu mode script untuk melihat error lengkapnya |
