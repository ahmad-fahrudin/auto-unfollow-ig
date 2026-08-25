import os
import sys
import time
from datetime import datetime

try:
    from colorama import init, Fore, Style
    init(autoreset=True)
    GREEN = Fore.GREEN
    CYAN = Fore.CYAN
    YELLOW = Fore.YELLOW
    RED = Fore.RED
    MAGENTA = Fore.MAGENTA
    BOLD = Style.BRIGHT
    RESET = Style.RESET_ALL
except ImportError:
    GREEN = ""
    CYAN = ""
    YELLOW = ""
    RED = ""
    MAGENTA = ""
    BOLD = ""
    RESET = ""

import config
from unfollower import InstagramUnfollower


def print_banner():
    banner = f"""
{CYAN}{BOLD}======================================================================
     AUTO UNFOLLOW INSTAGRAM (NON-FOLLBACK DETECTOR & CLEANER)
     Microsoft Edge Edition (Fedora Linux)
======================================================================{RESET}
"""
    print(banner)


def show_menu():
    print(f"{BOLD}PILIH MENU:{RESET}")
    print(f" {GREEN}[1]{RESET} 🔍 Scan & Tampilkan Akun Non-Follback (Hanya Analisis)")
    print(f" {YELLOW}[2]{RESET} 🧪 Jalankan Auto Unfollow ({BOLD}DRY-RUN / Simulasi{RESET})")
    print(f" {RED}[3]{RESET} 🚀 Jalankan Auto Unfollow ({BOLD}REAL MODE / Nyata{RESET})")
    print(f" {CYAN}[4]{RESET} 📋 Lihat & Kelola Daftar Whitelist (Akun Dilindungi)")
    print(f" {MAGENTA}[5]{RESET} ⚙️  Cek Konfigurasi & Panduan Edge Fedora")
    print(f" [0] 🚪 Keluar")
    print()


def view_whitelist():
    print(f"\n{CYAN}{BOLD}=== DAFTAR WHITELIST (AKUN DILINDUNGI) ==={RESET}")
    whitelist = config.load_whitelist()
    if not whitelist:
        print(f"{YELLOW}Whitelist masih kosong. Anda dapat menambahkan username ke file 'whitelist.txt'.{RESET}")
    else:
        print(f"Total akun dalam Whitelist: {len(whitelist)}")
        for idx, user in enumerate(sorted(whitelist), 1):
            print(f"  {idx}. @{user}")
    print(f"\n{GREEN}[i] Edit file '{config.WHITELIST_FILE}' untuk menambah/mengurangi akun.{RESET}\n")


def check_config_info():
    print(f"\n{MAGENTA}{BOLD}=== INFORMASI KONFIGURASI SISTEM ==={RESET}")
    print(f"• Edge User Data Asli  : {config.EDGE_USER_DATA_DIR}")
    print(f"• Edge Profile Asli    : {config.EDGE_PROFILE_DIR}")
    print(f"• Profil Otomasi       : {config.AUTOMATION_PROFILE_DIR}")
    print(f"• Auto-Sync Sesi Login : {'Aktif' if config.AUTO_SYNC_SESSION else 'Nonaktif'}")
    print(f"• Binary Edge (ELF)    : {config.EDGE_BINARY_PATH}")
    print(f"• Mode Tampilan        : {'Headless' if config.HEADLESS_MODE else 'GUI (Jendela Terbuka)'}")
    print(f"• Max Unfollow / Sesi  : {config.MAX_UNFOLLOW_LIMIT} akun")
    print(f"• Random Safety Delay  : {config.MIN_DELAY_SECONDS}s - {config.MAX_DELAY_SECONDS}s")
    print(f"• File Whitelist       : {config.WHITELIST_FILE}")
    print()
    print(f"{BOLD}Keunggulan Fitur Auto-Sync:{RESET}")
    print(f"1. Script otomatis membaca & menyalin sesi login Instagram dari profil Microsoft Edge Anda.")
    print(f"2. Anda {GREEN}TIDAK PERLU MENUTUP BROWSER EDGE{RESET} saat script ini dijalankan!")
    print(f"3. Profil utama tetap aman dan tidak akan terjadi konflik database (SingletonLock).")
    print()


def save_results_to_file(non_followers: list, my_username: str):
    """Menyimpan hasil scan ke file txt untuk referensi user."""
    filename = f"non_followers_{my_username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"# Daftar Akun Non-Follback untuk @{my_username}\n")
            f.write(f"# Waktu Scan: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# Total: {len(non_followers)} akun\n\n")
            for u in non_followers:
                f.write(f"{u}\n")
        print(f"\n{GREEN}[✓] Daftar non-follback berhasil disimpan ke file: {filename}{RESET}")
    except Exception as e:
        print(f"{YELLOW}[!] Gagal menyimpan file hasil scan: {e}{RESET}")


def run_process(mode: str):
    """
    mode:
    - 'scan': hanya scan dan tampilkan
    - 'dry_run': scan lalu simulasi unfollow
    - 'real': scan lalu unfollow nyata
    """
    is_dry_run = (mode != "real")
    unfollower = InstagramUnfollower(dry_run=is_dry_run)

    try:
        print(f"\n{CYAN}[*] Menginisialisasi browser Microsoft Edge...{RESET}")
        unfollower.init_driver()

        # Cek login
        if not unfollower.check_login():
            print(f"{RED}[✗] Proses dibatalkan karena belum login.{RESET}")
            return

        my_user = unfollower.get_my_username()
        print(f"\n{GREEN}{BOLD}[*] Memulai pemindaian akun untuk: @{my_user}{RESET}")

        # Scan Following & Followers
        following, followers, non_followers = unfollower.scan_non_followers()

        print("\n" + "="*50)
        print(f"{BOLD}HASIL PEMINDAIAN INSTAGRAM:{RESET}")
        print(f"• Total Following (Anda ikuti) : {CYAN}{len(following)}{RESET}")
        print(f"• Total Followers (Mengikuti)  : {GREEN}{len(followers)}{RESET}")
        print(f"• Tidak Follback (Non-Follback): {RED}{len(non_followers)}{RESET}")
        print("="*50)

        if not non_followers:
            print(f"\n{GREEN}[✓] Hebat! Semua akun yang Anda ikuti sudah follback balik, atau terlindungi whitelist.{RESET}\n")
            return

        # Simpan hasil scan ke file log
        save_results_to_file(non_followers, my_user)

        # Tampilkan daftar non-follback
        print(f"\n{YELLOW}{BOLD}Daftar Akun yang Tidak Follback:{RESET}")
        for i, u in enumerate(non_followers[:50], 1):
            print(f"  {i}. @{u}")
        if len(non_followers) > 50:
            print(f"  ... dan {len(non_followers) - 50} akun lainnya (lihat file txt tersimpan).")

        if mode == "scan":
            print(f"\n{GREEN}[✓] Pemindaian selesai! Gunakan Menu 2 atau 3 untuk melakukan unfollow.{RESET}\n")
            return

        # Batasi jumlah unfollow per sesi
        limit = config.MAX_UNFOLLOW_LIMIT
        targets = non_followers[:limit]

        print(f"\n{BOLD}Target Unfollow Sesi Ini:{RESET} {CYAN}{len(targets)} akun{RESET} (Maksimal: {limit})")

        if mode == "real":
            print(f"\n{RED}{BOLD}[PERINGATAN REAL MODE]{RESET}")
            print(f"Anda akan melakukan {RED}UNFOLLOW NYATA{RESET} pada {len(targets)} akun di atas.")
            confirm = input(f"Ketik '{BOLD}YA{RESET}' untuk melanjutkan atau tekan Enter untuk batal: ").strip()
            if confirm.upper() != "YA":
                print(f"{YELLOW}[!] Dibatalkan oleh pengguna.{RESET}\n")
                return

        print(f"\n{CYAN}[*] Memulai proses {'Simulasi ' if is_dry_run else ''}Unfollow...{RESET}")
        
        success_count = 0
        failed_count = 0

        for idx, target in enumerate(targets, 1):
            print(f"\n[{idx}/{len(targets)}] Memproses @{target}...")
            success, msg = unfollower.unfollow_user(target)
            if success:
                success_count += 1
                print(f"  {GREEN}[✓] {msg}{RESET}")
            else:
                failed_count += 1
                print(f"  {YELLOW}[!] {msg}{RESET}")

        print("\n" + "="*50)
        print(f"{BOLD}RINGKASAN EKSEKUSI:{RESET}")
        print(f"• Berhasil di-unfollow : {GREEN}{success_count}{RESET}")
        print(f"• Gagal / Dilewati     : {YELLOW}{failed_count}{RESET}")
        print(f"• Mode                 : {YELLOW if is_dry_run else RED}{'DRY RUN (Simulasi)' if is_dry_run else 'REAL MODE'}{RESET}")
        print("="*50 + "\n")

    except KeyboardInterrupt:
        print(f"\n{YELLOW}[!] Proses dihentikan oleh pengguna (Ctrl+C).{RESET}\n")
    except Exception as e:
        print(f"\n{RED}[✗] Terjadi kesalahan: {e}{RESET}\n")
    finally:
        unfollower.close()


def main():
    while True:
        print_banner()
        show_menu()
        choice = input(f"{BOLD}Masukkan pilihan [0-5]: {RESET}").strip()

        if choice == "1":
            run_process(mode="scan")
        elif choice == "2":
            run_process(mode="dry_run")
        elif choice == "3":
            run_process(mode="real")
        elif choice == "4":
            view_whitelist()
        elif choice == "5":
            check_config_info()
        elif choice == "0":
            print(f"\n{GREEN}Terima kasih telah menggunakan Auto Unfollow IG! Sampai jumpa.{RESET}\n")
            sys.exit(0)
        else:
            print(f"\n{RED}[!] Pilihan tidak valid, silakan coba lagi.{RESET}\n")

        input(f"{CYAN}Tekan Enter untuk kembali ke menu utama...{RESET}")


if __name__ == "__main__":
    main()
