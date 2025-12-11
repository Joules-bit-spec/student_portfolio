from types import SimpleNamespace
from app import app
from flask import render_template

with app.test_request_context('/'):
    fake = SimpleNamespace(username='Tester', course=None, profile_picture=None, bio=None)
    try:
        out = render_template('dashboard.html', projects=[], current_user=fake)
        print(out[:1200])
        print('\n--- RENDER OK ---')
    except Exception as e:
        import traceback
        traceback.print_exc()
