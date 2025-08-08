from flask import Flask, request, jsonify
from datetime import datetime, timedelta
import sqlite3
import os

app = Flask(__name__)

# In-memory veritabanı kullan (Render.com'da dosya sistemi sorunları olabilir)
DB_PATH = ":memory:"

# Test lisans anahtarları (in-memory)
TEST_LICENSES = {
    "TEST-API-KEY-1234-5678-9ABC": {
        "type": "test",
        "expiry_date": (datetime.now() + timedelta(days=30)).isoformat(),
        "is_used": 0,
        "used_by": None,
        "hardware_id": None,
        "last_check": None
    },
    # Admin panelden oluşturulan key'ler buraya eklenecek
    # Örnek: "QUARX-XXXX-XXXX-XXXX-XXXX": {
    #     "type": "premium",
    #     "expiry_date": (datetime.now() + timedelta(days=30)).isoformat(),
    #     "is_used": 0,
    #     "used_by": None,
    #     "hardware_id": None,
    #     "last_check": None
    # }
}

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
        
        # Test lisans anahtarlarını ekle
        for key, data in TEST_LICENSES.items():
            cursor.execute('''
                INSERT OR REPLACE INTO licenses 
                (license_key, license_type, created_date, expiry_date, is_used, used_by, generated_by, price)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (key, data['type'], datetime.now().isoformat(), data['expiry_date'], 
                  data['is_used'], data['used_by'], 'test', 0.0))
        
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
            '/api/license/status',
            '/api/test/add-key'
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
        
        # Test lisans anahtarlarında kontrol et
        if license_key in TEST_LICENSES:
            license_data = TEST_LICENSES[license_key]
            
            # Süre kontrolü
            expiry = datetime.fromisoformat(license_data['expiry_date'])
            now = datetime.now()
            
            if expiry < now:
                return jsonify({'valid': False, 'message': 'Lisans süresi dolmuş'}), 403
            
            # Son kontrol zamanını güncelle
            license_data['last_check'] = now.isoformat()
            
            response_data = {
                'key': license_key,
                'type': license_data['type'],
                'expiry_date': license_data['expiry_date'],
                'is_used': license_data['is_used'],
                'used_by': license_data['used_by'],
                'days_remaining': (expiry - now).days
            }
            
            return jsonify({'valid': True, 'license_data': response_data}), 200
        else:
            return jsonify({'valid': False, 'message': 'Lisans anahtarı bulunamadı'}), 404
        
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
        
        # Test lisans anahtarlarında kontrol et
        if license_key in TEST_LICENSES:
            license_data = TEST_LICENSES[license_key]
            
            # Süre kontrolü
            expiry = datetime.fromisoformat(license_data['expiry_date'])
            now = datetime.now()
            
            if expiry < now:
                return jsonify({'success': False, 'message': 'Lisans süresi dolmuş'}), 403
            
            # Aktivasyon
            license_data['is_used'] = 1
            license_data['used_by'] = username or 'unknown'
            license_data['hardware_id'] = hardware_id
            license_data['last_check'] = now.isoformat()
            
            return jsonify({'success': True, 'message': 'Lisans aktifleştirildi'}), 200
        else:
            return jsonify({'success': False, 'message': 'Lisans anahtarı bulunamadı'}), 404
        
    except Exception as e:
        return jsonify({'error': f'Internal server error: {e}'}), 500

@app.route('/api/license/status', methods=['GET'])
def get_license_status():
    """Lisans durumu"""
    try:
        license_key = request.args.get('license_key')
        
        if not license_key:
            return jsonify({'error': 'License key required'}), 400
        
        # Test lisans anahtarlarında kontrol et
        if license_key in TEST_LICENSES:
            license_data = TEST_LICENSES[license_key]
            
            response_data = {
                'key': license_key,
                'type': license_data['type'],
                'expiry_date': license_data['expiry_date'],
                'is_used': license_data['is_used'],
                'used_by': license_data['used_by'],
                'hardware_id': license_data['hardware_id'],
                'last_check': license_data['last_check'],
                'days_remaining': (datetime.fromisoformat(license_data['expiry_date']) - datetime.now()).days
            }
            
            return jsonify({'license_data': response_data}), 200
        else:
            return jsonify({'error': 'Lisans anahtarı bulunamadı'}), 404
        
    except Exception as e:
        return jsonify({'error': f'Internal server error: {e}'}), 500

@app.route('/api/license/add', methods=['POST'])
def add_license():
    """Admin panelden lisans anahtarı ekle"""
    try:
        data = request.get_json()
        license_key = data.get('license_key')
        license_type = data.get('license_type')
        expiry_date = data.get('expiry_date')
        
        if not license_key or not license_type or not expiry_date:
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400
        
        # Key zaten var mı kontrol et
        if license_key in TEST_LICENSES:
            return jsonify({'success': False, 'message': 'License key already exists'}), 409
        
        # Yeni key'i ekle
        TEST_LICENSES[license_key] = {
            "type": license_type,
            "expiry_date": expiry_date,
            "is_used": 0,
            "used_by": None,
            "hardware_id": None,
            "last_check": None
        }
        
        return jsonify({
            'success': True,
            'message': 'License key added successfully',
            'key': license_key,
            'type': license_type,
            'expiry_date': expiry_date
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Internal server error: {e}'}), 500

@app.route('/api/test/add-key', methods=['POST'])
def add_test_key():
    """Test lisans anahtarı ekle"""
    try:
        # Test lisans anahtarı zaten mevcut
        test_key = "TEST-API-KEY-1234-5678-9ABC"
        
        return jsonify({
            'success': True,
            'message': 'Test lisans anahtarı mevcut',
            'key': test_key,
            'expiry_date': TEST_LICENSES[test_key]['expiry_date']
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Internal server error: {e}'}), 500

if __name__ == '__main__':
    init_database()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
