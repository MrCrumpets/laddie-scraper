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
    print text
    normal_log.write(text + "\n")
    normal_log.flush()

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

def parse_class(data):
    try:
        crn = data[1]
        sec_id = data[2]
        sec_type = data[3]
        cr_hrs = data[4]
        tuit_code = data[5]
        tuit_bhrs = data[6]
        i = 8;
        days = time_start = time_end = location = None
        if data[8] != 'C/D' and data[13] != 'C/D':
            days = "".join(data[7:12])
            time_start = data[13].split("-")[0]
            time_end = data[13].split("-")[1]
            location = data[14]
            i = 14;
        
        enrol_max = data[i + 1]
        enrol_cur = data[i + 2]
        enrol_avail = data[i + 3]
        enrol_wtlst = data[i + 4]
        enrol_percent = data[i + 5]
        xlist_max = data[i + 6]
        xlist_cur = data[i + 7]
        
        log("CRN: " + crn)
        log("Days: " + days)
        
        if xlist_max == '':
            xlist_max = None
            xlist_cur = None

        instructor = data[i + 8]

        values = (crn, course_id, sec_id, sec_type, cr_hrs, tuit_code, tuit_bhrs, days,
                time_start, time_end, location, enrol_max, enrol_cur, enrol_avail, enrol_wtlst,
                enrol_percent, xlist_max, xlist_cur, instructor)
        # c.execute('INSERT INTO CLASSES VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', values)
    except (IndexError):
        # error_log.write("Row failed: %s\n" % data)
        print "Row failed"
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
        data = map(parse_string, row.findAll('td'))
        data = list(data)
        if data[0] == 'NOTE':
            continue
        if len(data) == 2: # Row is a new course heading 
            log("New Course:")
            course_id = parse_course(data)
        elif course_id != None:            
            log("New Class")
            parse_class(data)

    return len(rows)

if __name__ == "__main__":
    abspath = os.path.abspath(__file__)
    os.chdir(os.path.dirname(abspath))
    conn = sqlite3.connect("../courses.db")
    c = init_db(conn) 
    f = open('util/courses') # List of faculties and their names (CSCI, MATH, etc.)
    subjects = f.read().split("\n")[:-1]
    for subject in subjects[0:1]:
        subj = subject.split(" ")[0]
        download_subject(subj)
    print "Scraping completed."
    conn.commit()
    conn.close()
