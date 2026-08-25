import os
import time
import random
import re
from typing import Set, List, Tuple, Optional

from selenium import webdriver
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    WebDriverException,
    ElementClickInterceptedException,
)
from webdriver_manager.microsoft import EdgeChromiumDriverManager

import config


def parse_count_string(text: str) -> int:
    """Mengubah format angka Instagram ('628', '1,170', '1.170', '1.2K', '1M') menjadi integer."""
    if not text:
        return 0
    t = text.strip().upper().replace(",", "").replace(".", "")
    try:
        if "K" in t:
            num = float(t.replace("K", ""))
            return int(num * 1000)
        if "M" in t:
            num = float(t.replace("M", ""))
            return int(num * 1000000)
        return int(re.sub(r"[^\d]", "", t) or 0)
    except Exception:
        return 0


class InstagramUnfollower:
    def __init__(self, dry_run: bool = config.DEFAULT_DRY_RUN):
        self.dry_run = dry_run
        self.driver: Optional[webdriver.Edge] = None
        self.whitelist: Set[str] = config.load_whitelist()
        self.my_username: str = config.INSTAGRAM_USERNAME
        self.user_id: Optional[str] = None

    def init_driver(self) -> webdriver.Edge:
        """Inisialisasi WebDriver Microsoft Edge dengan Profil Otomasi Permanen."""
        options = EdgeOptions()
        options.page_load_strategy = "eager"

        if os.path.exists(config.EDGE_BINARY_PATH):
            options.binary_location = config.EDGE_BINARY_PATH

        if config.USE_REMOTE_DEBUGGING:
            debugger_address = f"127.0.0.1:{config.REMOTE_DEBUGGING_PORT}"
            options.add_experimental_option("debuggerAddress", debugger_address)
            print(f"[*] Menghubungkan ke Microsoft Edge di {debugger_address}...")
        else:
            user_data_dir = os.path.abspath(config.AUTOMATION_PROFILE_DIR)
            profile_dir = config.EDGE_PROFILE_DIR
            os.makedirs(user_data_dir, exist_ok=True)
            
            options.add_argument(f"--user-data-dir={user_data_dir}")
            options.add_argument(f"--profile-directory={profile_dir}")
            print(f"[*] Menggunakan direktori profil otomasi: {user_data_dir}")

        if config.HEADLESS_MODE:
            options.add_argument("--headless=new")

        # Argumen stealth & stabilitas Fedora Linux
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-notifications")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-first-run")
        options.add_argument("--no-default-browser-check")
        options.add_argument("--disable-features=Translate,OptimizationHints,MediaRouter")
        options.add_argument("--start-maximized")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        try:
            try:
                self.driver = webdriver.Edge(options=options)
            except Exception:
                driver_path = EdgeChromiumDriverManager().install()
                service = EdgeService(driver_path)
                self.driver = webdriver.Edge(service=service, options=options)

            self.driver.set_page_load_timeout(config.PAGE_TIMEOUT_SECONDS)
            self.driver.set_script_timeout(60)
            print("[✓] Microsoft Edge berhasil dibuka!")
            return self.driver

        except WebDriverException as e:
            print(f"\n[✗] Gagal membuka WebDriver Microsoft Edge: {e}")
            raise e

    def is_logged_in(self) -> bool:
        """Memeriksa apakah akun benar-benar sudah login di Instagram."""
        if not self.driver:
            return False

        try:
            cookies = {c["name"]: c.get("value", "") for c in self.driver.get_cookies()}
            if cookies.get("sessionid"):
                return True
        except Exception:
            pass

        try:
            logged_in_nav = self.driver.find_elements(
                By.XPATH,
                "//a[contains(@href, '/') and (.//span[text()='Profile' or text()='Profil' or text()='Home' or text()='Beranda' or text()='Messages' or text()='Pesan'] or .//svg[@aria-label='Home' or @aria-label='Beranda' or @aria-label='Direct' or @aria-label='Messenger'])]"
            )
            if any(elem.is_displayed() for elem in logged_in_nav):
                return True
        except Exception:
            pass

        current_url = self.driver.current_url.lower()
        if "accounts/login" in current_url or "accounts/emailsignup" in current_url:
            return False

        try:
            login_inputs = self.driver.find_elements(By.NAME, "username")
            if any(inp.is_displayed() for inp in login_inputs):
                return False
        except Exception:
            pass

        return False

    def check_login(self) -> bool:
        """Memverifikasi sesi login Instagram, dan memandu login 1x jika belum ada."""
        if not self.driver:
            raise RuntimeError("Driver belum diinisialisasi.")

        print("[*] Memeriksa status sesi login Instagram...")
        self.driver.get("https://www.instagram.com/")
        time.sleep(3)

        if self.is_logged_in():
            print("[✓] Status: Sesi login Instagram aktif!")
            return True

        print(f"\n{'='*70}")
        print("[!] Sesi login Instagram belum aktif pada profil otomasi ini.")
        print("[i] Silakan LOGIN 1 KALI SAJA di jendela browser Microsoft Edge")
        print("    yang sedang terbuka saat ini.")
        print("[✓] Setelah Anda berhasil login, sesi ini akan TERSIMPAN PERMANEN")
        print("    sehingga Anda tidak perlu login lagi di sesi-sesi berikutnya.")
        print("[*] Menunggu Anda menyelesaikan login di browser (maksimal 300 detik)...")
        print(f"{'='*70}\n")

        max_wait = 300
        start_time = time.time()
        while time.time() - start_time < max_wait:
            time.sleep(3)
            if self.is_logged_in():
                print("\n[✓] Login berhasil terdeteksi! Sesi telah tersimpan secara permanen.")
                time.sleep(2)
                return True

        print("\n[✗] Waktu tunggu login habis. Silakan jalankan ulang script dan lakukan login.")
        return False

    def get_my_username(self) -> str:
        """Mendapatkan username akun yang sedang login."""
        if self.my_username:
            return self.my_username

        if not self.driver:
            raise RuntimeError("Driver belum diinisialisasi.")

        print("[*] Mendeteksi username akun Anda...")
        
        try:
            detected = self.driver.execute_script(r"""
                var links = document.querySelectorAll('a[role="link"], a');
                var excluded = ['explore', 'reels', 'direct', 'stories', 'accounts', 'popular', 'legal', 'about', 'your_activity', 'archive', 'emailsignup'];
                for (var i = 0; i < links.length; i++) {
                    var href = links[i].getAttribute('href') || '';
                    var match = href.match(/^\/([a-zA-Z0-9_\.]+)\/?$/);
                    if (match) {
                        var u = match[1].toLowerCase();
                        if (excluded.indexOf(u) === -1) {
                            if (links[i].querySelector('img') || links[i].querySelector('svg[aria-label*="Profile"]') || links[i].querySelector('svg[aria-label*="Profil"]')) {
                                return match[1];
                            }
                        }
                    }
                }
                return null;
            """)
            if detected:
                self.my_username = detected
                print(f"[✓] Username terdeteksi: @{self.my_username}")
                return self.my_username
        except Exception:
            pass

        try:
            profile_links = self.driver.find_elements(
                By.XPATH,
                "//a[contains(@href, '/')][.//span[normalize-space()='Profile' or normalize-space()='Profil'] or .//img[contains(@alt, 'profile') or contains(@alt, 'profil')]]"
            )
            for pl in profile_links:
                href = pl.get_attribute("href") or ""
                match = re.search(r"instagram\.com/([a-zA-Z0-9_\.]+)/?$", href)
                if match:
                    u = match.group(1).lower()
                    if u not in {"explore", "reels", "direct", "stories", "accounts", "popular", "legal", "about"}:
                        self.my_username = match.group(1)
                        print(f"[✓] Username terdeteksi: @{self.my_username}")
                        return self.my_username
        except Exception:
            pass

        print("\n[?] Otomatisasi membutuhkan username akun Instagram Anda.")
        user_input = input("    Masukkan username Anda (tanpa @): ").strip().lstrip("@")
        self.my_username = user_input
        return self.my_username

    def get_profile_info(self, username: str) -> Tuple[str, int, int]:
        """
        Mengambil User ID, Total Following, dan Total Followers dari Instagram API.
        Mengembalikan (user_id: str, following_count: int, followers_count: int).
        """
        if not self.driver:
            raise RuntimeError("Driver belum diinisialisasi.")

        print(f"[*] Mengambil data profil untuk @{username}...")
        try:
            info = self.driver.execute_async_script("""
                var username = arguments[0];
                var callback = arguments[arguments.length - 1];
                fetch('https://www.instagram.com/api/v1/users/web_profile_info/?username=' + username, {
                    headers: {'X-IG-App-ID': '936619743392459', 'X-Requested-With': 'XMLHttpRequest'}
                }).then(r => r.json()).then(d => {
                    if (d.data && d.data.user) {
                        callback({
                            success: true,
                            id: d.data.user.id,
                            following_count: d.data.user.edge_follow.count,
                            followers_count: d.data.user.edge_followed_by.count
                        });
                    } else {
                        callback({success: false, error: 'Data user tidak ditemukan'});
                    }
                }).catch(e => callback({success: false, error: e.toString()}));
            """, username)

            if info.get("success"):
                self.user_id = str(info["id"])
                return self.user_id, int(info["following_count"]), int(info["followers_count"])
        except Exception as e:
            print(f"[!] Info API gagal ({e}), menggunakan fallback DOM...")

        return "", 0, 0

    def fetch_user_list_api(self, user_id: str, list_type: str, target_count: int) -> List[str]:
        """
        Mengambil 100% daftar username Following atau Followers menggunakan
        Internal Web API dengan cursor pagination (super cepat & 100% presisi).
        """
        print(f"\n[*] Mengambil seluruh data {list_type.upper()} via Web API (Target: {target_count})...")
        collected_users: List[str] = []
        max_id = ""
        page = 1

        while True:
            try:
                res = self.driver.execute_async_script("""
                    var userId = arguments[0];
                    var listType = arguments[1];
                    var maxId = arguments[2];
                    var callback = arguments[arguments.length - 1];
                    
                    var endpoint = (listType === 'following') ? 'following' : 'followers';
                    var url = 'https://www.instagram.com/api/v1/friendships/' + userId + '/' + endpoint + '/?count=200' + (maxId ? '&max_id=' + maxId : '');
                    
                    fetch(url, {
                        headers: {'X-IG-App-ID': '936619743392459', 'X-Requested-With': 'XMLHttpRequest'}
                    }).then(r => r.json()).then(d => {
                        callback({
                            success: true,
                            users: (d.users || []).map(u => u.username.toLowerCase()),
                            next_max_id: d.next_max_id || null
                        });
                    }).catch(e => callback({success: false, error: e.toString()}));
                """, user_id, list_type, max_id)

                if not res.get("success"):
                    print(f"\n[!] API error: {res.get('error')}")
                    break

                batch = res.get("users", [])
                for u in batch:
                    if u not in collected_users:
                        collected_users.append(u)

                total_now = len(collected_users)
                if target_count > 0:
                    percent = min(100.0, (total_now / target_count) * 100)
                    print(f"    -> Terkumpul: {total_now} / {target_count} ({percent:.1f}%) {list_type}...", end="\r")
                else:
                    print(f"    -> Terkumpul: {total_now} {list_type}...", end="\r")

                next_max_id = res.get("next_max_id")
                if next_max_id and len(batch) > 0:
                    max_id = str(next_max_id)
                    time.sleep(0.35 + random.uniform(0.1, 0.2))
                    page += 1
                else:
                    break

            except Exception as e:
                print(f"\n[!] Terjadi kendala saat fetch batch {page}: {e}")
                break

        print(f"\n[✓] Selesai mengambil {list_type}! Total didapatkan: {len(collected_users)}")
        return collected_users

    def scan_non_followers(self) -> Tuple[List[str], List[str], List[str]]:
        """
        Memindai 100% following dan followers secara akurat dan presisi,
        lalu mengembalikan (following_list, followers_list, non_followers_list).
        """
        my_user = self.get_my_username()
        self.whitelist = config.load_whitelist()

        # Buka halaman profil user sekali untuk load context API & Cookie
        self.driver.get(f"https://www.instagram.com/{my_user}/")
        time.sleep(3)

        user_id, following_total, followers_total = self.get_profile_info(my_user)
        print(f"\n{'='*55}")
        print(f"  STATISTIK PROFIL RESMI @{my_user}:")
        print(f"  • Total Following : {following_total} akun")
        print(f"  • Total Followers : {followers_total} akun")
        print(f"{'='*55}")

        # 1. Ambil 100% daftar Following
        if user_id:
            following = self.fetch_user_list_api(user_id, "following", following_total)
            time.sleep(1)
            # 2. Ambil 100% daftar Followers
            followers = self.fetch_user_list_api(user_id, "followers", followers_total)
        else:
            # Fallback DOM
            following = []
            followers = []

        followers_set = {u.lower() for u in followers}
        
        # 3. Hitung non-follback secara 100% presisi
        non_followers = []
        for u in following:
            u_clean = u.lower()
            if u_clean not in followers_set:
                if u_clean not in self.whitelist:
                    non_followers.append(u)
                else:
                    print(f"[i] Akun @{u} tidak follback tapi terlindungi oleh Whitelist.")

        return following, followers, non_followers

    def unfollow_user(self, target_username: str) -> Tuple[bool, str]:
        """
        Melakukan unfollow pada satu akun Instagram.
        Mengembalikan (status_sukses: bool, pesan: str).
        """
        if not self.driver:
            raise RuntimeError("Driver belum diinisialisasi.")

        if self.dry_run:
            sim_delay = random.uniform(1.0, 2.0)
            time.sleep(sim_delay)
            return True, f"[SIMULASI / DRY-RUN] Berhasil mensimulasikan unfollow @{target_username}"

        if target_username.lower() in self.whitelist:
            return False, f"Dibatalkan: Akun @{target_username} ada di dalam Whitelist"

        profile_url = f"https://www.instagram.com/{target_username}/"
        self.driver.get(profile_url)
        time.sleep(random.uniform(2.5, 3.5))

        # Cari tombol "Following" / "Mengikuti" / "Requested" / "Diminta"
        following_button = None
        following_xpaths = [
            "//button[normalize-space()='Following' or normalize-space()='Mengikuti']",
            "//button[normalize-space()='Requested' or normalize-space()='Diminta']",
            "//header//button[.//div[normalize-space()='Following' or normalize-space()='Mengikuti']]",
            "//header//button[.//div[normalize-space()='Requested' or normalize-space()='Diminta']]",
            "//header//button[.//span[normalize-space()='Following' or normalize-space()='Mengikuti']]",
            "//header//button[.//svg[@aria-label='Following' or @aria-label='Mengikuti']]",
            "//button[contains(., 'Following') or contains(., 'Mengikuti')]"
        ]

        for xpath in following_xpaths:
            try:
                btns = self.driver.find_elements(By.XPATH, xpath)
                for btn in btns:
                    if btn.is_displayed():
                        following_button = btn
                        break
                if following_button:
                    break
            except Exception:
                continue

        if not following_button:
            try:
                follow_btn = self.driver.find_elements(
                    By.XPATH, "//button[normalize-space()='Follow' or normalize-space()='Ikuti']"
                )
                if any(b.is_displayed() for b in follow_btn):
                    return False, f"Sudah tidak mengikuti @{target_username} (Tombol 'Follow'/'Ikuti' aktif)"
            except Exception:
                pass
            return False, f"Tombol 'Following'/'Mengikuti' tidak ditemukan di profil @{target_username}"

        # Klik tombol Following
        try:
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", following_button)
            time.sleep(0.5)
            following_button.click()
        except ElementClickInterceptedException:
            self.driver.execute_script("arguments[0].click();", following_button)
        except Exception as e:
            return False, f"Gagal mengklik tombol Following: {e}"

        time.sleep(random.uniform(1.2, 2.0))

        # Tunggu dialog konfirmasi unfollow
        confirm_xpaths = [
            "//div[@role='dialog']//button[normalize-space()='Unfollow' or normalize-space()='Batal Mengikuti' or normalize-space()='Berhenti Mengikuti' or normalize-space()='Batalkan ikuti']",
            "//div[@role='dialog']//button[contains(., 'Unfollow') or contains(., 'Batal Mengikuti') or contains(., 'Berhenti Mengikuti') or contains(., 'Batalkan ikuti')]",
            "//div[@role='dialog']//span[normalize-space()='Unfollow' or normalize-space()='Batal Mengikuti']/ancestor::button",
            "//div[@role='dialog']//button[contains(@class, '_a9--') or contains(@class, '_a9_1')]"
        ]

        confirm_button = None
        for xpath in confirm_xpaths:
            try:
                btns = self.driver.find_elements(By.XPATH, xpath)
                for btn in btns:
                    if btn.is_displayed():
                        confirm_button = btn
                        break
                if confirm_button:
                    break
            except Exception:
                continue

        if not confirm_button:
            return False, f"Pop-up konfirmasi unfollow untuk @{target_username} tidak merespons."

        # Klik konfirmasi Unfollow
        try:
            confirm_button.click()
        except Exception:
            self.driver.execute_script("arguments[0].click();", confirm_button)

        delay = random.uniform(config.MIN_DELAY_SECONDS, config.MAX_DELAY_SECONDS)
        time.sleep(delay)

        return True, f"Sukses unfollow @{target_username} (Delay: {delay:.1f} detik)"

    def close(self):
        """Menutup browser jika dibuka oleh script."""
        if self.driver:
            try:
                if not config.USE_REMOTE_DEBUGGING:
                    self.driver.quit()
                    print("[✓] Browser otomasi berhasil ditutup.")
            except Exception:
                pass
            finally:
                self.driver = None
