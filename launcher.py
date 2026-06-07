import os
import threading
import tempfile
import requests
import shutil
import json
import subprocess
import sys
import customtkinter as ctk

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VERSION_FILE = os.path.join(BASE_DIR, 'version.txt')
CONFIG_FILE = os.path.join(BASE_DIR, 'update_config.json')
RELEASE_DIR = os.path.join(BASE_DIR, 'release')

# UI app
class LauncherApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title('Spielezentrum Launcher')
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

    def _build_ui(self):
        ctk.CTkLabel(self, text='Spielezentrum Launcher', font=ctk.CTkFont(size=22, weight='bold')).pack(padx=20, pady=(18,8))

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
            version_url = self.config.get('version_url')
            if not version_url:
                self._log('Kein version_url in update_config.json konfiguriert.')
                self.status_label.configure(text='Konfig fehlt')
                self.check_btn.configure(state='normal')
                return

            r = requests.get(version_url, timeout=8)
            r.raise_for_status()
            remote = r.text.strip()
            self.remote_version = remote
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
            if not dl_template:
                self._log('Kein download_url_template in update_config.json konfiguriert.')
                self.status_label.configure(text='Konfig fehlt')
                return

            url = dl_template.format(version=self.remote_version)
            self._log(f'Lade von {url} ...')
            r = requests.get(url, stream=True, timeout=20)
            r.raise_for_status()

            if not os.path.exists(RELEASE_DIR):
                os.makedirs(RELEASE_DIR, exist_ok=True)

            dest_path = os.path.join(RELEASE_DIR, f'spielezentrum_{self.remote_version}.exe')
            tmp_fd, tmp_path = tempfile.mkstemp(suffix='.download')
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
