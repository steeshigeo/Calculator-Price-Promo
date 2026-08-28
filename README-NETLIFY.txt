KALKULATOR PROMO APPLE — NETLIFY

A. Update dari Excel
1. Ganti file Calculator Promo.xlsx dengan master Excel terbaru.
2. Jalankan: python3 build_static.py
3. Hasil terbaru ada di folder public/ (index.html + data.json).

B. Upload ke Netlify tanpa Wi-Fi yang sama
1. Buka Netlify dan login.
2. Pilih Add new project / Deploy manually (Netlify Drop).
3. Upload folder public/.
4. Netlify akan memberi URL publik https://....netlify.app yang bisa dibuka dari HP maupun device lain.

C. Jika Excel berubah lagi
1. Edit & simpan Calculator Promo.xlsx.
2. Jalankan python3 build_static.py.
3. Upload/redeploy folder public/ lagi.

D. Update otomatis via GitHub (opsional)
Simpan folder project di GitHub, letakkan Calculator Promo.xlsx di repository, lalu hubungkan repository ke Netlify.
Tambahkan build command yang menjalankan python3 build_static.py dan publish directory public.
Dengan alur ini, setiap update Excel yang di-commit ke GitHub dapat memicu deploy Netlify otomatis.

E. Mode lokal Mac
Double-click START_CALCULATOR.command. Buka http://127.0.0.1:8765 di Mac. Untuk akses HP di jaringan lokal, gunakan alamat IP yang ditampilkan oleh terminal.
