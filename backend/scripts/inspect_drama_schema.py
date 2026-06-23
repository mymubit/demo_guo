import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.db import connection

with connection.cursor() as c:
    c.execute(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_name='drama_role_execution' ORDER BY 1"
    )
    print("drama_role_execution:", [r[0] for r in c.fetchall()])
    c.execute("SELECT to_regclass('drama_project')")
    print("drama_project table:", c.fetchone()[0])
