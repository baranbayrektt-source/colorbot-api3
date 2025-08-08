# ColorBot API

ColorBot lisans yönetim sistemi API'si.

## Endpoints

- `GET /` - Ana sayfa
- `GET /api/health` - Sağlık kontrolü
- `POST /api/license/validate` - Lisans doğrulama
- `POST /api/license/activate` - Lisans aktivasyon
- `GET /api/license/status` - Lisans durumu

## Deployment

Bu API Render.com'da deploy edilmiştir.

## Kullanım

```bash
# Lisans doğrulama
curl -X POST https://your-app.onrender.com/api/license/validate \
  -H "Content-Type: application/json" \
  -d '{"license_key": "your-key", "hardware_id": "your-hwid"}'

# Lisans aktivasyon
curl -X POST https://your-app.onrender.com/api/license/activate \
  -H "Content-Type: application/json" \
  -d '{"license_key": "your-key", "username": "user", "hardware_id": "your-hwid"}'
```
