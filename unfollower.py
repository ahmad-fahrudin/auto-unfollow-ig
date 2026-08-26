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
from selenium.webdriver.common.action_chains import ActionChains
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
        self.user_ids: dict = {}

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
                            id: String(d.data.user.id),
                            following_count: d.data.user.edge_follow.count,
                            followers_count: d.data.user.edge_followed_by.count
                        });
                    } else {
                        callback({success: false, error: 'Data user tidak ditemukan'});
                    }
                }).catch(e => callback({success: false, error: e.toString()}));
            """, username)

            if info.get("success"):
                uid = str(info["id"])
                if username.lower() == self.my_username.lower():
                    self.user_id = uid
                self.user_ids[username.lower()] = uid
                return uid, int(info["following_count"]), int(info["followers_count"])
        except Exception as e:
            print(f"[!] Info API gagal ({e}), menggunakan fallback DOM...")

        return "", 0, 0

    def fetch_user_list_api(self, user_id: str, list_type: str, target_count: int) -> List[str]:
        """
        Mengambil 100% daftar username Following atau Followers menggunakan
        Internal Web API & GraphQL (super cepat & 100% presisi).
        Sekaligus mencatat pemetaan username -> user_id untuk eksekusi API.
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

                    function getCookie(name) {
                        var match = document.cookie.match(new RegExp('(^|;\\\\s*)(' + name + ')=([^;]*)'));
                        return match ? decodeURIComponent(match[3]) : null;
                    }

                    var csrfToken = getCookie('csrftoken') || '';
                    var headers = {
                        'X-CSRFToken': csrfToken,
                        'X-IG-App-ID': '936619743392459',
                        'X-Requested-With': 'XMLHttpRequest',
                        'X-ASBD-ID': '129477'
                    };

                    if (listType === 'followers') {
                        // Gunakan Instagram Web GraphQL endpoint untuk Followers
                        var variables = { id: userId, first: 50 };
                        if (maxId) variables.after = maxId;

                        var url = 'https://www.instagram.com/graphql/query/?query_hash=5aefa9893005572d237da5068082d8d5&variables=' + encodeURIComponent(JSON.stringify(variables));
                        fetch(url, { headers: headers }).then(function(r) {
                            var ct = r.headers.get('content-type') || '';
                            if (ct.includes('json')) {
                                return r.json();
                            }
                            return { error: 'Non-JSON response (' + r.status + ')' };
                        }).then(function(d) {
                            if (d.error) {
                                callback({ success: false, error: d.error });
                                return;
                            }
                            var edge = (d.data && d.data.user && d.data.user.edge_followed_by) || {};
                            var edges = edge.edges || [];
                            var parsed = edges.map(function(e) {
                                var n = e.node || {};
                                return {
                                    username: (n.username || '').toLowerCase(),
                                    id: String(n.id || '')
                                };
                            });
                            var pageInfo = edge.page_info || {};
                            callback({
                                success: true,
                                users: parsed,
                                next_max_id: (pageInfo.has_next_page ? pageInfo.end_cursor : null)
                            });
                        }).catch(function(err) {
                            callback({ success: false, error: err.toString() });
                        });
                    } else {
                        // Gunakan Friendships API endpoint untuk Following
                        var url = 'https://www.instagram.com/api/v1/friendships/' + userId + '/following/?count=200' + (maxId ? '&max_id=' + encodeURIComponent(maxId) : '');
                        fetch(url, { headers: headers }).then(function(r) {
                            var ct = r.headers.get('content-type') || '';
                            if (ct.includes('json')) {
                                return r.json();
                            }
                            return { error: 'Non-JSON response (' + r.status + ')' };
                        }).then(function(d) {
                            if (d.error) {
                                callback({ success: false, error: d.error });
                                return;
                            }
                            var rawUsers = d.users || [];
                            var parsed = rawUsers.map(function(u) {
                                return {
                                    username: (u.username || '').toLowerCase(),
                                    id: String(u.pk || u.id || u.pk_id || '')
                                };
                            });
                            callback({
                                success: true,
                                users: parsed,
                                next_max_id: d.next_max_id || null
                            });
                        }).catch(function(err) {
                            callback({ success: false, error: err.toString() });
                        });
                    }
                """, user_id, list_type, max_id)

                if not res.get("success"):
                    print(f"\n[!] API error: {res.get('error')}")
                    break

                batch = res.get("users", [])
                for u in batch:
                    uname = u.get("username", "").strip().lower()
                    uid = u.get("id", "").strip()
                    if uname:
                        if uid:
                            self.user_ids[uname] = uid
                        if uname not in collected_users:
                            collected_users.append(uname)

                total_now = len(collected_users)
                if target_count > 0:
                    percent = min(100.0, (total_now / target_count) * 100)
                    print(f"    -> Terkumpul: {total_now} / {target_count} ({percent:.1f}%) {list_type}...", end="\r")
                else:
                    print(f"    -> Terkumpul: {total_now} {list_type}...", end="\r")

                next_max_id = res.get("next_max_id")
                if next_max_id and len(batch) > 0:
                    max_id = str(next_max_id)
                    time.sleep(0.2 + random.uniform(0.05, 0.15))
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

    def unfollow_user_api(self, user_id: str) -> Tuple[bool, str, bool]:
        """
        Melakukan unfollow via internal Web API Instagram (direct fetch in browser context).
        Mengembalikan (status_sukses: bool, pesan: str, is_action_blocked: bool).
        """
        try:
            # Dapatkan csrftoken dari selenium cookies jika ada
            csrf_from_driver = ""
            try:
                cookies = {c["name"]: c.get("value", "") for c in self.driver.get_cookies()}
                csrf_from_driver = cookies.get("csrftoken", "")
            except Exception:
                pass

            res = self.driver.execute_async_script("""
                var targetId = arguments[0];
                var driverCsrf = arguments[1] || '';
                var callback = arguments[arguments.length - 1];

                function getCookie(name) {
                    var match = document.cookie.match(new RegExp('(^|;\\\\s*)(' + name + ')=([^;]*)'));
                    return match ? decodeURIComponent(match[3]) : null;
                }

                var csrfToken = getCookie('csrftoken') || driverCsrf;

                async function performUnfollow() {
                    var endpoints = [
                        'https://www.instagram.com/api/v1/web/friendships/' + targetId + '/unfollow/',
                        'https://www.instagram.com/web/friendships/' + targetId + '/unfollow/'
                    ];

                    for (var i = 0; i < endpoints.length; i++) {
                        var url = endpoints[i];
                        try {
                            var r = await fetch(url, {
                                method: 'POST',
                                headers: {
                                    'X-CSRFToken': csrfToken,
                                    'X-IG-App-ID': '936619743392459',
                                    'X-Requested-With': 'XMLHttpRequest',
                                    'X-ASBD-ID': '129477',
                                    'Content-Type': 'application/x-www-form-urlencoded'
                                },
                                body: 'user_id=' + encodeURIComponent(targetId)
                            });

                            var ct = r.headers.get('content-type') || '';
                            if (ct.includes('json')) {
                                var data = await r.json();
                                if (r.ok && data.status === 'ok') {
                                    return { success: true, is_block: false, data: data };
                                } else {
                                    var msg = data.message || data.feedback_message || ('HTTP ' + r.status);
                                    var isBlock = (
                                        data.feedback_required === true ||
                                        data.spam === true ||
                                        (typeof msg === 'string' && (
                                            msg.toLowerCase().includes('feedback_required') ||
                                            msg.toLowerCase().includes('block') ||
                                            msg.toLowerCase().includes('limit') ||
                                            msg.toLowerCase().includes('coba lagi')
                                        ))
                                    );
                                    return {
                                        success: false,
                                        is_block: isBlock,
                                        message: msg,
                                        data: data
                                    };
                                }
                            }
                        } catch (err) {
                            // Coba endpoint alternatif jika ada error network
                        }
                    }
                    return { success: false, is_block: false, message: 'Gagal melakukan request API unfollow.' };
                }

                performUnfollow().then(r => callback(r)).catch(err => callback({ success: false, is_block: false, message: err.toString() }));
            """, user_id, csrf_from_driver)

            if res.get("success"):
                return True, "Sukses (Web API)", False
            elif res.get("is_block"):
                return False, f"Akun dibatasi oleh Instagram (Action Block): {res.get('message')}", True
            else:
                return False, res.get("message") or "API error", False
        except Exception as e:
            return False, f"Exception API: {e}", False

    def unfollow_user_dom(self, target_username: str) -> Tuple[bool, str]:
        """
        Melakukan unfollow via manipulasi antarmuka web (DOM fallback).
        Mengembalikan (status_sukses: bool, pesan: str).
        """
        profile_url = f"https://www.instagram.com/{target_username}/"
        self.driver.get(profile_url)
        time.sleep(random.uniform(2.5, 3.5))

        # Cari tombol "Following" / "Mengikuti" / "Requested" / "Diminta"
        following_button = None
        following_xpaths = [
            "//header//button[.//div[normalize-space()='Following' or normalize-space()='Mengikuti']]",
            "//header//button[.//span[normalize-space()='Following' or normalize-space()='Mengikuti']]",
            "//header//button[.//div[normalize-space()='Requested' or normalize-space()='Diminta']]",
            "//header//button[.//span[normalize-space()='Requested' or normalize-space()='Diminta']]",
            "//header//button[normalize-space()='Following' or normalize-space()='Mengikuti']",
            "//header//button[normalize-space()='Requested' or normalize-space()='Diminta']",
            "//header//button[contains(., 'Following') or contains(., 'Mengikuti')]",
            "//header//button[contains(., 'Requested') or contains(., 'Diminta')]",
            "//header//div[@role='button'][contains(., 'Following') or contains(., 'Mengikuti')]",
            "//button[normalize-space()='Following' or normalize-space()='Mengikuti']",
            "//button[normalize-space()='Requested' or normalize-space()='Diminta']",
            "//button[contains(., 'Following') or contains(., 'Mengikuti')]",
            "//button[contains(., 'Requested') or contains(., 'Diminta')]"
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
            # Periksa apakah sudah tombol Follow (artinya sudah tidak mengikuti)
            try:
                follow_btn = self.driver.find_elements(
                    By.XPATH,
                    "//header//button[normalize-space()='Follow' or normalize-space()='Ikuti'] | //button[normalize-space()='Follow' or normalize-space()='Ikuti']"
                )
                if any(b.is_displayed() for b in follow_btn):
                    return False, f"Sudah tidak mengikuti @{target_username} (Tombol 'Follow'/'Ikuti' aktif)"
            except Exception:
                pass
            return False, f"Tombol 'Following'/'Mengikuti' tidak ditemukan di profil @{target_username}"

        # Klik tombol Following dengan trigger mouse event lengkap
        try:
            self.driver.execute_script("""
                var elem = arguments[0];
                elem.scrollIntoView({block: 'center', inline: 'center'});
                elem.dispatchEvent(new MouseEvent('mouseover', {bubbles: true}));
                elem.dispatchEvent(new MouseEvent('mousedown', {bubbles: true}));
                elem.dispatchEvent(new MouseEvent('mouseup', {bubbles: true}));
                elem.dispatchEvent(new MouseEvent('click', {bubbles: true}));
            """, following_button)
        except Exception:
            try:
                following_button.click()
            except Exception as e:
                return False, f"Gagal mengklik tombol Following: {e}"

        # Polling tunggu dialog konfirmasi unfollow (maksimal 5 detik)
        confirm_xpaths = [
            "//div[@role='dialog']//button[normalize-space()='Unfollow' or normalize-space()='Batal Mengikuti' or normalize-space()='Batalkan Mengikuti' or normalize-space()='Berhenti Mengikuti' or normalize-space()='Batalkan ikuti' or normalize-space()='Batal ikuti']",
            "//div[@role='dialog']//button[contains(., 'Unfollow') or contains(., 'Batal Mengikuti') or contains(., 'Batalkan Mengikuti') or contains(., 'Berhenti Mengikuti') or contains(., 'Batalkan ikuti')]",
            "//div[@role='dialog']//span[normalize-space()='Unfollow' or normalize-space()='Batal Mengikuti']/ancestor::button",
            "//div[@role='dialog']//button[contains(@class, '_a9--') or contains(@class, '_a9_1')]",
            "//div[@role='dialog']//button[not(.//span[normalize-space()='Cancel' or normalize-space()='Batal']) and not(normalize-space()='Cancel' or normalize-space()='Batal') and (normalize-space()!='' or .//*)]",
            "//div[@role='presentation']//button[contains(., 'Unfollow') or contains(., 'Batal Mengikuti') or contains(., 'Batalkan Mengikuti') or contains(., 'Berhenti Mengikuti')]",
            "//button[normalize-space()='Unfollow' or normalize-space()='Batal Mengikuti' or normalize-space()='Batalkan Mengikuti' or normalize-space()='Berhenti Mengikuti']",
            "//button[contains(., 'Unfollow') or contains(., 'Batal Mengikuti') or contains(., 'Batalkan Mengikuti') or contains(., 'Berhenti Mengikuti')]"
        ]

        confirm_button = None
        start_wait = time.time()
        while time.time() - start_wait < 5.0:
            for xpath in confirm_xpaths:
                try:
                    btns = self.driver.find_elements(By.XPATH, xpath)
                    for b in btns:
                        if b.is_displayed():
                            b_text = b.text.strip().lower()
                            if b_text not in ["cancel", "batal", "kembali"]:
                                confirm_button = b
                                break
                    if confirm_button:
                        break
                except Exception:
                    continue
            if confirm_button:
                break
            time.sleep(0.3)

        if not confirm_button:
            # Cek apakah ada popup pembatasan aksi / block dari Instagram
            try:
                block_modals = self.driver.find_elements(
                    By.XPATH,
                    "//div[@role='dialog'][contains(., 'Try Again Later') or contains(., 'Coba Lagi Nanti') or contains(., 'Limit') or contains(., 'Dibatasi')]"
                )
                if any(m.is_displayed() for m in block_modals):
                    return False, f"[PERINGATAN] Akun dibatasi oleh Instagram (Action Block): Terdeteksi popup pembatasan aksi."
            except Exception:
                pass
            return False, f"Pop-up konfirmasi unfollow untuk @{target_username} tidak merespons."

        # Klik konfirmasi Unfollow
        try:
            self.driver.execute_script("""
                var elem = arguments[0];
                elem.dispatchEvent(new MouseEvent('mouseover', {bubbles: true}));
                elem.dispatchEvent(new MouseEvent('mousedown', {bubbles: true}));
                elem.dispatchEvent(new MouseEvent('mouseup', {bubbles: true}));
                elem.dispatchEvent(new MouseEvent('click', {bubbles: true}));
            """, confirm_button)
        except Exception:
            try:
                confirm_button.click()
            except Exception as e:
                return False, f"Gagal mengonfirmasi unfollow: {e}"

        time.sleep(1.2)
        return True, f"Sukses unfollow @{target_username} via DOM"

    def unfollow_user(self, target_username: str) -> Tuple[bool, str]:
        """
        Melakukan unfollow pada satu akun Instagram.
        Menggunakan arsitektur hybrid: Web API langsung (cepat & presisi) + DOM fallback.
        Mengembalikan (status_sukses: bool, pesan: str).
        """
        if not self.driver:
            raise RuntimeError("Driver belum diinisialisasi.")

        target_username = target_username.strip().lstrip("@")
        target_lower = target_username.lower()

        if self.dry_run:
            sim_delay = random.uniform(1.0, 2.0)
            time.sleep(sim_delay)
            return True, f"[SIMULASI / DRY-RUN] Berhasil mensimulasikan unfollow @{target_username}"

        if target_lower in self.whitelist:
            return False, f"Dibatalkan: Akun @{target_username} ada di dalam Whitelist"

        # 1. Coba Unfollow via Internal Web API
        target_id = self.user_ids.get(target_lower)
        if not target_id:
            # Ambil User ID via profile info jika belum tercatat di cache
            target_id, _, _ = self.get_profile_info(target_lower)

        if target_id:
            success, msg, is_blocked = self.unfollow_user_api(target_id)
            if is_blocked:
                return False, f"[PERINGATAN] Akun dibatasi oleh Instagram (Action Block): {msg}"
            if success:
                delay = random.uniform(config.MIN_DELAY_SECONDS, config.MAX_DELAY_SECONDS)
                time.sleep(delay)
                return True, f"Sukses unfollow @{target_username} (Delay: {delay:.1f} detik)"

        # 2. Fallback ke DOM jika API tidak merespons atau ID tidak ditemukan
        success, msg = self.unfollow_user_dom(target_username)
        if success:
            delay = random.uniform(config.MIN_DELAY_SECONDS, config.MAX_DELAY_SECONDS)
            time.sleep(delay)
            return True, f"{msg} (Delay: {delay:.1f} detik)"
        else:
            return False, msg

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

