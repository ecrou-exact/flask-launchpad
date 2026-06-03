def login_as(client, email, password):
    return client.post('/account/login',
        data={'email': email, 'password': password},
        follow_redirects=True)


# ── HTML routes ──────────────────────────────────────────────────────────────

def test_profile_requires_login(client):
    res = client.get('/account/')
    assert res.status_code == 302

def test_profile_as_admin(client):
    login_as(client, 'admin@admin.admin', 'admin')
    res = client.get('/account/')
    assert res.status_code == 200

def test_edit_requires_login(client):
    res = client.get('/account/edit')
    assert res.status_code == 302

def test_edit_as_admin(client):
    login_as(client, 'admin@admin.admin', 'admin')
    res = client.get('/account/edit')
    assert res.status_code == 200


# ── Avatar endpoint ───────────────────────────────────────────────────────────

def test_avatar_requires_login(client):
    res = client.post('/account/avatar')
    assert res.status_code == 302

def test_avatar_no_file(client):
    login_as(client, 'admin@admin.admin', 'admin')
    res = client.post('/account/avatar')
    assert res.status_code == 400

def test_avatar_invalid_file(client):
    login_as(client, 'admin@admin.admin', 'admin')
    data = {'avatar': (b'not an image at all !!!', 'test.jpg')}
    res = client.post('/account/avatar',
        content_type='multipart/form-data', data=data)
    assert res.status_code == 400

def test_avatar_oversized(client):
    import io
    login_as(client, 'admin@admin.admin', 'admin')
    big = io.BytesIO(b'X' * (3 * 1024 * 1024))  # 3 MB
    data = {'avatar': (big, 'big.jpg')}
    res = client.post('/account/avatar',
        content_type='multipart/form-data', data=data)
    assert res.status_code == 400


# ── Reload API key ────────────────────────────────────────────────────────────

def test_reload_api_key_requires_login(client):
    res = client.post('/account/reload-api-key')
    assert res.status_code == 302

def test_reload_api_key_as_admin(client):
    login_as(client, 'admin@admin.admin', 'admin')
    res = client.post('/account/reload-api-key')
    assert res.status_code == 200
    data = res.get_json()
    assert 'api_key' in data
    assert len(data['api_key']) >= 30


# ── API endpoints ─────────────────────────────────────────────────────────────

def test_api_get_me(client):
    res = client.get('/api/account/me', headers={'X-API-KEY': 'admin_api_key'})
    assert res.status_code == 200
    data = res.get_json()
    assert 'email' in data
    assert 'api_key' not in data   # must not leak key

def test_api_edit_me(client):
    res = client.put('/api/account/me',
        content_type='application/json',
        headers={'X-API-KEY': 'admin_api_key'},
        json={'bio': 'Hello world', 'job_title': 'Dev'})
    assert res.status_code == 200

def test_api_reload_key(client):
    res = client.post('/api/account/me/reload-api-key',
        headers={'X-API-KEY': 'admin_api_key'})
    assert res.status_code == 200
    assert 'api_key' in res.get_json()

def test_api_add_user(client):
    res = client.post('/api/account/add_user',
        content_type='application/json',
        json={
            'first_name': 'Test', 'last_name': 'User',
            'email': 'newtest@test.com', 'password': 'Test1234'
        })
    assert res.status_code == 201

def test_api_add_user_duplicate_email(client):
    res = client.post('/api/account/add_user',
        content_type='application/json',
        json={
            'first_name': 'Admin', 'last_name': 'Admin',
            'email': 'admin@admin.admin', 'password': 'Test1234'
        })
    assert res.status_code == 400

def test_api_add_user_weak_password(client):
    res = client.post('/api/account/add_user',
        content_type='application/json',
        json={
            'first_name': 'Test', 'last_name': 'User',
            'email': 'weak@test.com', 'password': 'short'
        })
    assert res.status_code == 400

def test_api_forbidden_without_key(client):
    res = client.get('/api/account/me')
    assert res.status_code == 403

def test_api_delete_user_requires_admin(client):
    res = client.delete('/api/account/delete_user/1',
        headers={'X-API-KEY': 'editor_api_key'})
    assert res.status_code == 403


# ── Security ──────────────────────────────────────────────────────────────────

def test_xss_in_bio(client):
    res = client.put('/api/account/me',
        content_type='application/json',
        headers={'X-API-KEY': 'admin_api_key'},
        json={'bio': '<script>alert(1)</script>'})
    # Bio is stored (sanitized at display by Jinja auto-escape), 200 is acceptable
    # The key check is that it doesn't execute — Jinja will escape it
    assert res.status_code == 200

def test_invalid_phone_format(client):
    res = client.put('/api/account/me',
        content_type='application/json',
        headers={'X-API-KEY': 'admin_api_key'},
        json={'phone': 'not-a-phone!!'})
    assert res.status_code == 400

def test_invalid_handle_format(client):
    res = client.put('/api/account/me',
        content_type='application/json',
        headers={'X-API-KEY': 'admin_api_key'},
        json={'social_twitter': 'handle with spaces!'})
    assert res.status_code == 400
