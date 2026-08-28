# KALKULATOR PROMO APPLE — AUTO SYNC ONEDRIVE → GITHUB → NETLIFY

Paket ini sudah menyiapkan alur otomatis supaya Anda cukup **mengubah dan menyimpan Excel master**. GitHub Actions akan mengecek OneDrive secara berkala, membangun data kalkulator, lalu push perubahan ke GitHub. Netlify yang terhubung ke repository akan otomatis menerbitkan versi terbaru.

## 1. Gambaran sistem

```text
Excel master di OneDrive
        │
        │ save / berubah
        ▼
GitHub Actions (cek tiap 5 menit)
        │
        ├─ sync_onedrive.py
        ├─ build_static.py
        └─ commit public/data.json
        │
        ▼
GitHub production branch
        │
        ▼
Netlify Continuous Deployment
        │
        ▼
Link kalkulator publik
```

**Catatan:** schedule GitHub Actions adalah polling. Job terjadwal dapat mengalami keterlambatan saat GitHub sedang padat, sehingga jangan menganggap perubahan muncul persis dalam 5 menit.

---

# 2. Yang perlu Anda siapkan

Akun berikut diperlukan:

1. Microsoft 365 / OneDrive yang menyimpan Excel master.
2. GitHub.
3. Netlify.
4. Akses admin Microsoft Entra ID untuk membuat App Registration dan memberikan permission Microsoft Graph.

Untuk setup perusahaan, gunakan akun Microsoft 365/OneDrive for Business. Jangan menaruh client secret di source code atau di `index.html`.

---

# 3. Siapkan folder Excel master di OneDrive

Buat misalnya:

```text
OneDrive
└── Calculator Promo
    └── Calculator Promo.xlsx
```

File ini adalah **satu-satunya master data**.

Semua perubahan berikut cukup dilakukan di file ini:

- Price List
- Promo Berjalan
- BNPL
- Provider
- Qoala Protection
- Trade in
- atau sheet lain yang dipakai kalkulator

Setelah selesai mengubah Excel, klik **Save**. Tidak perlu membuka Netlify.

---

# 4. Buat GitHub repository

Buat repository baru, misalnya:

```text
calculator-promo-apple
```

Gunakan repository **Private** jika file/kode promo bersifat internal.

Salin isi folder paket ini ke repository. Gunakan folder berikut sebagai root repository:

```text
Calculator Promo Apple Auto Sync/
```

Struktur penting:

```text
.github/workflows/update-promo.yml
scripts/sync_onedrive.py
build_static.py
calculator_promo_server.py
index.html
netlify.toml
requirements.txt
.gitignore
public/index.html
public/data.json
```

File `Calculator Promo.xlsx` ada di paket untuk memudahkan mode lokal, tetapi `.gitignore` sengaja mencegahnya ikut committed ke GitHub.

---

# 5. Buat Microsoft Entra App Registration

Buka:

https://entra.microsoft.com/

Masuk dengan akun admin Microsoft 365 organisasi Anda.

Kemudian:

```text
Identity
→ Applications
→ App registrations
→ New registration
```

Nama contoh:

```text
Promo Calculator Automation
```

Untuk aplikasi background, Anda tidak perlu menambahkan login user untuk workflow ini.

Setelah dibuat, catat:

```text
Application (client) ID
Directory (tenant) ID
```

Nilainya nanti menjadi:

```text
AZURE_CLIENT_ID
AZURE_TENANT_ID
```

---

# 6. Buat Client Secret

Di App Registration:

```text
Certificates & secrets
→ Client secrets
→ New client secret
```

Buat secret, lalu **langsung salin Value**-nya.

Nilainya nanti menjadi:

```text
AZURE_CLIENT_SECRET
```

Jangan masukkan value secret ke file Python, README, screenshot, atau chat.

---

# 7. Berikan Microsoft Graph permission

Di App Registration:

```text
API permissions
→ Add a permission
→ Microsoft Graph
→ Application permissions
```

Gunakan permission minimum yang diizinkan oleh kebijakan Microsoft 365 Anda untuk membaca file OneDrive.

Untuk skenario file-sync aplikasi background, permission aplikasi harus disetujui admin tenant.

Klik:

```text
Grant admin consent
```

Jika organisasi Anda menerapkan pembatasan izin aplikasi, minta admin Microsoft 365/security untuk menyetujui permission tersebut.

---

# 8. Tentukan lokasi file OneDrive

Paket ini mendukung dua cara.

## Cara A — berdasarkan user + path (paling mudah)

Contoh:

```text
ONEDRIVE_USER
sales@perusahaan.com
```

dan:

```text
ONEDRIVE_FILE_PATH
Calculator Promo/Calculator Promo.xlsx
```

Script akan menggunakan alamat OneDrive user tersebut.

## Cara B — berdasarkan Drive ID + Item ID

Bila tim IT Anda sudah memiliki `drive_id` dan `item_id`, isi:

```text
ONEDRIVE_DRIVE_ID
...

ONEDRIVE_ITEM_ID
...
```

Bila dua variabel ini terisi, script akan menggunakannya sebagai alamat file.

---

# 9. Masukkan GitHub Secrets

Buka repository GitHub:

```text
Settings
→ Secrets and variables
→ Actions
→ New repository secret
```

Buat secret berikut:

| Secret | Isi |
|---|---|
| `AZURE_TENANT_ID` | Directory/Tenant ID dari Entra |
| `AZURE_CLIENT_ID` | Application/Client ID |
| `AZURE_CLIENT_SECRET` | Value client secret |
| `ONEDRIVE_USER` | Email/UPN pemilik OneDrive |
| `ONEDRIVE_FILE_PATH` | Path file Excel di OneDrive |

Opsional:

| Secret | Keterangan |
|---|---|
| `ONEDRIVE_DRIVE_ID` | Isi jika menggunakan Drive ID |
| `ONEDRIVE_ITEM_ID` | Isi jika menggunakan Item ID |

**Jangan membuat secret kosong untuk data yang tidak digunakan jika Anda ingin setup lebih sederhana.**

Untuk metode path, minimal isi 5 secret utama pertama.

---

# 10. Upload repository ke GitHub

Pastikan file workflow berada tepat di:

```text
.github/workflows/update-promo.yml
```

Setelah push pertama, buka:

```text
GitHub
→ Actions
→ Auto Update Promo Calculator
```

Klik:

```text
Run workflow
```

Ini menjalankan sync manual untuk pengujian pertama.

---

# 11. Periksa hasil GitHub Actions

Workflow harus berhasil pada langkah:

```text
Checkout production branch
✓
Set up Python
✓
Install dependencies
✓
Download latest Excel from OneDrive
✓
Build public data
✓
Commit only generated website data
✓
```

Jika file Excel berhasil dibaca, `public/data.json` akan berubah sesuai Excel terbaru.

Jika data Excel tidak berubah sejak run sebelumnya, workflow akan mengatakan:

```text
No promo data changes detected. Nothing to commit.
```

Itu normal.

---

# 12. Hubungkan repository ke Netlify

Buka:

https://app.netlify.com/

Pilih:

```text
Add new project
→ Import an existing project
→ GitHub
```

Pilih repository:

```text
calculator-promo-apple
```

Production branch:

```text
main
```

Publish directory:

```text
public
```

`netlify.toml` di paket ini juga sudah menetapkan publish directory ke `public`.

Klik **Deploy/Publish**.

Netlify sekarang terhubung ke repository.

---

# 13. Test end-to-end

Lakukan test pertama:

### Test 1
Ubah satu harga di Excel, misalnya:

```text
Harga Promo
Rp24.999.000
```

menjadi:

```text
Rp23.999.000
```

Save Excel.

### Test 2
Di GitHub:

```text
Actions
→ Auto Update Promo Calculator
→ Run workflow
```

### Test 3
Setelah workflow selesai, cek commit terbaru di GitHub.

Seharusnya ada commit seperti:

```text
chore: auto-update promo data
```

### Test 4
Netlify akan melihat push baru tersebut dan melakukan deploy otomatis.

### Test 5
Buka URL kalkulator Netlify dari HP.

Harga harus sudah berubah.

---

# 14. Setelah setup berhasil: rutinitas Anda sangat sederhana

Mulai tahap ini Anda **tidak perlu lagi deploy manual**.

Rutinitas sehari-hari hanya:

```text
Buka Calculator Promo.xlsx
        ↓
Edit harga / promo / trade in / Qoala / provider
        ↓
Save
        ↓
Selesai
```

Automation akan bekerja di belakang layar.

---

# 15. Berapa cepat perubahan muncul?

Workflow default mengecek OneDrive setiap 5 menit.

Secara praktis:

```text
Excel Save
   ↓
GitHub Actions polling
   ↓
Build data
   ↓
Git push
   ↓
Netlify deploy
   ↓
Website terbaru
```

Perubahan tidak dijamin muncul tepat 5 menit karena scheduled GitHub Actions dapat terlambat pada kondisi tertentu. Untuk operasi toko, polling 5 menit biasanya sudah cukup.

---

# 16. Kenapa Excel tidak langsung dibaca dari browser?

Karena itu akan membuat credential OneDrive/Graph terekspos ke browser staff.

Arsitektur ini sengaja menempatkan credential di:

```text
GitHub Secrets
```

bukan di:

```text
index.html
```

Browser hanya menerima data kalkulator yang sudah diproses menjadi:

```text
public/data.json
```

---

# 17. Jika GitHub Actions gagal

## Error: invalid_client

Periksa:

```text
AZURE_TENANT_ID
AZURE_CLIENT_ID
AZURE_CLIENT_SECRET
```

Pastikan menggunakan **Client Secret Value**, bukan Secret ID.

## Error: access denied / 403

Permission Microsoft Graph belum benar atau belum diberikan admin consent.

## Error: item not found / 404

Periksa:

```text
ONEDRIVE_USER
ONEDRIVE_FILE_PATH
```

Pastikan path relatif terhadap root OneDrive dan nama file persis benar.

Contoh:

```text
Calculator Promo/Calculator Promo.xlsx
```

## Error: downloaded content does not look like xlsx

Biasanya endpoint/credential salah sehingga Graph mengembalikan JSON error atau halaman lain. Baca pesan HTTP di log Actions.

## Netlify tidak berubah

Periksa GitHub terlebih dahulu. Bila `data.json` tidak berubah, berarti Excel/hasil build belum berubah. Bila GitHub sudah membuat commit baru tetapi Netlify belum deploy, periksa deploy log Netlify.

---

# 18. Keamanan

Client secret adalah kredensial sensitif.

Jangan:

- menyimpan secret di `index.html`;
- memasukkan secret ke GitHub repository;
- memasukkan secret ke Excel;
- mengirim secret melalui WhatsApp/grup;
- memasukkan secret ke screenshot.

Gunakan GitHub Actions Secrets.

Jika memungkinkan, gunakan credential yang dapat dibatasi hanya untuk kebutuhan membaca file master dan ikuti kebijakan security perusahaan.

---

# 19. File utama dalam paket

```text
.github/workflows/update-promo.yml
    Automation tiap 5 menit + manual trigger.

scripts/sync_onedrive.py
    Mengambil Calculator Promo.xlsx dari OneDrive melalui Microsoft Graph.

build_static.py
    Mengubah workbook menjadi data.json untuk kalkulator.

calculator_promo_server.py
    Parser workbook untuk mode lokal/static build.

netlify.toml
    Konfigurasi Netlify, publish directory, dan cache data.json.

requirements.txt
    Dependency Python untuk OneDrive sync.

README-AUTO-SYNC.md
    Panduan ini.
```

---

# 20. Catatan tentang kartu kredit dan promo

Kalkulator tetap menggunakan struktur Excel master terbaru Anda. Bila ada penambahan atau perubahan pada sheet promo/kartu kredit/Trade In/Qoala/Provider, `build_static.py` akan membaca data tersebut saat workflow berjalan.

---

## Referensi resmi

GitHub scheduled workflows dan batas frekuensinya:
https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax

Netlify continuous deployment dari Git:
https://docs.netlify.com/deploy/create-deploys/

Microsoft Graph — addressing file di OneDrive:
https://learn.microsoft.com/en-us/graph/onedrive-addressing-driveitems

Microsoft Entra OAuth client credentials:
https://learn.microsoft.com/en-us/entra/identity-platform/v2-oauth2-client-creds-grant-flow
