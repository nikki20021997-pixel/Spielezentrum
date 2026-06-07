import os
import threading
import tempfile
import requests
import shutil
import json
import subprocess
import sys
import customtkinter as ctk

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
    # When PyInstaller bundles the app as onefile, data files are extracted into _MEIPASS.
    bundle_dir = getattr(sys, '_MEIPASS', None)
    config_candidates = [os.path.join(BASE_DIR, 'update_config.json')]
    if bundle_dir:
        config_candidates.append(os.path.join(bundle_dir, 'update_config.json'))
    CONFIG_FILE = next((path for path in config_candidates if os.path.exists(path)), config_candidates[0])
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    CONFIG_FILE = os.path.join(BASE_DIR, 'update_config.json')
VERSION_FILE = os.path.join(BASE_DIR, 'version.txt')
RELEASE_DIR = os.path.join(BASE_DIR, 'release')

# UI app
class LauncherApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title('Spielezentrum Update')
        self.geometry('560x360')
        self.resizable(False, False)
        ctk.set_appearance_mode('dark')

        self.local_version = self._read_local_version()
        self.remote_version = None
        self.config = self._read_config()

        self._build_ui()

    def _read_local_version(self):
        try:
            with open(VERSION_FILE, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except Exception:
            return '0.0.0'

    def _read_config(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def _get_github_auth_token(self):
        token = self.config.get('github_token') or os.environ.get('GITHUB_TOKEN')
        return token.strip() if isinstance(token, str) else None

    def _get_request_headers(self, use_github_api=False):
        headers = {
            'User-Agent': 'spielezentrum-launcher'
        }
        if use_github_api:
            headers['Accept'] = 'application/vnd.github.v3+json'
        token = self._get_github_auth_token()
        if token:
            headers['Authorization'] = f'token {token}'
        return headers

    def _get_download_folder(self):
        try:
            if os.path.isdir(BASE_DIR):
                return BASE_DIR
        except Exception:
            pass
        return RELEASE_DIR

    def _build_ui(self):
        ctk.CTkLabel(self, text='Spielezentrum Update', font=ctk.CTkFont(size=22, weight='bold')).pack(padx=20, pady=(18,8))

        self.info_label = ctk.CTkLabel(self, text=f'Lokale Version: {self.local_version}', text_color='#cbd5e1')
        self.info_label.pack(padx=20, pady=(0,12))

        btn_frame = ctk.CTkFrame(self, fg_color='#1f2937')
        btn_frame.pack(fill='x', padx=20, pady=(0,12))

        self.check_btn = ctk.CTkButton(btn_frame, text='Nach Updates suchen', command=self.check_updates)
        self.check_btn.grid(row=0, column=0, padx=12, pady=12)

        self.update_btn = ctk.CTkButton(btn_frame, text='Update herunterladen', state='disabled', command=self.download_update)
        self.update_btn.grid(row=0, column=1, padx=12, pady=12)

        self.run_btn = ctk.CTkButton(btn_frame, text='Starten', command=self.run_app)
        self.run_btn.grid(row=0, column=2, padx=12, pady=12)

        self.status_label = ctk.CTkLabel(self, text='Bereit', text_color='#94a3b8')
        self.status_label.pack(padx=20, pady=(8,0))

        self.log = ctk.CTkTextbox(self, width=520, height=120, fg_color='#0f172a', text_color='#e5e7eb')
        self.log.pack(padx=20, pady=(8,18))
        self.log.insert('0.0', 'Launcher gestartet.\n')
        self.log.configure(state='disabled')

    def _log(self, text):
        self.log.configure(state='normal')
        self.log.insert('end', text + '\n')
        self.log.see('end')
        self.log.configure(state='disabled')

    def check_updates(self):
        self._log('Prüfe Remote-Version...')
        self.status_label.configure(text='Suche Updates...')
        self.check_btn.configure(state='disabled')
        threading.Thread(target=self._do_check).start()

    def _do_check(self):
        try:
            # Prefer querying the GitHub Releases API when a repo is configured
            repo = self.config.get('repo')
            if repo:
                api_url = f'https://api.github.com/repos/{repo}/releases/latest'
                self._log(f'Prüfe Releases-API: {api_url}')
                r = requests.get(api_url, timeout=8, headers=self._get_request_headers(use_github_api=True))
                r.raise_for_status()
                data = r.json()
                tag = data.get('tag_name') or ''
                # normalize version (strip leading 'v' if present)
                remote = tag.lstrip('v') if tag else ''
                self.latest_tag = tag
                self.remote_version = remote
                self._log(f'Gefundene Release-Tag: {tag} -> Version: {remote}')
                self.status_label.configure(text=f'Remote-Version: {remote}')
            else:
                version_url = self.config.get('version_url')
                if not version_url:
                    self._log('Kein version_url oder repo in update_config.json konfiguriert.')
                    self.status_label.configure(text='Konfig fehlt')
                    self.check_btn.configure(state='normal')
                    return

                r = requests.get(version_url, timeout=8)
                r.raise_for_status()
                remote = r.text.strip()
                self.remote_version = remote
                self.latest_tag = None
                self._log(f'Gefundene Version: {remote}')
                self.status_label.configure(text=f'Remote-Version: {remote}')

            if self._is_newer(remote, self.local_version):
                self._log('Update verfügbar.')
                self.update_btn.configure(state='normal')
            else:
                self._log('Du hast bereits die neueste Version.')
                self.update_btn.configure(state='disabled')
        except Exception as e:
            self._log(f'Fehler beim Prüfen: {e}')
            self.status_label.configure(text='Fehler')
        finally:
            self.check_btn.configure(state='normal')

    def _is_newer(self, remote, local):
        def parse(v):
            return [int(x) for x in v.split('.') if x.isdigit()]
        try:
            return parse(remote) > parse(local)
        except Exception:
            return remote != local

    def download_update(self):
        if not self.remote_version:
            return
        self.update_btn.configure(state='disabled')
        self.status_label.configure(text='Lade Update...')
        threading.Thread(target=self._do_download).start()

    def _do_download(self):
        try:
            dl_template = self.config.get('download_url_template')
            repo = self.config.get('repo')

            if dl_template:
                url = dl_template.format(version=self.remote_version)
            elif repo and getattr(self, 'latest_tag', None):
                # construct download URL from repo and tag
                tag = self.latest_tag
                asset_name = f'spielezentrum_{self.remote_version}.exe'
                url = f'https://github.com/{repo}/releases/download/{tag}/{asset_name}'
            else:
                self._log('Kein download_url_template oder repo/release-Tag konfiguriert.')
                self.status_label.configure(text='Konfig fehlt')
                return
            self._log(f'Lade von {url} ...')
            r = requests.get(url, stream=True, timeout=20, headers=self._get_request_headers())
            r.raise_for_status()

            dest_folder = self._get_download_folder()
            if not os.path.exists(dest_folder):
                os.makedirs(dest_folder, exist_ok=True)

            dest_path = os.path.join(dest_folder, f'spielezentrum_{self.remote_version}.exe')
            tmp_fd, tmp_path = tempfile.mkstemp(suffix='.download', dir=dest_folder)
            os.close(tmp_fd)

            with open(tmp_path, 'wb') as f:
                shutil.copyfileobj(r.raw, f)

            shutil.move(tmp_path, dest_path)
            self._log(f'Update gespeichert: {dest_path}')

            # Update local version file
            with open(VERSION_FILE, 'w', encoding='utf-8') as vf:
                vf.write(self.remote_version)
            self.local_version = self.remote_version
            self.info_label.configure(text=f'Lokale Version: {self.local_version}')
            self.status_label.configure(text='Update fertig')

            # If the downloaded asset is a launcher exe, run the updater to replace this running exe
            try:
                name_lower = os.path.basename(dest_path).lower()
                if 'launcher' in name_lower and dest_path.lower().endswith('.exe'):
                    self._log('Launcher-Update erkannt — starte Aktualisierer.')
                    update_bat = os.path.join(BASE_DIR, 'release', 'update.bat')
                    # create update.bat if it doesn't exist
                    if not os.path.exists(update_bat):
                        with open(update_bat, 'w', encoding='utf-8') as ub:
                            ub.write('@echo off\r\n')
                            ub.write('set NEW=%~1\r\n')
                            ub.write('set TARGET=%~2\r\n')
                            ub.write(':waitloop\r\n')
                            ub.write('REM wait until target is not locked\r\n')
                            ub.write('powershell -Command "while (Test-Path -Path \"%TARGET%\" -PathType Leaf -ErrorAction SilentlyContinue) { try { $stream = [System.IO.File]::Open(\"%TARGET%\", \"Open\", \"ReadWrite\") ; $stream.Close(); break } catch { Start-Sleep -Seconds 1 } }"\r\n')
                            ub.write('move /Y "%NEW%" "%TARGET%"\r\n')
                            ub.write('start "" "%TARGET%"\r\n')
                            ub.write('exit /b 0\r\n')

                    # Launch updater and exit so it can replace this exe
                    target_exe = sys.executable if sys.executable else os.path.join(RELEASE_DIR, os.path.basename(dest_path))
                    try:
                        subprocess.Popen([update_bat, dest_path, target_exe], cwd=os.path.join(BASE_DIR, 'release'))
                        self._log('Aktualisierer gestartet.')
                    except Exception as e:
                        self._log(f'Fehler beim Starten des Aktualisierers: {e}')

                    # Quit the launcher application to allow replacement
                    self._log('Beende Launcher für Update.')
                    try:
                        self.quit()
                    except Exception:
                        pass
                    return
            except Exception as e:
                self._log(f'Fehler in Selbstupdate-Logik: {e}')

        except Exception as e:
            self._log(f'Fehler beim Herunterladen: {e}')
            self.status_label.configure(text='Fehler')
        finally:
            self.update_btn.configure(state='normal')

    def run_app(self):
        # Try release exe for current version, then dist, then fall back to running the script
        candidates = []
        candidates.append(os.path.join(RELEASE_DIR, f'spielezentrum_{self.local_version}.exe'))
        candidates.append(os.path.join(BASE_DIR, 'dist', f'spielezentrum_{self.local_version}.exe'))
        candidates.append(os.path.join(BASE_DIR, 'spielezentrum.py'))

        for path in candidates:
            if os.path.exists(path):
                self._log(f'Starte: {path}')
                try:
                    if path.endswith('.exe'):
                        subprocess.Popen([path], cwd=os.path.dirname(path))
                    else:
                        # launch python script
                        subprocess.Popen([sys.executable, path], cwd=BASE_DIR)
                    return
                except Exception as e:
                    self._log(f'Fehler beim Starten: {e}')
        self._log('Keine ausführbare Datei gefunden. Baue das Projekt oder platziere die exe in release/.')


if __name__ == '__main__':
    app = LauncherApp()
    app.mainloop()
