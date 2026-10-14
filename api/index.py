import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
sub_dir = os.path.abspath(os.path.join(current_dir, '..', 'Intern_task-1'))

if sub_dir not in sys.path:
    sys.path.insert(0, sub_dir)

os.chdir(sub_dir)

from app import app
