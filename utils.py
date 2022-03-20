import requests
import bs4
import json
import re
import time
import os

idlogin = 'https://id.tsinghua.edu.cn/do/off/ui/auth/login/post/bb5df85216504820be7bba2b0ae1535b/0?/login.do'
learnlogin = 'https://learn.tsinghua.edu.cn/f/loginAccountSave'
jspringsecurity = 'https://learn.tsinghua.edu.cn/b/j_spring_security_thauth_roaming_entry?ticket=%s'
getCurrentAndNextSemester = 'https://learn.tsinghua.edu.cn/b/kc/zhjw_v_code_xnxq/getCurrentAndNextSemester?_csrf=%s'
loadCourseBySemesterId = 'https://learn.tsinghua.edu.cn/b/wlxt/kc/v_wlkc_xs_xkb_kcb_extend/student/loadCourseBySemesterId/%s?timestamp=%s&_csrf=%s'
downloadfileurl = 'https://learn.tsinghua.edu.cn/b/wlxt/kj/wlkc_kjxxb/student/downloadFile?sfgk=0&_csrf=%s&wjid=%s'
getfileinfourl = 'https://learn.tsinghua.edu.cn/b/wlxt/kj/wlkc_kjxxb/student/kjxxbByWlkcidAndSizeForStudent?wlkcid=%s&size=5&_csrf=%s'


class course(object):
    def __init__(self, kcm, wlkcid):
        super(course, self).__init__()
        self.name = kcm
        self.id = wlkcid


class THUer(object):
    def __init__(self, username, password):
        super(THUer, self).__init__()
        self.secret = {}
        self.secret['i_user'] = username
        self.secret['i_pass'] = password
        self.cookie = {}
        self.ticket = ''
        self.semester = ''
        self.courselist = []
        self.login()

    def login(self):
        # login & get cookie | important
        h1 = {"mimeType": "application/x-www-form-urlencoded; charset=UTF-8",
              "text": "loginAccount=" + self.secret['i_user']}
        p1 = requests.post(learnlogin, data=h1)
        setcoo = p1.headers['set-cookie']
        self.cookie['XSRF-TOKEN'] = re.search('^XSRF-TOKEN=([^;]*)', setcoo).group(1)
        self.cookie['JSESSIONID'] = re.search('JSESSIONID=([^;]*)', setcoo).group(1)
        self.cookie['serverid'] = re.search('serverid=([^;]*)', setcoo).group(1)

        # login id.tsinghua.edu.cn & get ticket
        idloginres = requests.post(idlogin, data=self.secret)
        ana_idlogin = bs4.BeautifulSoup(idloginres.text, features='lxml')
        url_with_ticket = ana_idlogin.a['href']
        p2 = requests.get(url_with_ticket, cookies=self.cookie)
        self.ticket = re.search('ticket=(.*)', url_with_ticket).group(1)

        # jspring_security sign and then we get the index html!!!
        js = requests.get(jspringsecurity % (self.ticket,), cookies=self.cookie)

    def getcourses(self):
        self.semester = \
        eval(requests.get(getCurrentAndNextSemester % (self.cookie['XSRF-TOKEN'],), cookies=self.cookie).text)[
            'result']['id']
        coursetemp = json.loads(
            requests.get(loadCourseBySemesterId % (self.semester, str(int(time.time())), self.cookie['XSRF-TOKEN']),
                         cookies=self.cookie).text)
        self.courselist = coursetemp['resultList']

    def getcoursefileinfo(self, wlkcid):
        try:
            filelist = \
            json.loads(requests.get(getfileinfourl % (wlkcid, self.cookie['XSRF-TOKEN']), cookies=self.cookie).text)[
                'object']
            return filelist
        except:
            print(requests.get(getfileinfourl % (wlkcid, self.cookie['XSRF-TOKEN'])).text)

    def getonecoursefiledownload(self, kcid, path=''):
        flist = self.getcoursefileinfo(kcid)
        for _ in flist:
            self.downloadfilebyid(_['wjid'], path + _['bt'] + '.' + _['wjlx'])

    def getallfiledownload(self):
        for c in self.courselist:
            if not os.path.exists(c['kcm']):
                os.mkdir(c['kcm'])
            self.getonecoursefiledownload(c['wlkcid'], (c['kcm'] + '/'))

    def downloadfilebyid(self, wjid, path='undefined.pdf'):
        resp = requests.get(downloadfileurl % (self.cookie['XSRF-TOKEN'], wjid), cookies=self.cookie)
        with open(path, 'wb') as f:
            f.write(resp.content)
