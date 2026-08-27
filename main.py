import os
import sys
import time
import re
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
    print(f"• Profil Otomasi       : {config.AUTOMATION_PROFILE_DIR}")
    print(f"• Profil Browser       : {config.EDGE_PROFILE_DIR}")
    print(f"• Binary Edge (ELF)    : {config.EDGE_BINARY_PATH}")
    print(f"• Mode Tampilan        : {'Headless' if config.HEADLESS_MODE else 'GUI (Jendela Terbuka)'}")
    print(f"• Max Unfollow / Batch : {config.MAX_UNFOLLOW_LIMIT} akun")
    print(f"• Random Safety Delay  : {config.MIN_DELAY_SECONDS}s - {config.MAX_DELAY_SECONDS}s")
    print(f"• File Whitelist       : {config.WHITELIST_FILE}")
    print()
    print(f"{BOLD}Fitur Batch & Keamanan Akun:{RESET}")
    print(f"1. Setiap batch memproses maksimal {config.MAX_UNFOLLOW_LIMIT} akun.")
    print(f"2. Setelah satu batch selesai, Anda dapat langsung melanjutkan ke batch berikutnya")
    print(f"   {GREEN}tanpa perlu menutup browser dan tanpa memindai ulang dari awal{RESET}.")
    print(f"3. Anda juga dapat memberikan jeda waktu istirahat antar-batch untuk keamanan akun.")
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
        print(f"\n{YELLOW}{BOLD}Daftar Akun yang Tidak Follback ({len(non_followers)} akun):{RESET}")
        for i, u in enumerate(non_followers[:50], 1):
            print(f"  {i}. @{u}")
        if len(non_followers) > 50:
            print(f"  ... dan {len(non_followers) - 50} akun lainnya (tersimpan di file txt).")

        if mode == "scan":
            print(f"\n{GREEN}[✓] Pemindaian selesai! Gunakan Menu 2 atau 3 untuk melakukan unfollow.{RESET}\n")
            return

        # Konfirmasi awal untuk Real Mode sebelum memulai eksekusi
        if mode == "real":
            print(f"\n{RED}{BOLD}[PERINGATAN REAL MODE]{RESET}")
            print(f"Anda akan memulai proses {RED}UNFOLLOW NYATA{RESET} secara bertahap (batch).")
            print(f"Setiap batch akan memproses maksimal {config.MAX_UNFOLLOW_LIMIT} akun.")
            confirm = input(f"Ketik '{BOLD}YA{RESET}' untuk mulai atau tekan Enter untuk batal: ").strip()
            if confirm.upper() != "YA":
                print(f"{YELLOW}[!] Dibatalkan oleh pengguna.{RESET}\n")
                return

        remaining_targets = list(non_followers)
        total_success = 0
        total_failed = 0
        batch_number = 1
        action_blocked = False

        while remaining_targets and not action_blocked:
            batch_limit = config.MAX_UNFOLLOW_LIMIT
            current_batch = remaining_targets[:batch_limit]
            
            print("\n" + "="*55)
            print(f"{CYAN}{BOLD}BATCH #{batch_number}: Memproses {len(current_batch)} akun (Sisa antrean: {len(remaining_targets)} akun){RESET}")
            print("="*55)

            for idx, target in enumerate(current_batch, 1):
                global_idx = total_success + total_failed + 1
                print(f"\n[{idx}/{len(current_batch)}] (Total Akun #{global_idx}) Memproses @{target}...")
                success, msg = unfollower.unfollow_user(target)
                if success:
                    total_success += 1
                    print(f"  {GREEN}[✓] {msg}{RESET}")
                else:
                    total_failed += 1
                    print(f"  {YELLOW}[!] {msg}{RESET}")
                    if "[PERINGATAN]" in msg or "Action Block" in msg or "dibatasi oleh Instagram" in msg:
                        action_blocked = True
                        print(f"\n{RED}{BOLD}[!] PERINGATAN KEAMANAN AKUN:{RESET}")
                        print(f"{RED}Instagram membatasi tindakan unfollow sementara (Action Block).{RESET}")
                        print(f"{YELLOW}Otomatisasi dihentikan untuk melindungi akun Anda.{RESET}\n")
                        break

            # Hapus akun yang sudah diproses dari daftar antrean
            remaining_targets = remaining_targets[len(current_batch):]

            if action_blocked:
                break

            # Jika semua akun telah selesai diproses
            if not remaining_targets:
                print(f"\n{GREEN}{BOLD}[✓] Semua akun non-follback ({len(non_followers)} akun) telah selesai diproses!{RESET}")
                break

            # Tampilkan ringkasan batch yang baru selesai
            print("\n" + "-"*50)
            print(f"{BOLD}Batch #{batch_number} Selesai!{RESET}")
            print(f"• Total berhasil di-unfollow sejauh ini: {GREEN}{total_success}{RESET}")
            print(f"• Sisa akun belum di-unfollow         : {CYAN}{len(remaining_targets)}{RESET} akun")
            print("-" * 50)

            # Tanya user untuk melanjutkan ke batch berikutnya tanpa keluar browser & tanpa scan ulang
            next_count = min(config.MAX_UNFOLLOW_LIMIT, len(remaining_targets))
            print(f"\n{BOLD}[?] Lanjut ke Batch #{batch_number + 1} ({next_count} akun berikutnya)?{RESET}")
            print(f" {GREEN}[Y / Enter]{RESET} Lanjutkan langsung sekarang (tanpa tutup browser & tanpa scan ulang)")
            print(f" {YELLOW}[J <detik>]{RESET} Beri jeda istirahat dulu (contoh: 'J 30' untuk jeda 30 detik) lalu lanjut")
            print(f" {RED}[N]{RESET}        Cukup / Selesai (kembali ke menu utama)")

            choice = input(f"\n{BOLD}Pilihan Anda [Y/n/jeda]: {RESET}").strip().lower()

            if choice in ["", "y", "ya", "yes", "1", "lanjut"]:
                batch_number += 1
                continue
            elif choice.startswith("j"):
                # Parsing waktu jeda (misal: "j 30", "jeda 60", "j30")
                match = re.search(r"\d+", choice)
                delay_sec = int(match.group()) if match else 30
                print(f"\n{YELLOW}[*] Mengambil jeda istirahat selama {delay_sec} detik...{RESET}")
                try:
                    for s in range(delay_sec, 0, -1):
                        print(f"    Melanjutkan dalam {s} detik...", end="\r")
                        time.sleep(1)
                    print(f"    Melanjutkan ke Batch #{batch_number + 1} sekarang!             ")
                except KeyboardInterrupt:
                    print(f"\n{YELLOW}[!] Jeda dilewati, langsung melanjutkan ke batch berikutnya.{RESET}")
                batch_number += 1
                continue
            elif choice in ["n", "no", "tidak", "batal", "0", "exit", "keluar"]:
                print(f"\n{YELLOW}[*] Proses dihentikan oleh pengguna. Sisa {len(remaining_targets)} akun tersimpan di daftar.{RESET}")
                break
            else:
                print(f"\n{YELLOW}[*] Sesi diakhiri. Kembali ke menu utama.{RESET}")
                break

        print("\n" + "="*50)
        print(f"{BOLD}RINGKASAN TOTAL EKSEKUSI:{RESET}")
        print(f"• Total Batch Dijalankan : {BOLD}{batch_number}{RESET}")
        print(f"• Berhasil di-unfollow   : {GREEN}{total_success}{RESET}")
        print(f"• Gagal / Dilewati       : {YELLOW}{total_failed}{RESET}")
        print(f"• Sisa Akun Belum Selesai: {CYAN}{len(remaining_targets)}{RESET}")
        print(f"• Mode                   : {YELLOW if is_dry_run else RED}{'DRY RUN (Simulasi)' if is_dry_run else 'REAL MODE'}{RESET}")
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
