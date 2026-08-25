# 🚀 Auto Unfollow Instagram (Non-Follback Cleaner) - Microsoft Edge on Fedora

Script otomatisasi Python cerdas untuk mendeteksi dan meng-unfollow akun Instagram yang **tidak mengikuti balik (follback)** menggunakan sesi profil **Microsoft Edge** yang sudah login di **Fedora Linux**.

---

## 🌟 Keunggulan & Fitur Utama

- **Smart Profile Sync (Tanpa Perlu Tutup Browser)**:
  Script secara otomatis menyalin dan menyinkronkan data sesi login (`Cookies`, `Local Storage`, `Tokens`) dari direktori Microsoft Edge Fedora (`~/.config/microsoft-edge`) ke profil otomasi yang terisolasi (`~/.config/auto-unfollow-ig-edge`). Browser Edge utama Anda **bisa tetap terbuka** tanpa memicu error `SingletonLock` atau kebijakan keamanan DevTools!
- **Langsung Pakai Tanpa Login Ulang**: Tidak perlu memasukkan password, email, atau kode OTP / 2FA.
- **Deteksi Otomatis Username**: Otomatis mendeteksi akun Instagram yang sedang login di Edge.
- **Deteksi Non-Follback Akurat**: Memindai seluruh *Followers* & *Following*, lalu membandingkan `Non-Followers = Following - Followers`.
- **Dukungan Whitelist**: Akun penting (teman, keluarga, idola, brand) yang Anda daftarkan di `whitelist.txt` tidak akan pernah di-unfollow.
- **Mode Simulasi (Dry-Run)**: Anda dapat menguji proses pemindaian dan melihat daftar target tanpa melakukan unfollow sungguhan.
- **Fitur Keamanan (Anti-Ban & Anti Action-Block)**:
  - Random human-like delay (6 - 15 detik) antar aksi unfollow.
  - Batas maksimal per sesi (default: 25 akun) agar reputasi akun Instagram Anda tetap aman.
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

## 📦 Cara Menjalankan

1. **Buka Terminal di Folder Proyek**:
   ```bash
   cd /home/fahrudin/Projects/auto-unfollow-ig
   ```

2. **Jalankan Program Utama**:
   ```bash
   ./venv/bin/python3 main.py
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
- **Menu 2**: Mensimulasikan proses unfollow langkah-demi-langkah (aman untuk uji coba).
- **Menu 3**: Melakukan aksi unfollow sesungguhnya (akan meminta konfirmasi `YA` terlebih dahulu).
- **Menu 4**: Melihat daftar akun yang terlindungi oleh `whitelist.txt`.

---

## ⚙️ Pengaturan di `config.py`

| Parameter | Deskripsi | Default |
| :--- | :--- | :--- |
| `EDGE_USER_DATA_DIR` | Path direktori Edge utama di Fedora | `~/.config/microsoft-edge` |
| `EDGE_PROFILE_DIR` | Nama profil yang digunakan | `"Default"` |
| `AUTOMATION_PROFILE_DIR` | Direktori profil khusus otomasi | `~/.config/auto-unfollow-ig-edge` |
| `AUTO_SYNC_SESSION` | Otomatis sinkronkan sesi login Edge | `True` |
| `HEADLESS_MODE` | Sembunyikan jendela browser | `False` |
| `MAX_UNFOLLOW_LIMIT` | Maksimal akun unfollow per sesi | `25` |
| `MIN_DELAY_SECONDS` | Jeda minimum antar unfollow | `6` detik |
| `MAX_DELAY_SECONDS` | Jeda maksimum antar unfollow | `15` detik |

---

## 🛡️ Tips Keamanan Menghindari Pemblokiran Instagram

1. **Batasi Jumlah Unfollow**: Disarankan maksimal **25 - 50 akun per hari**.
2. **Beri Jeda Antar Sesi**: Setelah 1 sesi unfollow (misal 25 akun), istirahatkan akun selama 2 - 4 jam sebelum sesi berikutnya.
3. **Pertahankan Delay Bawaan**: Jeda 6 - 15 detik meniru perilaku manusia dan sangat efektif menghindari deteksi bot.
4. **Isi Whitelist**: Tambahkan akun teman akrab, figur publik, atau akun berita favorit ke file `whitelist.txt`.
