# Aplikasi CRUD Data Mahasiswa

UTS Lab Pemrograman - Departemen Bisnis Digital, Universitas Diponegoro (Gasal 2026/2027).

Aplikasi web sederhana untuk mengelola data mahasiswa (Create, Read, Update, Delete)
dengan **Flask** dan **SQLite**.

## Cara menjalankan

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Buka http://127.0.0.1:5000. File database `mahasiswa.db` dibuat otomatis saat
aplikasi pertama kali dijalankan dan tetap ada setelah aplikasi dimatikan.

## Fitur

- Tambah, lihat daftar, lihat detail, ubah, dan hapus mahasiswa
- Pencarian berdasarkan NIM, nama, atau program studi
- Validasi: NIM/nama/program studi/angkatan/IPK wajib diisi, IPK harus 0.00-4.00,
  NIM tidak boleh duplikat
- Lama Studi (tahun) = tahun sekarang - angkatan, dihitung otomatis oleh program

## Struktur

```
app.py            backend Flask + akses database SQLite
templates/        tampilan HTML (Jinja2)
static/style.css  styling
```

## Tabel `mahasiswa`

| Field | Tipe | Keterangan |
|---|---|---|
| nim | INTEGER | primary key (unik) |
| nama | TEXT | wajib |
| program_studi | TEXT | wajib |
| angkatan | INTEGER | wajib |
| ipk | REAL | wajib, 0.00-4.00 |
