from flask import Flask, request, jsonify
from datetime import datetime, timedelta
import sqlite3
import os

app = Flask(__name__)

# Render'da veritabanı yolu
DB_PATH = os.environ.get('DATABASE_URL', 'license_database.db')

def init_database():
    """Veritabanını başlat"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Licenses tablosu
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS licenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                license_key TEXT UNIQUE NOT NULL,
                license_type TEXT NOT NULL,
                created_date TEXT NOT NULL,
                expiry_date TEXT NOT NULL,
                is_used INTEGER DEFAULT 0,
                used_by TEXT,
                generated_by TEXT DEFAULT 'admin',
                price REAL DEFAULT 0.0,
                hardware_id TEXT,
                last_check TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        print("✅ Veritabanı başlatıldı")
        
    except Exception as e:
        print(f"❌ Veritabanı hatası: {e}")

@app.route('/', methods=['GET'])
def home():
    """Ana sayfa"""
    return jsonify({
        'message': 'ColorBot API is running on Render!',
        'status': 'active',
        'timestamp': datetime.now().isoformat(),
        'endpoints': [
            '/api/health',
            '/api/license/validate',
            '/api/license/activate',
            '/api/license/status'
        ]
    })

@app.route('/api/health', methods=['GET'])
def health():
    """Sağlık kontrolü"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'platform': 'render'
    })

@app.route('/api/license/validate', methods=['POST'])
def validate_license():
    """Lisans doğrulama"""
    try:
        data = request.get_json()
        license_key = data.get('license_key')
        hardware_id = data.get('hardware_id')
        
        if not license_key:
            return jsonify({'valid': False, 'message': 'License key required'}), 400
        
        # Veritabanında kontrol et
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT license_key, license_type, expiry_date, is_used, used_by
            FROM licenses 
            WHERE license_key = ?
        ''', (license_key,))
        
        result = cursor.fetchone()
        
        if not result:
            return jsonify({'valid': False, 'message': 'Lisans anahtarı bulunamadı'}), 404
        
        key, license_type, expiry_date, is_used, used_by = result
        
        # Süre kontrolü
        expiry = datetime.fromisoformat(expiry_date)
        now = datetime.now()
        
        if expiry < now:
            return jsonify({'valid': False, 'message': 'Lisans süresi dolmuş'}), 403
        
        # Son kontrol zamanını güncelle
        cursor.execute('''
            UPDATE licenses SET last_check = ? WHERE license_key = ?
        ''', (now.isoformat(), license_key))
        
        conn.commit()
        conn.close()
        
        license_data = {
            'key': key,
            'type': license_type,
            'expiry_date': expiry_date,
            'is_used': is_used,
            'used_by': used_by,
            'days_remaining': (expiry - now).days
        }
        
        return jsonify({'valid': True, 'license_data': license_data}), 200
        
    except Exception as e:
        return jsonify({'error': f'Internal server error: {e}'}), 500

@app.route('/api/license/activate', methods=['POST'])
def activate_license():
    """Lisans aktivasyon"""
    try:
        data = request.get_json()
        license_key = data.get('license_key')
        username = data.get('username')
        email = data.get('email')
        hardware_id = data.get('hardware_id')
        
        if not license_key:
            return jsonify({'success': False, 'message': 'License key required'}), 400
        
        # Veritabanında kontrol et
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT license_key, license_type, expiry_date, is_used, used_by
            FROM licenses 
            WHERE license_key = ?
        ''', (license_key,))
        
        result = cursor.fetchone()
        
        if not result:
            return jsonify({'success': False, 'message': 'Lisans anahtarı bulunamadı'}), 404
        
        key, license_type, expiry_date, is_used, used_by = result
        
        # Süre kontrolü
        expiry = datetime.fromisoformat(expiry_date)
        now = datetime.now()
        
        if expiry < now:
            return jsonify({'success': False, 'message': 'Lisans süresi dolmuş'}), 403
        
        # Aktivasyon
        cursor.execute('''
            UPDATE licenses 
            SET is_used = 1, used_by = ?, hardware_id = ?, last_check = ?
            WHERE license_key = ?
        ''', (username or 'unknown', hardware_id, now.isoformat(), license_key))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Lisans aktifleştirildi'}), 200
        
    except Exception as e:
        return jsonify({'error': f'Internal server error: {e}'}), 500

@app.route('/api/license/status', methods=['GET'])
def get_license_status():
    """Lisans durumu"""
    try:
        license_key = request.args.get('license_key')
        
        if not license_key:
            return jsonify({'error': 'License key required'}), 400
        
        # Veritabanında kontrol et
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT license_key, license_type, expiry_date, is_used, used_by, hardware_id, last_check
            FROM licenses 
            WHERE license_key = ?
        ''', (license_key,))
        
        result = cursor.fetchone()
        
        if not result:
            return jsonify({'error': 'Lisans anahtarı bulunamadı'}), 404
        
        key, license_type, expiry_date, is_used, used_by, hardware_id, last_check = result
        
        license_data = {
            'key': key,
            'type': license_type,
            'expiry_date': expiry_date,
            'is_used': is_used,
            'used_by': used_by,
            'hardware_id': hardware_id,
            'last_check': last_check,
            'days_remaining': (datetime.fromisoformat(expiry_date) - datetime.now()).days
        }
        
        conn.close()
        
        return jsonify({'license_data': license_data}), 200
        
    except Exception as e:
        return jsonify({'error': f'Internal server error: {e}'}), 500

@app.route('/api/test/add-key', methods=['POST'])
def add_test_key():
    """Test lisans anahtarı ekle"""
    try:
        # Test lisans anahtarı oluştur
        test_key = "TEST-API-KEY-1234-5678-9ABC"
        expiry_date = (datetime.now() + timedelta(days=30)).isoformat()
        
        # Veritabanına ekle
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO licenses 
            (license_key, license_type, created_date, expiry_date, is_used, used_by, generated_by, price)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (test_key, 'test', datetime.now().isoformat(), expiry_date, 0, None, 'test', 0.0))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Test lisans anahtarı eklendi',
            'key': test_key,
            'expiry_date': expiry_date
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Internal server error: {e}'}), 500

if __name__ == '__main__':
    init_database()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
