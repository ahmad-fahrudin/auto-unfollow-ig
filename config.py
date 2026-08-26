import os

# ==============================================================================
# KONFIGURASI MICROSOFT EDGE DI FEDORA LINUX
# ==============================================================================

# Lokasi Direktori Profil Khusus Otomatisasi
# Profil ini menyimpan sesi login Instagram Anda secara permanen dan aman
# tanpa mengganggu atau terganggu oleh browser Microsoft Edge utama Anda.
AUTOMATION_PROFILE_DIR = os.path.expanduser("~/.config/auto-unfollow-ig-edge")

# Nama Profil yang digunakan
EDGE_PROFILE_DIR = "Default"

# Lokasi binary Microsoft Edge di Fedora (diarahkan ke ELF binary langsung)
if os.path.exists("/opt/microsoft/msedge/msedge"):
    EDGE_BINARY_PATH = "/opt/microsoft/msedge/msedge"
elif os.path.exists("/opt/microsoft/msedge-dev/msedge"):
    EDGE_BINARY_PATH = "/opt/microsoft/msedge-dev/msedge"
elif os.path.exists("/opt/microsoft/msedge-beta/msedge"):
    EDGE_BINARY_PATH = "/opt/microsoft/msedge-beta/msedge"
else:
    EDGE_BINARY_PATH = "/usr/bin/microsoft-edge"

# Tampilkan jendela browser saat otomasi berjalan (False = tampak di layar, True = di latar belakang)
HEADLESS_MODE = False

# Mode Remote Debugging Manual (Opsional):
USE_REMOTE_DEBUGGING = False
REMOTE_DEBUGGING_PORT = 9222


# ==============================================================================
# KONFIGURASI INSTAGRAM & AUTO UNFOLLOW
# ==============================================================================

# Username Instagram Anda (kosongkan "" jika ingin dideteksi otomatis saat login)
INSTAGRAM_USERNAME = ""

# Batas maksimal akun yang di-unfollow dalam satu kali sesi eksekusi.
# Disarankan: 15 - 30 akun per sesi untuk menjaga akun tetap aman dari action block.
MAX_UNFOLLOW_LIMIT = 300

# Waktu tunggu acak (detik) antar tindakan unfollow (Safety Human-like Delay)
# Mencegah deteksi bot otomatis oleh Instagram
MIN_DELAY_SECONDS = 6
MAX_DELAY_SECONDS = 15

# Delay waktu scroll modal daftar follower/following (detik)
SCROLL_DELAY_SECONDS = 1.8

# Waktu tunggu timeout elemen web (detik)
PAGE_TIMEOUT_SECONDS = 25

# Mode Simulasi Default (Dry Run)
# True  = Hanya simulasi tanpa klik unfollow nyata.
# False = Eksekusi nyata.
DEFAULT_DRY_RUN = False


# ==============================================================================
# DAFTAR WHITELIST (AKUN YANG TIDAK AKAN PERNAH DI-UNFOLLOW)
# ==============================================================================

# File eksternal untuk menyimpan daftar whitelist (satu username per baris)
WHITELIST_FILE = "whitelist.txt"

# Whitelist tambahan langsung di config (huruf kecil semua, tanpa tanda @)
# Contoh: ["instagram", "natgeo", "teman_baik"]
CONFIG_WHITELIST = [
    # "instagram",
    # "cristiano",
]


def load_whitelist() -> set:
    """Membaca daftar whitelist dari file dan config."""
    whitelist = {u.strip().lower().lstrip("@") for u in CONFIG_WHITELIST if u.strip()}
    
    if os.path.exists(WHITELIST_FILE):
        try:
            with open(WHITELIST_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    clean_line = line.strip().lower()
                    if clean_line and not clean_line.startswith("#"):
                        whitelist.add(clean_line.lstrip("@"))
        except Exception as e:
            print(f"[Warning] Gagal membaca {WHITELIST_FILE}: {e}")
            
    return whitelist
