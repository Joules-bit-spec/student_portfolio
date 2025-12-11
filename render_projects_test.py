from types import SimpleNamespace
from app import app
from flask import render_template

with app.test_request_context('/'):
    fake_user = SimpleNamespace(username='Tester', course='CS', profile_picture=None, bio=None, id=1)
    try:
        out = render_template('projects.html', projects=[], current_user=fake_user)
        print(out.splitlines()[0:40])
        print('\n--- RENDER OK ---')
    except Exception as e:
        import traceback
        traceback.print_exc()
