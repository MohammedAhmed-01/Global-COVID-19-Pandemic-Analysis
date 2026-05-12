import sys
sys.path.insert(0, 'DashBoard')

from app.callbacks.dashboard_callbacks import _ensure_continents_list

print('✓ Helper function imported successfully!')
print(f'Test 1 (list): {_ensure_continents_list(["Asia", "Europe"])}')
print(f'Test 2 (string): {_ensure_continents_list("Asia")}')
print(f'Test 3 (None): {_ensure_continents_list(None)}')
print(f'Test 4 (empty list): {_ensure_continents_list([])}')
print('✓ All tests passed!')
