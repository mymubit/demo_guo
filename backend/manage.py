import os
import sys
import django
from pathlib import Path

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from config.windows_compat import apply as _apply_windows_compat
from config.windows_compat import apply_after_django_setup as _apply_windows_compat_post

_apply_windows_compat()

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
_apply_windows_compat_post()

if __name__ == '__main__':
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
