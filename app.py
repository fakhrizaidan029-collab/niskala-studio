from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import os

# Muat variabel dari file .env (jika berjalan di komputer lokal)
load_dotenv()

app = Flask(__name__)

# Ambil secret key secara aman dari environment variable sistem/server
app.secret_key = os.environ.get('SECRET_KEY')

# Pengaman: Hentikan aplikasi jika secret key belum diset agar tidak berjalan dengan kunci kosong/bawaan
if not app.secret_key:
    raise RuntimeError("Variabel lingkungan 'SECRET_KEY' belum diatur! Harap atur SECRET_KEY di file .env atau di server hosting.")

DB_NAME = 'company_portfolio.db'

# Fungsi Inisialisasi Database SQLite
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fullname TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0
        )
    ''')
    
    # Tambahkan kolom status dan progress
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS project_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            service TEXT NOT NULL,
            brief TEXT NOT NULL,
            status TEXT DEFAULT 'Menunggu Review',
            progress INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contact_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_name TEXT NOT NULL,
            sender_email TEXT NOT NULL,
            subject TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

# Rute Halaman Utama (Index)
@app.route('/')
def index():
    user = session.get('user_name')
    return render_template('index.html', user=user)

# Rute Registrasi Klien
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        fullname = request.form['fullname']
        email = request.form['email']
        password = request.form['password']
        hashed_pw = generate_password_hash(password)

        # Otomatis jadikan admin jika email mengandung kata 'admin' (untuk testing)
        is_admin = 1 if 'admin' in email.lower() else 0

        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (fullname, email, password, is_admin) VALUES (?, ?, ?, ?)",
                           (fullname, email, hashed_pw, is_admin))
            conn.commit()
            conn.close()
            flash('Registrasi berhasil! Silakan masuk ke portal.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Email sudah terdaftar. Gunakan email lain.', 'error')

    return render_template('register.html')

# Rute Login Klien & Admin
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT id, fullname, password, is_admin FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user[2], password):
            session['user_id'] = user[0]
            session['user_name'] = user[1]
            session['is_admin'] = user[3]
            
            flash(f'Selamat datang kembali, {user[1]}!', 'success')
            
            # Arahkan berdasarkan peran (Admin atau Klien)
            if user[3] == 1:
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('dashboard'))
        else:
            flash('Email atau kata sandi salah.', 'error')

    return render_template('login.html')

# Rute Dashboard Klien Biasa
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session or session.get('is_admin') == 1:
        flash('Silakan masuk terlebih dahulu sebagai klien.', 'error')
        return redirect(url_for('login'))
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Ambil daftar brief/proyek milik user yang sedang login
    cursor.execute('''
        SELECT id, service, brief, status, progress, created_at 
        FROM project_requests 
        WHERE user_id = ? 
        ORDER BY created_at DESC
    ''', (session['user_id'],))
    my_projects = cursor.fetchall()
    conn.close()

    case_studies = [
        {"title": "NovaPay FinTech Architecture", "category": "Cloud & Security", "metric": "Latensi < 50ms, 1.2M Transaksi/hari"},
        {"title": "OrbitCloud ERP", "category": "Enterprise Web App", "metric": "Efisiensi operasional meningkat 42%"},
        {"title": "Aether Logistics AI", "category": "Machine Learning", "metric": "Prediksi rute otomatis akurasi 96%"}
    ]
    return render_template('dashboard.html', user=session['user_name'], case_studies=case_studies, my_projects=my_projects)

# Rute Kirim Brief / Proyek Baru dari Dashboard Klien
@app.route('/request-project', methods=['POST'])
def request_project():
    if 'user_id' not in session or session.get('is_admin') == 1:
        flash('Silakan masuk sebagai klien.', 'error')
        return redirect(url_for('login'))
    
    service = request.form.get('service')
    brief = request.form.get('brief')
    user_id = session.get('user_id')

    # Simpan brief ke database
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO project_requests (user_id, service, brief) VALUES (?, ?, ?)",
                   (user_id, service, brief))
    conn.commit()
    conn.close()

    flash(f'Brief untuk layanan "{service}" berhasil dikirim ke tim Niskala!', 'success')
    return redirect(url_for('dashboard'))

# Rute Dashboard Khusus Admin
@app.route('/admin-dashboard')
def admin_dashboard():
    if 'user_id' not in session or session.get('is_admin') != 1:
        flash('Akses ditolak! Halaman ini khusus Administrator.', 'error')
        return redirect(url_for('login'))
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, fullname, email, is_admin FROM users")
    clients = cursor.fetchall()

    cursor.execute('''
        SELECT project_requests.id, users.fullname, users.email, project_requests.service, 
               project_requests.brief, project_requests.created_at, project_requests.status, project_requests.progress
        FROM project_requests 
        JOIN users ON project_requests.user_id = users.id
        ORDER BY project_requests.created_at DESC
    ''')
    requests_list = cursor.fetchall()

    # Ambil pesan kontak publik
    cursor.execute("SELECT id, sender_name, sender_email, subject, message, created_at FROM contact_messages ORDER BY created_at DESC")
    messages_list = cursor.fetchall()
    
    conn.close()

    return render_template('admin_dashboard.html', user=session['user_name'], clients=clients, requests_list=requests_list, messages_list=messages_list)

# Rute Logout
@app.route('/logout')
def logout():
    session.clear()
    flash('Anda telah keluar dari sesi.', 'info')
    return redirect(url_for('index'))

# Rute Halaman Profil Perusahaan & Struktur Organisasi
@app.route('/profile')
def profile():
    user = session.get('user_name')
    # Data anggota inti tim (Struktur Organisasi)
    team_members = [
        {"name": "Fakhrul R.", "role": "Chief Executive Officer & Lead Architect", "image_icon": "👨‍💻"},
        {"name": "Niskala Team", "role": "Cloud & DevOps Engineering Squad", "image_icon": "☁️"},
        {"name": "Creative Division", "role": "Futuristic UI/UX & Digital Studio", "image_icon": "🎨"}
    ]
    return render_template('profile.html', user=user, team_members=team_members)

# Rute Hapus Brief Proyek dari Admin Dashboard
@app.route('/delete-request/<int:req_id>', methods=['POST'])
def delete_request(req_id):
    if 'user_id' not in session or session.get('is_admin') != 1:
        flash('Akses ditolak!', 'error')
        return redirect(url_for('login'))

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM project_requests WHERE id = ?", (req_id,))
    conn.commit()
    conn.close()

    flash('Brief proyek berhasil dihapus dari sistem.', 'success')
    return redirect(url_for('admin_dashboard'))

# Rute Hapus Akun Klien dari Admin Dashboard
@app.route('/delete-user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    if 'user_id' not in session or session.get('is_admin') != 1:
        flash('Akses ditolak!', 'error')
        return redirect(url_for('login'))

    # Cegah admin menghapus akunnya sendiri yang sedang aktif
    if user_id == session.get('user_id'):
        flash('Anda tidak dapat menghapus akun administrator yang sedang Anda gunakan!', 'error')
        return redirect(url_for('admin_dashboard'))

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Hapus brief milik user tersebut terlebih dahulu agar database tetap bersih
    cursor.execute("DELETE FROM project_requests WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()

    flash('Akun pengguna beserta datanya berhasil dihapus.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/update-project/<int:req_id>', methods=['POST'])
def update_project(req_id):
    if 'user_id' not in session or session.get('is_admin') != 1:
        flash('Akses ditolak!', 'error')
        return redirect(url_for('login'))

    status = request.form.get('status')
    progress = request.form.get('progress', 0)

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE project_requests SET status = ?, progress = ? WHERE id = ?", (status, progress, req_id))
    conn.commit()
    conn.close()

    flash('Status dan progres proyek berhasil diperbarui!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/send-contact', methods=['POST'])
def send_contact():
    sender_name = request.form.get('sender_name')
    sender_email = request.form.get('sender_email')
    subject = request.form.get('subject')
    message = request.form.get('message')

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO contact_messages (sender_name, sender_email, subject, message)
        VALUES (?, ?, ?, ?)
    ''', (sender_name, sender_email, subject, message))
    conn.commit()
    conn.close()

    flash('Pesan Anda telah terkirim! Tim Niskala Studio akan segera menghubungi Anda.', 'success')
    return redirect(url_for('index') + '#contact')

# 4. Rute Hapus Pesan Kontak dari Admin Dashboard
@app.route('/delete-message/<int:msg_id>', methods=['POST'])
def delete_message(msg_id):
    if 'user_id' not in session or session.get('is_admin') != 1:
        flash('Akses ditolak!', 'error')
        return redirect(url_for('login'))

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM contact_messages WHERE id = ?", (msg_id,))
    conn.commit()
    conn.close()

    flash('Pesan kontak berhasil dihapus.', 'success')
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)