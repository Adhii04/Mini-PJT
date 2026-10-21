import os
import sys
import importlib.util

current_dir = os.path.dirname(os.path.abspath(__file__))
sub_dir = os.path.join(current_dir, 'Intern_task-1')
if sub_dir not in sys.path:
    sys.path.insert(0, sub_dir)

os.chdir(sub_dir)

target_file = os.path.join(sub_dir, 'app.py')
spec = importlib.util.spec_from_file_location("nexus_app_module", target_file)
mod = importlib.util.module_from_spec(spec)
sys.modules["nexus_app_module"] = mod
spec.loader.exec_module(mod)

app = mod.app

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
