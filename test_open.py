import os, sqlite3
p = os.path.join(os.getcwd(), 'instance', 'warranty_system.db')
print('path', p)
print('exists', os.path.exists(p))
try:
    conn = sqlite3.connect(p)
    print('opened')
    conn.close()
except Exception as e:
    print('error', e)
