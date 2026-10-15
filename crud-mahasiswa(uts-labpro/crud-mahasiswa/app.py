"""Aplikasi CRUD Data Mahasiswa - Flask + SQLite.

Jalankan:  python app.py   lalu buka http://127.0.0.1:5000
"""
import sqlite3
from datetime import datetime
from pathlib import Path

from flask import Flask, flash, g, redirect, render_template, request, url_for

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "mahasiswa.db"

app = Flask(__name__)
app.secret_key = "ganti-dengan-kunci-rahasia-sendiri"


# ---------------------------------------------------------------- database
def get_db():
    """Satu koneksi SQLite per request."""
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """Buat tabel jika belum ada. Data lama tidak dihapus."""
    with sqlite3.connect(DB_PATH) as db:
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS mahasiswa (
                nim           INTEGER PRIMARY KEY,
                nama          TEXT    NOT NULL,
                program_studi TEXT    NOT NULL,
                angkatan      INTEGER NOT NULL,
                ipk           REAL    NOT NULL CHECK (ipk >= 0 AND ipk <= 4)
            )
            """
        )


# -------------------------------------------------------------- validasi
def validasi(form, nim_dari_url=None):
    """Kembalikan (data, daftar_error). Dipakai untuk create & update."""
    errors = []
    nim_raw = (nim_dari_url if nim_dari_url is not None else form.get("nim", "")).strip()
    nama = form.get("nama", "").strip()
    prodi = form.get("program_studi", "").strip()
    angkatan_raw = form.get("angkatan", "").strip()
    ipk_raw = form.get("ipk", "").strip().replace(",", ".")

    nim = None
    if not nim_raw:
        errors.append("NIM tidak boleh kosong.")
    elif not nim_raw.isdigit():
        errors.append("NIM harus berupa angka.")
    else:
        nim = int(nim_raw)

    if not nama:
        errors.append("Nama tidak boleh kosong.")
    if not prodi:
        errors.append("Program studi tidak boleh kosong.")

    angkatan = None
    if not angkatan_raw:
        errors.append("Angkatan tidak boleh kosong.")
    elif not angkatan_raw.isdigit():
        errors.append("Angkatan harus berupa angka (contoh: 2023).")
    else:
        angkatan = int(angkatan_raw)
        if angkatan > datetime.now().year:
            errors.append("Angkatan tidak boleh lebih dari tahun sekarang.")

    ipk = None
    if not ipk_raw:
        errors.append("IPK tidak boleh kosong.")
    else:
        try:
            ipk = float(ipk_raw)
            if not 0.00 <= ipk <= 4.00:
                errors.append("IPK harus berada di antara 0.00 dan 4.00.")
        except ValueError:
            errors.append("IPK harus berupa angka (contoh: 3.75).")

    data = {"nim": nim_raw, "nama": nama, "program_studi": prodi,
            "angkatan": angkatan_raw, "ipk": ipk_raw}
    if not errors:
        data = {"nim": nim, "nama": nama, "program_studi": prodi,
                "angkatan": angkatan, "ipk": round(ipk, 2)}
    return data, errors


def tambah_lama_studi(row):
    """Lama Studi dihitung program: tahun sekarang - angkatan (bukan input user)."""
    d = dict(row)
    d["lama_studi"] = datetime.now().year - d["angkatan"]
    return d


# ------------------------------------------------------------------ route
@app.route("/")
def index():
    q = request.args.get("q", "").strip()
    db = get_db()
    if q:
        like = f"%{q}%"
        rows = db.execute(
            "SELECT * FROM mahasiswa WHERE CAST(nim AS TEXT) LIKE ? OR nama LIKE ? "
            "OR program_studi LIKE ? ORDER BY nim",
            (like, like, like),
        ).fetchall()
    else:
        rows = db.execute("SELECT * FROM mahasiswa ORDER BY nim").fetchall()
    return render_template("index.html", mahasiswa=[tambah_lama_studi(r) for r in rows], q=q)


@app.route("/tambah", methods=["GET", "POST"])
def tambah():
    if request.method == "POST":
        data, errors = validasi(request.form)
        if not errors:
            db = get_db()
            ada = db.execute("SELECT 1 FROM mahasiswa WHERE nim = ?", (data["nim"],)).fetchone()
            if ada:
                errors.append(f"NIM {data['nim']} sudah terdaftar.")
        if errors:
            for e in errors:
                flash(e, "error")
            return render_template("form.html", mode="tambah", m=data), 400
        db.execute(
            "INSERT INTO mahasiswa (nim, nama, program_studi, angkatan, ipk) VALUES (?,?,?,?,?)",
            (data["nim"], data["nama"], data["program_studi"], data["angkatan"], data["ipk"]),
        )
        db.commit()
        flash(f"Mahasiswa {data['nama']} berhasil ditambahkan.", "ok")
        return redirect(url_for("index"))
    return render_template("form.html", mode="tambah", m={})


@app.route("/mahasiswa/<int:nim>")
def detail(nim):
    row = get_db().execute("SELECT * FROM mahasiswa WHERE nim = ?", (nim,)).fetchone()
    if row is None:
        flash("Data mahasiswa tidak ditemukan.", "error")
        return redirect(url_for("index"))
    return render_template("detail.html", m=tambah_lama_studi(row))


@app.route("/mahasiswa/<int:nim>/ubah", methods=["GET", "POST"])
def ubah(nim):
    db = get_db()
    row = db.execute("SELECT * FROM mahasiswa WHERE nim = ?", (nim,)).fetchone()
    if row is None:
        flash("Data mahasiswa tidak ditemukan.", "error")
        return redirect(url_for("index"))
    if request.method == "POST":
        # NIM adalah kunci data, jadi diambil dari URL dan tidak bisa diubah.
        data, errors = validasi(request.form, nim_dari_url=str(nim))
        if errors:
            for e in errors:
                flash(e, "error")
            return render_template("form.html", mode="ubah", m=data), 400
        db.execute(
            "UPDATE mahasiswa SET nama=?, program_studi=?, angkatan=?, ipk=? WHERE nim=?",
            (data["nama"], data["program_studi"], data["angkatan"], data["ipk"], nim),
        )
        db.commit()
        flash("Data mahasiswa berhasil diperbarui.", "ok")
        return redirect(url_for("detail", nim=nim))
    return render_template("form.html", mode="ubah", m=dict(row))


@app.route("/mahasiswa/<int:nim>/hapus", methods=["POST"])
def hapus(nim):
    db = get_db()
    cur = db.execute("DELETE FROM mahasiswa WHERE nim = ?", (nim,))
    db.commit()
    if cur.rowcount:
        flash(f"Mahasiswa dengan NIM {nim} dihapus.", "ok")
    else:
        flash("Data mahasiswa tidak ditemukan.", "error")
    return redirect(url_for("index"))


init_db()

if __name__ == "__main__":
    app.run(debug=True)
