import os
import sqlite3
import tkinter as tk
from contextlib import contextmanager
from datetime import date
from tkinter import ttk, messagebox

DB_NAME = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mahasiswa.db")
DAFTAR_PRODI = ["Informatika", "Sistem Informasi", "Manajemen", "Akuntansi"]

@contextmanager
def koneksi():
    """Membuka koneksi, menyimpan perubahan, lalu selalu menutupnya."""
    conn = sqlite3.connect(DB_NAME)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def buat_tabel():
    with koneksi() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS mahasiswa (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                nama     TEXT NOT NULL,
                nim      TEXT NOT NULL UNIQUE,
                prodi    TEXT NOT NULL,
                alamat   TEXT,
                angkatan INTEGER
            )
        """)
        kolom_ada = [r[1] for r in conn.execute("PRAGMA table_info(mahasiswa)")]
        if "angkatan" not in kolom_ada:
            conn.execute("ALTER TABLE mahasiswa ADD COLUMN angkatan INTEGER")


buat_tabel()

root = tk.Tk()
root.title("Aplikasi Data Mahasiswa")
root.geometry("960x640")

form = ttk.LabelFrame(root, text="Formulir Mahasiswa", padding=12)
form.pack(fill="x", padx=15, pady=12)

ttk.Label(form, text="Nama").grid(row=0, column=0, padx=5, pady=5, sticky="w")
entry_nama = ttk.Entry(form, width=30)
entry_nama.grid(row=0, column=1, padx=5, pady=5)

ttk.Label(form, text="NIM").grid(row=0, column=2, padx=5, pady=5, sticky="w")
entry_nim = ttk.Entry(form, width=30)
entry_nim.grid(row=0, column=3, padx=5, pady=5)

ttk.Label(form, text="Program Studi").grid(row=1, column=0, padx=5, pady=5, sticky="w")
combo_prodi = ttk.Combobox(form, values=DAFTAR_PRODI, state="readonly", width=27)
combo_prodi.grid(row=1, column=1, padx=5, pady=5)

ttk.Label(form, text="Alamat").grid(row=1, column=2, padx=5, pady=5, sticky="w")
entry_alamat = ttk.Entry(form, width=30)
entry_alamat.grid(row=1, column=3, padx=5, pady=5)

ttk.Label(form, text="Angkatan").grid(row=2, column=0, padx=5, pady=5, sticky="w")
entry_angkatan = ttk.Entry(form, width=30)
entry_angkatan.grid(row=2, column=1, padx=5, pady=5)

# --- Baris pencarian ---
baris_cari = ttk.Frame(root)
baris_cari.pack(fill="x", padx=15)
ttk.Label(baris_cari, text="Cari (nama / NIM):").pack(side="left")
entry_cari = ttk.Entry(baris_cari, width=30)
entry_cari.pack(side="left", padx=6)

# --- Treeview ---
kolom = ("id", "nama", "nim", "prodi", "alamat", "angkatan")
frame_tabel = ttk.Frame(root)
frame_tabel.pack(fill="both", expand=True, padx=15, pady=8)

tabel = ttk.Treeview(frame_tabel, columns=kolom, show="headings", selectmode="browse")
for key, judul in [("id", "ID"), ("nama", "Nama"), ("nim", "NIM"),
                   ("prodi", "Program Studi"), ("alamat", "Alamat"),
                   ("angkatan", "Angkatan")]:
    tabel.heading(key, text=judul)

tabel.column("id", width=45, anchor="center")
tabel.column("nama", width=170)
tabel.column("nim", width=110)
tabel.column("prodi", width=150)
tabel.column("alamat", width=240)
tabel.column("angkatan", width=80, anchor="center")

scroll = ttk.Scrollbar(frame_tabel, orient="vertical", command=tabel.yview)
tabel.configure(yscrollcommand=scroll.set)
tabel.pack(side="left", fill="both", expand=True)
scroll.pack(side="right", fill="y")

# --- Bilah status ---
status = tk.StringVar(value="")
ttk.Label(root, textvariable=status, anchor="w").pack(fill="x", padx=15, pady=(0, 8))


def tampilkan_data():
    """SELECT: tampilkan semua data, atau hasil pencarian jika kotak cari terisi."""
    for item in tabel.get_children():
        tabel.delete(item)

    kata_kunci = entry_cari.get().strip()
    with koneksi() as conn:
        if kata_kunci:
            pola = f"%{kata_kunci}%"
            rows = conn.execute(
                """SELECT id, nama, nim, prodi, alamat, angkatan
                   FROM mahasiswa
                   WHERE nama LIKE ? OR nim LIKE ?
                   ORDER BY id DESC""",
                (pola, pola),
            ).fetchall()
        else:
            rows = conn.execute(
                """SELECT id, nama, nim, prodi, alamat, angkatan
                   FROM mahasiswa ORDER BY id DESC"""
            ).fetchall()

    for row in rows:
        tabel.insert("", tk.END, values=tuple("" if v is None else v for v in row))

    if kata_kunci:
        status.set(f"{len(rows)} data cocok dengan \"{kata_kunci}\".")
    else:
        status.set(f"Total {len(rows)} data mahasiswa.")


def bersihkan_form():
    entry_nama.delete(0, tk.END)
    entry_nim.delete(0, tk.END)
    combo_prodi.set("")
    entry_alamat.delete(0, tk.END)
    entry_angkatan.delete(0, tk.END)
    entry_nama.focus_set()


def baca_form():
    """Membaca dan memvalidasi formulir.
    Mengembalikan (nama, nim, prodi, alamat, angkatan) atau None bila tidak valid."""
    nama = entry_nama.get().strip()
    nim = entry_nim.get().strip()
    prodi = combo_prodi.get().strip()
    alamat = entry_alamat.get().strip()
    teks_angkatan = entry_angkatan.get().strip()

    if not nama or not nim or not prodi:
        messagebox.showwarning("Validasi", "Nama, NIM, dan Program Studi wajib diisi.")
        return None

    angkatan = None
    if teks_angkatan:
        tahun_ini = date.today().year
        if not (teks_angkatan.isdigit() and len(teks_angkatan) == 4
                and 1990 <= int(teks_angkatan) <= tahun_ini):
            messagebox.showwarning(
                "Validasi", f"Angkatan harus berupa tahun 4 digit (1990–{tahun_ini}).")
            return None
        angkatan = int(teks_angkatan)

    return nama, nim, prodi, alamat, angkatan


def simpan_data():
    """INSERT"""
    data = baca_form()
    if data is None:
        return

    try:
        with koneksi() as conn:
            conn.execute(
                """INSERT INTO mahasiswa (nama, nim, prodi, alamat, angkatan)
                   VALUES (?, ?, ?, ?, ?)""",
                data,
            )
        messagebox.showinfo("Berhasil", "Data berhasil disimpan.")
        tampilkan_data()
        bersihkan_form()
    except sqlite3.IntegrityError:
        messagebox.showerror("NIM Duplikat", "NIM sudah terdaftar.")
    except sqlite3.Error as error:
        messagebox.showerror("Kesalahan Database", str(error))


def isi_form_dari_tabel(event=None):
    """Memuat record terpilih ke form. Dibaca ulang dari database agar
    NIM berawalan nol (misalnya 00123) tidak berubah."""
    pilihan = tabel.selection()
    if not pilihan:
        return
    record_id = int(tabel.item(pilihan[0], "values")[0])

    with koneksi() as conn:
        row = conn.execute(
            "SELECT nama, nim, prodi, alamat, angkatan FROM mahasiswa WHERE id = ?",
            (record_id,),
        ).fetchone()
    if row is None:
        return

    bersihkan_form()
    entry_nama.insert(0, row[0])
    entry_nim.insert(0, row[1])
    combo_prodi.set(row[2])
    entry_alamat.insert(0, row[3] or "")
    entry_angkatan.insert(0, "" if row[4] is None else str(row[4]))


def ubah_data():
    """UPDATE"""
    pilihan = tabel.selection()
    if not pilihan:
        messagebox.showwarning("Pilih Data", "Pilih data yang akan diubah.")
        return
    record_id = int(tabel.item(pilihan[0], "values")[0])

    data = baca_form()
    if data is None:
        return

    try:
        with koneksi() as conn:
            conn.execute(
                """UPDATE mahasiswa
                   SET nama = ?, nim = ?, prodi = ?, alamat = ?, angkatan = ?
                   WHERE id = ?""",
                data + (record_id,),
            )
        tampilkan_data()
        bersihkan_form()
        messagebox.showinfo("Berhasil", "Data berhasil diperbarui.")
    except sqlite3.IntegrityError:
        messagebox.showerror("NIM Duplikat", "NIM sudah digunakan data lain.")
    except sqlite3.Error as error:
        messagebox.showerror("Kesalahan Database", str(error))


def hapus_data():
    """DELETE"""
    pilihan = tabel.selection()
    if not pilihan:
        messagebox.showwarning("Pilih Data", "Pilih baris yang akan dihapus.")
        return

    data = tabel.item(pilihan[0], "values")
    record_id = int(data[0])
    if not messagebox.askyesno("Konfirmasi", f"Hapus data {data[1]}?"):
        return

    try:
        with koneksi() as conn:
            conn.execute("DELETE FROM mahasiswa WHERE id = ?", (record_id,))
    except sqlite3.Error as error:
        messagebox.showerror("Kesalahan Database", str(error))
        return

    tampilkan_data()
    bersihkan_form()


def reset_pencarian():
    entry_cari.delete(0, tk.END)
    tampilkan_data()


tabel.bind("<<TreeviewSelect>>", isi_form_dari_tabel)
entry_cari.bind("<Return>", lambda e: tampilkan_data())
entry_cari.bind("<KeyRelease>", lambda e: tampilkan_data())

ttk.Button(baris_cari, text="Cari", command=tampilkan_data).pack(side="left", padx=2)
ttk.Button(baris_cari, text="Reset", command=reset_pencarian).pack(side="left", padx=2)

baris_tombol = ttk.Frame(root)
baris_tombol.pack(fill="x", padx=15, pady=(0, 10))

ttk.Button(baris_tombol, text="Simpan Data", command=simpan_data).pack(side="left", padx=4)
ttk.Button(baris_tombol, text="Ubah Data", command=ubah_data).pack(side="left", padx=4)
ttk.Button(baris_tombol, text="Refresh", command=tampilkan_data).pack(side="left", padx=4)
ttk.Button(baris_tombol, text="Bersihkan Form", command=bersihkan_form).pack(side="left", padx=4)
ttk.Button(baris_tombol, text="Hapus Data Terpilih", command=hapus_data).pack(side="right", padx=4)

tampilkan_data()
root.mainloop()
