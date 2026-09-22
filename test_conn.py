import psycopg2
conn = psycopg2.connect(host='postgres', port=5432, dbname='infrapilot', user='postgres', password='postgrespassword')
print('Container-to-Postgres OK, version:', conn.server_version)
conn.close()
