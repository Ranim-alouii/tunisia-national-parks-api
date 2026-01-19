import sqlite3

db_path = 'tunisia_parks.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check rarity values
cursor.execute('SELECT DISTINCT rarity FROM species WHERE rarity IS NOT NULL')
rarity_values = cursor.fetchall()

# Check conservation_status values
cursor.execute('SELECT DISTINCT conservation_status FROM species WHERE conservation_status IS NOT NULL')
conservation_values = cursor.fetchall()

print('Rarity values:')
for val in rarity_values:
    print(f'  "{val[0]}"')

print('Conservation status values:')
for val in conservation_values:
    print(f'  "{val[0]}"')

conn.close()
