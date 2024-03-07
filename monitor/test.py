import http.client

conn = http.client.HTTPSConnection("app.icproject.com")
conn.request("POST", "/", '{"test": "event"}', {"Content-Type": "application/json"})

print(conn.getresponse().read().decode("utf-8"))
