from bs4 import BeautifulSoup
import os
import requests
import sqlite3
from time import sleep
normal_log = open('normal.log', 'w')
error_log = open('error.log', 'w')

def connect_db(database):
    return sqlite3.connect(database)

def init_db(db): 
    f = open('schema.sql') 
    db.cursor().executescript(f.read())
    return db.cursor()
    
def parse_string(el):
    text = ''.join(el.findAll(text=True))
    return text.strip()

def log(text):
    # print text
    # normal_log.write(text.encode('ascii', 'ignore') + u"\n")
    # normal_log.flush()
    pass

def log_el(el):
    log(el.text.encode('utf-8').strip())

def get_description(subj, id):
    url = "http://www.registrar.dal.ca/calendar/class.php?subj=%s&num=%s" % (subj, id.replace("X", "").replace("Y", ""))
    r = requests.get(url)
    soup = BeautifulSoup(r.text)
    description = soup.find("div", {'class', 'content'})
    if description == None:
        return None
    return description.text

def download_subject(subj):
    normal_log.write(subj + "\n")
    rows_read = 1
    n = 1 #number to load at a time
    while rows_read > 0:
        url = "https://dalonline.dal.ca/PROD/fysktime.P_DisplaySchedule?s_term=201410,201420&s_crn=&s_subj=%s&s_numb=&n=%i&s_district=100" % (subj, n)
        normal_log.write("URL: %s \n" % (url))
        normal_log.flush();
        rows_read = scrape_url(url, subj)
        n = n + 20

def parse_course(data):
    d = data[0].split(" ")
    id = d[1]
    subj = d[0]
    title = " ".join(d[2:]).replace('\n', '')
    description = get_description(subj, id)
    semester = data[1].split("\n")[0]
    values = (None, id, subj, title, description, semester)
    c.execute('INSERT INTO COURSES VALUES (?,?,?,?,?,?)', values)
    course_id = c.lastrowid
    log("ID: " + id)
    log("Title: " + title)
    return course_id

def parse_class(course_id, data, row):
    td_elements = list(map(lambda td: td.findAll(text=True), row.findAll('td')))
    # print td_elements[6:11]
    try:
        crn = data[1]
        sec_id = data[2]
        sec_type = data[3]
        cr_hrs = data[4]
        tuit_code = data[5]
        tuit_bhrs = data[6]
        skip = 6 # The number of columns to skip to the next block
        days = location = times = ""

        if data[6] == 'C/D':
            skip = 0
        elif data[11] == 'C/D':
            skip = 6
        else:
            # HOLY LIST COMPREHENSIONS BATMAN. This is a terrible piece of code. It collects the different days and times from the td's
            # and merges them.
            times = '|'.join([' '.join([td[i] for td in td_elements[6:12]]).encode('ascii', 'ignore') for i in range(len(td_elements[6]))])
            location = data[12]
        # Enrollment Info
        instructor = data[14 + skip].split("\n")[0]
        tuit_code = data[15 + skip]
        tuit_bhrs = data[16 + skip]
        log("CRN: " + crn) 
        log("Instructor: '" + instructor + "'")

        values = (crn, course_id, sec_id, sec_type, cr_hrs, tuit_code, tuit_bhrs, 
            times, location, instructor)
        c.execute('INSERT INTO CLASSES VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', values)
    except IndexError as e:
        error_log.write("Row failed: %s\n" % data)
        print "Row failed", e
        error_log.flush()

def scrape_url(url, subject):
    r = requests.get(url)
    s = r.text
    soup = BeautifulSoup(s)
    tables = soup.findAll("table", {'class', 'dataentrytable'})
    datatable = tables[1]
    # Get a list of all the <tr>s in the table, skip the header row
    rows = datatable.find_all('tr')[2:]
    print subject, len(rows)
    if len(rows) == 0:
        return 0
    course_id = None
    for row in rows:
        # Get all the text from the <td>s
        data = list(map(parse_string, row.findAll('td')))
        if data[0] == 'NOTE':
            continue
        if len(data) == 2: # Row is a new course heading 
            log("New Course:")
            course_id = parse_course(data)
        elif course_id != None:            
            log("New Class:")
            parse_class(course_id, data, row)

    return len(rows)

if __name__ == "__main__":
    abspath = os.path.abspath(__file__)
    os.chdir(os.path.dirname(abspath))
    conn = sqlite3.connect("../courses.db")
    c = init_db(conn) 
    f = open('util/courses') # List of faculties and their names (CSCI, MATH, etc.)
    subjects = f.read().split("\n")[:-1]
    for subject in subjects:
        subj = subject.split(" ")[0]
        download_subject(subj)
    print "Scraping completed."
    conn.commit()
    conn.close()
