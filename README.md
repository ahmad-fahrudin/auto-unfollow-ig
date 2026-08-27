# 🚀 Auto Unfollow Instagram (Non-Follback Cleaner) - Microsoft Edge on Fedora

Script otomatisasi Python cerdas untuk mendeteksi dan meng-unfollow akun Instagram yang **tidak mengikuti balik (follback)** menggunakan sesi profil **Microsoft Edge** yang sudah login di **Fedora Linux**.

---

## 🌟 Keunggulan & Fitur Utama

- **Batch Unfollow Berkelanjutan (Tanpa Scan Ulang & Tanpa Tutup Browser)**:
  Setelah 1 batch (misal 25 akun) selesai di-unfollow, Anda dapat langsung melanjutkan ke batch berikutnya atau menambahkan jeda waktu istirahat secara instan tanpa perlu keluar dari program, membuka ulang browser, ataupun memindai ulang followers/following dari awal.
- **Sesi Profil Otomasi Permanen**: Sesi login tersimpan permanen di direktori otomasi terisolasi sehingga browser Edge utama Anda bebas dipakai kapan saja.
- **Deteksi Otomatis Username**: Otomatis mendeteksi akun Instagram yang sedang login.
- **Deteksi Non-Follback Akurat & Cepat**: Memindai seluruh *Followers* & *Following* via GraphQL/Web API internal secara instan.
- **Dukungan Whitelist**: Akun penting (teman, keluarga, idola, brand) yang Anda daftarkan di `whitelist.txt` tidak akan pernah di-unfollow.
- **Mode Simulasi (Dry-Run)**: Anda dapat menguji proses pemindaian dan melihat simulasi unfollow tanpa klik nyata.
- **Fitur Keamanan (Anti-Ban & Anti Action-Block)**:
  - Random safety delay antar aksi unfollow.
  - Pembagian per batch (default: 25 akun) dan deteksi otomatis Action Block (*Try Again Later*).
- **Multi-bahasa UI**: Mendukung antarmuka Instagram Bahasa Indonesia dan Bahasa Inggris.
- **Export Hasil**: Otomatis menyimpan daftar akun yang tidak follback ke file `.txt` lengkap dengan waktu pemindaian.

---

## 📁 Struktur Direktori

```
auto-unfollow-ig/
├── config.py             # File konfigurasi (pengaturan Edge Fedora, limits, delay, whitelist)
├── unfollower.py         # Modul inti scraping & unfollow Instagram
├── main.py               # Program utama dengan CLI menu interaktif berwarna
├── whitelist.txt         # Daftar akun yang dilindungi
├── requirements.txt      # Daftar pustaka Python yang dibutuhkan
└── README.md             # Petunjuk dan dokumentasi lengkap
```

---

## 🛠️ Persyaratan Sistem

- **OS**: Fedora Linux
- **Python**: Python 3.9+
- **Browser**: Microsoft Edge for Linux (`/opt/microsoft/msedge/msedge` atau `/usr/bin/microsoft-edge`)

---

## 📦 Instalasi & Cara Menjalankan

1. **Buka Terminal di Folder Proyek**:
   ```bash
   cd /home/fahrudin/Projects/auto-unfollow-ig
   ```

2. **Install Dependensi**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Jalankan Program Utama**:
   ```bash
   python3 main.py
   ```

---

## 🎮 Pilihan Menu CLI

```
======================================================================
     AUTO UNFOLLOW INSTAGRAM (NON-FOLLBACK DETECTOR & CLEANER)
     Microsoft Edge Edition (Fedora Linux)
======================================================================

PILIH MENU:
 [1] 🔍 Scan & Tampilkan Akun Non-Follback (Hanya Analisis)
 [2] 🧪 Jalankan Auto Unfollow (DRY-RUN / Simulasi)
 [3] 🚀 Jalankan Auto Unfollow (REAL MODE / Nyata)
 [4] 📋 Lihat & Kelola Daftar Whitelist (Akun Dilindungi)
 [5] ⚙️  Cek Konfigurasi & Panduan Edge Fedora
 [0] 🚪 Keluar
```

- **Menu 1**: Memindai followers & following Anda, mencocokkan non-follback, menampilkan hasilnya di layar dan mengekspornya ke file `.txt`.
- **Menu 2**: Mensimulasikan proses unfollow secara bertahap (batch) tanpa klik nyata.
- **Menu 3**: Melakukan aksi unfollow sesungguhnya per batch dengan opsi lanjut langsung ke batch berikutnya atau jeda waktu istirahat.
- **Menu 4**: Melihat daftar akun yang terlindungi oleh `whitelist.txt`.
- **Menu 5**: Melihat informasi konfigurasi dan direktori profil otomasi.

---

## ⚙️ Pengaturan di `config.py`

| Parameter | Deskripsi | Default |
| :--- | :--- | :--- |
| `AUTOMATION_PROFILE_DIR` | Direktori profil khusus otomasi | `~/.config/auto-unfollow-ig-edge` |
| `EDGE_PROFILE_DIR` | Nama profil yang digunakan | `"Default"` |
| `HEADLESS_MODE` | Sembunyikan jendela browser | `False` |
| `MAX_UNFOLLOW_LIMIT` | Maksimal akun unfollow per batch | `25` |
| `MIN_DELAY_SECONDS` | Jeda minimum antar unfollow | `1` detik |
| `MAX_DELAY_SECONDS` | Jeda maksimum antar unfollow | `2` detik |
| `WHITELIST_FILE` | File daftar akun yang dilindungi | `"whitelist.txt"` |

---

## 🛡️ Tips Keamanan Menghindari Pemblokiran Instagram

1. **Gunakan Sistem Batch**: Lakukan unfollow bertahap per batch (misal 25 akun per batch).
2. **Beri Jeda Antar Batch**: Manfaatkan opsi jeda waktu (misal `J 30` untuk istirahat 30-60 detik) sebelum melanjutkan ke batch berikutnya.
3. **Isi Whitelist**: Tambahkan akun teman akrab, figur publik, atau akun bisnis ke file `whitelist.txt`.
