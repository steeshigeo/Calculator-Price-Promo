# KALKULATOR PROMO APPLE — GOOGLE DRIVE → GITHUB ACTIONS → NETLIFY

Paket ini disiapkan untuk kalkulator promo Apple versi terakhir. Tujuannya: **Anda cukup mengubah dan menyimpan `Calculator Promo.xlsx` di Google Drive**. GitHub Actions akan mengambil Excel terbaru secara otomatis, membangun `public/data.json`, lalu Netlify yang terhubung ke GitHub akan menerbitkan versi website terbaru.

## HASIL AKHIR

```text
EDIT EXCEL DI GOOGLE DRIVE
          ↓
        SAVE
          ↓
GitHub Actions (cek berkala)
          ↓
sync_google_drive.py
          ↓
     build_static.py
          ↓
  public/data.json berubah
          ↓
      git commit/push
          ↓
Netlify Continuous Deployment
          ↓
LINK KALKULATOR PUBLIK
```

Netlify continuous deployment akan membangun dan menerbitkan ulang site saat ada push ke repository yang terhubung.

Referensi resmi:
- Google Drive API downloads: https://developers.google.com/workspace/drive/api/guides/manage-downloads
- Google Drive API file lookup: https://developers.google.com/workspace/drive/api/guides/search-files
- Netlify continuous deployment: https://docs.netlify.com/deploy/create-deploys/
- GitHub Actions workflow syntax: https://docs.github.com/actions/using-workflows/workflow-syntax-for-github-actions

---

# BAGIAN 1 — YANG PERLU DIKETAHUI SEBELUM MULAI

Paket ini menggunakan **file XLSX biasa di Google Drive**.

Contoh:

```text
Google Drive
└── Calculator Promo
    └── Calculator Promo.xlsx
```

Penting: **jangan mengubah file XLSX menjadi Google Sheets native** untuk alur ini. Script mengharapkan file binary `.xlsx` dan mendownloadnya melalui Google Drive API dengan `alt=media`.

File Excel harus dibagikan ke email **service account** dengan akses minimal **Viewer**.

---

# BAGIAN 2 — BUAT FOLDER DAN FILE MASTER DI GOOGLE DRIVE

1. Buka https://drive.google.com/
2. Buat folder:

```text
Calculator Promo
```

3. Upload file Excel terbaru Anda ke folder tersebut.
4. Nama file boleh tetap:

```text
Calculator Promo.xlsx
```

5. Pastikan file ini adalah **master**.

Mulai sekarang perubahan untuk:

- Price List
- Promo Berjalan
- BNPL
- Provider
- Qoala Protection
- Trade in
- dan sheet lain yang dipakai kalkulator

cukup dilakukan di file ini.

---

# BAGIAN 3 — DAPATKAN GOOGLE DRIVE FILE ID

Buka file Excel di Google Drive.

URL biasanya terlihat seperti:

```text
https://drive.google.com/file/d/1AbCdEfGhIjKlMnOpQrStUvWxYz/view
```

Bagian:

```text
1AbCdEfGhIjKlMnOpQrStUvWxYz
```

adalah **FILE ID**.

Simpan nilai tersebut. Nanti masuk ke GitHub Secret:

```text
GOOGLE_DRIVE_FILE_ID
```

Catatan: setelah file yang sama diedit, **File ID biasanya tetap sama**. Anda tidak perlu mengganti secret setiap kali mengubah isi workbook.

---

# BAGIAN 4 — BUAT GOOGLE CLOUD PROJECT

Buka:

https://console.cloud.google.com/

1. Login dengan akun Google yang mengelola file Drive.
2. Klik project selector.
3. Pilih **New Project**.
4. Contoh nama:

```text
Promo Calculator Automation
```

5. Buat project.

---

# BAGIAN 5 — AKTIFKAN GOOGLE DRIVE API

Di Google Cloud Console:

```text
APIs & Services
→ Library
→ cari: Google Drive API
→ Enable
```

Anda perlu Drive API karena script mengambil file menggunakan Google Drive API.

---

# BAGIAN 6 — BUAT SERVICE ACCOUNT

Di Google Cloud Console:

```text
IAM & Admin
→ Service Accounts
→ Create Service Account
```

Contoh:

```text
Name:
promo-calculator-bot
```

Buat service account.

Setelah dibuat, buka service account tersebut dan catat emailnya. Contohnya:

```text
promo-calculator-bot@promo-calculator-automation.iam.gserviceaccount.com
```

**Email inilah yang harus diberi akses Viewer pada file Excel di Google Drive.**

---

# BAGIAN 7 — BUAT SERVICE ACCOUNT KEY

Di service account:

```text
Keys
→ Add Key
→ Create new key
→ JSON
```

Google akan mengunduh file JSON, misalnya:

```text
promo-calculator-bot-1234567890.json
```

**Jangan upload JSON ini ke GitHub repository.**

Jangan masukkan ke `public/`.

Jangan masukkan ke `index.html`.

Jangan kirim file JSON credential ke chat.

---

# BAGIAN 8 — SHARE EXCEL KE SERVICE ACCOUNT

Kembali ke Google Drive.

Klik kanan:

```text
Calculator Promo.xlsx
→ Share
```

Masukkan email service account, misalnya:

```text
promo-calculator-bot@promo-calculator-automation.iam.gserviceaccount.com
```

Pilih:

```text
Viewer
```

Klik **Send**.

Tidak perlu memberi Editor.

---

# BAGIAN 9 — BUAT GITHUB REPOSITORY

Buka:

https://github.com/

Buat repository baru, misalnya:

```text
calculator-promo-apple
```

Untuk kalkulator dan promo internal, saya menyarankan repository **Private**.

Upload seluruh isi folder paket ini ke repository.

Struktur penting:

```text
.github/
└── workflows/
    └── update-promo-google-drive.yml

scripts/
└── sync_google_drive.py

build_static.py
calculator_promo_server.py
index.html
netlify.toml
requirements.txt
public/
```

---

# BAGIAN 10 — JANGAN UPLOAD SECRET

Pastikan JSON service-account tidak ada di repository.

`.gitignore` pada paket sudah dibuat untuk membantu mencegah file credential ikut ter-commit.

Jika Anda pernah telanjur meng-upload JSON credential ke GitHub, **hapus/rotasi key tersebut** di Google Cloud sebelum melanjutkan.

---

# BAGIAN 11 — UBAH SERVICE ACCOUNT JSON MENJADI BASE64

GitHub Actions akan menerima credential lewat GitHub Secret.

Di Mac/Linux buka Terminal pada folder tempat JSON berada.

Jalankan:

```bash
base64 -i promo-calculator-bot-1234567890.json | tr -d '\n'
```

Salin seluruh hasil yang sangat panjang itu.

Di Windows PowerShell Anda dapat memakai:

```powershell
[Convert]::ToBase64String([IO.File]::ReadAllBytes("promo-calculator-bot-1234567890.json"))
```

Output inilah yang akan menjadi:

```text
GOOGLE_SERVICE_ACCOUNT_JSON_BASE64
```

---

# BAGIAN 12 — BUAT GITHUB SECRETS

Masuk ke repository GitHub:

```text
Settings
→ Secrets and variables
→ Actions
→ New repository secret
```

Buat dua secret wajib:

## SECRET 1

```text
Name:
GOOGLE_SERVICE_ACCOUNT_JSON_BASE64
```

Value:

```text
hasil base64 dari file JSON service account
```

## SECRET 2

```text
Name:
GOOGLE_DRIVE_FILE_ID
```

Value:

```text
File ID Calculator Promo.xlsx
```

Contoh:

```text
1AbCdEfGhIjKlMnOpQrStUvWxYz
```

---

# BAGIAN 13 — TEST GOOGLE DRIVE SYNC DULU

Sebelum menghubungkan Netlify, test GitHub Actions.

Buka:

```text
GitHub
→ repository
→ Actions
→ Auto Update Promo Calculator from Google Drive
→ Run workflow
→ Run workflow
```

Tunggu sampai job selesai.

Klik job tersebut dan cari langkah:

```text
Download latest Excel from Google Drive
```

Jika berhasil, Anda akan melihat informasi file dan pesan seperti:

```text
Google Drive file: Calculator Promo.xlsx
Downloaded: Calculator Promo.xlsx (... bytes)
```

Kemudian:

```text
Build public data
```

harus berhasil.

Jika data kalkulator berubah dibanding commit sebelumnya, workflow akan melakukan commit:

```text
chore: auto-update promo data from Google Drive
```

Jika tidak ada perubahan, workflow mengatakan:

```text
No promo data changes detected. Nothing to commit.
```

Itu normal.

---

# BAGIAN 14 — HUBUNGKAN GITHUB KE NETLIFY

Buka:

https://app.netlify.com/

Kemudian:

```text
Add new project
→ Import an existing project
→ GitHub
```

Pilih repository:

```text
calculator-promo-apple
```

Set publish directory:

```text
public
```

Build command:

```text
kosong
```

Karena GitHub Actions sudah menghasilkan folder `public` yang siap dipublish.

Klik Publish.

Netlify akan memberi URL seperti:

```text
https://nama-kalkulator.netlify.app
```

Netlify mendukung continuous deployment dari repository Git. Setiap push ke production branch yang terhubung akan memicu build/deploy.

---

# BAGIAN 15 — TEST END-TO-END

Lakukan test menggunakan perubahan kecil yang aman.

Misalnya ubah salah satu angka promo di:

```text
Promo Berjalan
```

Save Excel di Google Drive.

Kemudian jalankan manual:

```text
GitHub
→ Actions
→ workflow
→ Run workflow
```

Dengan workflow terjadwal, GitHub juga akan mengecek berkala.

Setelah workflow selesai:

```text
GitHub commit baru
        ↓
Netlify deploy
        ↓
Website update
```

Buka URL kalkulator dari HP dan cek harga yang berubah.

---

# BAGIAN 16 — PENGGUNAAN HARIAN SETELAH SETUP SELESAI

Setelah semuanya berhasil, Anda **tidak perlu menyentuh GitHub atau Netlify untuk perubahan promo biasa**.

Workflow harian Anda cukup:

```text
1. Buka Calculator Promo.xlsx di Google Drive
2. Ubah promo/harga
3. Save
4. Tutup Excel
```

Selesai.

GitHub Actions akan mengecek secara berkala.

Jika isi yang diproses kalkulator berubah:

```text
Google Drive
      ↓
GitHub Actions
      ↓
sync_google_drive.py
      ↓
build_static.py
      ↓
git push
      ↓
Netlify
      ↓
Website terbaru
```

---

# BAGIAN 17 — KENAPA WEBSITE TIDAK LANGSUNG BERUBAH SETELAH SAVE?

Karena workflow menggunakan polling schedule.

Konfigurasi saat ini:

```yaml
cron: "*/5 * * * *"
```

Artinya GitHub Actions dijadwalkan mengecek setiap 5 menit.

GitHub dapat menunda scheduled workflow pada kondisi tertentu, sehingga jangan menjanjikan update tepat pada detik Excel disimpan.

Anda selalu dapat menjalankan workflow manual menggunakan **Run workflow** untuk memaksa pengecekan sekarang.

---

# BAGIAN 18 — TROUBLESHOOTING

## Error: 403 Forbidden

Biasanya service account belum mempunyai akses ke file Excel.

Solusi:

```text
Google Drive
→ Calculator Promo.xlsx
→ Share
→ tambahkan email service account
→ Viewer
```

Kemudian jalankan workflow lagi.

## Error: 404 File not found

Periksa:

```text
GOOGLE_DRIVE_FILE_ID
```

Pastikan hanya File ID-nya, bukan seluruh URL.

## Error: credential invalid

Periksa:

```text
GOOGLE_SERVICE_ACCOUNT_JSON_BASE64
```

Pastikan hasil base64 berasal dari file JSON service account yang benar.

Jika key sudah dicabut/expired, buat key baru dan ganti GitHub Secret.

## Error: not an XLSX blob

File yang digunakan harus benar-benar:

```text
Calculator Promo.xlsx
```

bukan file Google Sheets native.

Jika Anda mengubah file menjadi Google Sheets, gunakan kembali file Excel `.xlsx` sebagai master untuk workflow ini.

## GitHub Actions berhasil tetapi Netlify belum berubah

Masuk ke:

```text
Netlify
→ Deploys
```

Lihat apakah ada deploy baru setelah commit GitHub.

Periksa juga bahwa Netlify terhubung ke repository dan production branch yang sama.

## Website masih menampilkan data lama

`netlify.toml` pada paket sudah memberi header no-cache untuk `data.json`.

Coba refresh halaman di browser HP.

---

# BAGIAN 19 — KEAMANAN

Jangan pernah:

```text
❌ memasukkan service-account JSON ke index.html
❌ memasukkan private_key ke GitHub source code
❌ memasukkan credential ke data.json
❌ membagikan file JSON ke staff umum
❌ memberi akses Editor ke service account jika hanya perlu membaca
```

Service account cukup memiliki akses Viewer terhadap Excel.

GitHub Secret digunakan untuk menyimpan credential agar tidak ditaruh di source code.

---

# BAGIAN 20 — HASIL YANG DIINGINKAN

Setelah setup selesai, target penggunaan Anda adalah:

```text
STAFF / ADMIN
     │
     ▼
Google Drive
     │
     │ edit + save
     ▼
Calculator Promo.xlsx
     │
     ▼
GitHub Actions
     │
     ▼
Website
     │
     ▼
https://kalkulator-anda.netlify.app
```

Staff tidak perlu tahu cara menjalankan Python, GitHub, atau Netlify.

---

# BAGIAN 21 — CHECKLIST SETUP

Centang satu per satu:

```text
[ ] Google Cloud Project dibuat
[ ] Google Drive API di-enable
[ ] Service Account dibuat
[ ] Service Account JSON dibuat
[ ] Excel dibagikan ke email Service Account
[ ] File ID Excel sudah dicatat
[ ] GitHub repository dibuat
[ ] Isi ZIP di-upload ke GitHub
[ ] GOOGLE_SERVICE_ACCOUNT_JSON_BASE64 dibuat
[ ] GOOGLE_DRIVE_FILE_ID dibuat
[ ] GitHub Secrets sudah diisi
[ ] GitHub Actions manual test berhasil
[ ] public/data.json berubah jika Excel berubah
[ ] Netlify sudah terhubung ke GitHub
[ ] URL Netlify bisa dibuka dari HP
[ ] Test perubahan promo berhasil
```

Jika semua tercentang, sistem auto-update sudah aktif.

---

# CATATAN TENTANG FILE XLSX DI PAKET

`Calculator Promo.xlsx` yang ada di paket adalah salinan untuk kebutuhan lokal/backup dan initial build.

Master operasional harian tetap:

```text
Google Drive → Calculator Promo.xlsx
```

GitHub tidak perlu digunakan sebagai tempat Anda mengedit Excel.

---

# FILE UTAMA DALAM PAKET

```text
.github/workflows/update-promo-google-drive.yml
    → workflow otomatis

scripts/sync_google_drive.py
    → download Excel dari Google Drive

build_static.py
    → mengubah Excel menjadi data JSON untuk website

netlify.toml
    → konfigurasi Netlify

public/
    → hasil website siap publish

README-GOOGLE-DRIVE-AUTO-SYNC.md
    → panduan lengkap ini
```
