import sqlite3
import re

conn = sqlite3.connect("courses.db")
c = conn.cursor()

f = open('dump')
text = f.read().split('\n')
for row in text:
    print(re.findall("\".*\"", row)[0].replace("\"", ""), (re.sub("<.*>", "", row)))
c.close()
