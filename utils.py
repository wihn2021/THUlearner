import requests
import json
import re
import os
import time

idlogin = 'https://id.tsinghua.edu.cn/do/off/ui/auth/login/post/bb5df85216504820be7bba2b0ae1535b/0?/login.do'
learnlogin = 'https://learn.tsinghua.edu.cn/f/loginAccountSave'
jspringsecurity = 'https://learn.tsinghua.edu.cn/b/j_spring_security_thauth_roaming_entry?ticket=%s'
getCurrentAndNextSemester = 'https://learn.tsinghua.edu.cn/b/kc/zhjw_v_code_xnxq/getCurrentAndNextSemester?_csrf=%s'
loadCourseBySemesterId = 'https://learn.tsinghua.edu.cn/b/wlxt/kc/v_wlkc_xs_xkb_kcb_extend/student/loadCourseBySemesterId/%s?timestamp=%s&_csrf=%s'
downloadfileurl = 'https://learn.tsinghua.edu.cn/b/wlxt/kj/wlkc_kjxxb/student/downloadFile?sfgk=0&_csrf=%s&wjid=%s'
getfileinfourl = 'https://learn.tsinghua.edu.cn/b/wlxt/kj/wlkc_kjxxb/student/kjxxbByWlkcidAndSizeForStudent?wlkcid=%s&size=50&_csrf=%s'
homeworkunhandled = 'https://learn.tsinghua.edu.cn/b/wlxt/kczy/zy/student/zyListWj?_csrf=%s&_csrf=%s'
unspecifieddata = 'aoData=[{"name":"sEcho","value":1},{"name":"iColumns","value":8},{"name":"sColumns","value":",,,,,,,"},{"name":"iDisplayStart","value":0},{"name":"iDisplayLength","value":"30"},{"name":"mDataProp_0","value":"wz"},{"name":"bSortable_0","value":false},{"name":"mDataProp_1","value":"bt"},{"name":"bSortable_1","value":true},{"name":"mDataProp_2","value":"mxdxmc"},{"name":"bSortable_2","value":true},{"name":"mDataProp_3","value":"zywcfs"},{"name":"bSortable_3","value":true},{"name":"mDataProp_4","value":"kssj"},{"name":"bSortable_4","value":true},{"name":"mDataProp_5","value":"jzsj"},{"name":"bSortable_5","value":true},{"name":"mDataProp_6","value":"jzsj"},{"name":"bSortable_6","value":true},{"name":"mDataProp_7","value":"function"},{"name":"bSortable_7","value":false},{"name":"iSortCol_0","value":5},{"name":"sSortDir_0","value":"desc"},{"name":"iSortCol_1","value":6},{"name":"sSortDir_1","value":"desc"},{"name":"iSortingCols","value":2},{"name":"wlkcid","value":"%s"}]'


class THUer(object):
    def __init__(self, username, password):
        super(THUer, self).__init__()
        self.secret = {'i_user': username, 'i_pass': password}
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
        self.cookie['XSRF-TOKEN'] = re.search(
            '^XSRF-TOKEN=([^;]*)', setcoo).group(1)
        self.cookie['JSESSIONID'] = re.search(
            'JSESSIONID=([^;]*)', setcoo).group(1)
        self.cookie['serverid'] = re.search(
            'serverid=([^;]*)', setcoo).group(1)

        # login id.tsinghua.edu.cn & get ticket
        idloginres = requests.post(idlogin, data=self.secret)
        url_with_ticket = re.search(
            '<a href="(.*)">', idloginres.text).group(1)
        p2 = requests.get(url_with_ticket, cookies=self.cookie)
        self.ticket = re.search('ticket=(.*)', url_with_ticket).group(1)

        # jspring_security sign and then we get the index html!!!
        js = requests.get(jspringsecurity %
                          (self.ticket,), cookies=self.cookie)
        self.getcourses()

    def getcourses(self):
        self.courselist = []
        self.semester = \
            eval(requests.get(getCurrentAndNextSemester % (self.cookie['XSRF-TOKEN'],), cookies=self.cookie).text)[
                'result']['id']
        coursetemp = json.loads(
            requests.get(loadCourseBySemesterId % (self.semester, str(int(time.time())), self.cookie['XSRF-TOKEN']),
                         cookies=self.cookie).text)
        for _ in coursetemp['resultList']:
            self.courselist.append(course(_['kcm'], _['wlkcid'], self))

    def getallfiledownload(self):
        for c in self.courselist:
            c.downloadmyfiles()


class course(object):
    def __init__(self, kcm, wlkcid, parent: THUer):
        super(course, self).__init__()
        self.name = kcm
        self.id = wlkcid
        self.parent = parent
        self.filelist = []
        if not os.path.exists(self.name):
            os.mkdir(self.name)
        self.getmyfiles()
        self.homeworklist = []
        self.getmyhws()

    def getmyfiles(self):
        fltmp = json.loads(requests.get(getfileinfourl % (self.id, self.parent.cookie['XSRF-TOKEN']),
                                        cookies=self.parent.cookie).text)['object']
        for _ in fltmp:
            self.filelist.append(onlinefile(
                _['wjid'], _['bt'], _['wjlx'], self))

    def downloadmyfiles(self):
        for _ in self.filelist:
            _.download(self.name)

    def getmyhws(self):
        self.homeworklist=[]
        head = {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'X-Requested-With': 'XMLHttpRequest', 'X-XSRF-TOKEN': self.parent.cookie['XSRF-TOKEN']}
        resp = requests.post(homeworkunhandled % (self.parent.cookie['XSRF-TOKEN'], self.parent.cookie['XSRF-TOKEN']),
                             cookies=self.parent.cookie, data=unspecifieddata % (self.id,), headers=head).text
        hwtemp = json.loads(resp)['object']['aaData']
        for _ in hwtemp:
            self.homeworklist.append(
                homework(_['xszyid'], _['bt'], _['zyid'], _['jzsj'], self))


class onlinefile(object):
    def __init__(self, wjid, bt, wjlx, parent: course, downloaded=False):
        super(onlinefile, self).__init__()
        self.wjid = wjid
        self.bt = bt
        self.wjlx = wjlx
        self.parent = parent
        self.downloaded = downloaded

    def download(self, path):
        downloadfile(self, self.parent.parent.cookie, path)


def downloadfile(fileobject: onlinefile, cookie, path, check=True):
    print(
        'download %s to %s from %s' % (fileobject.bt, path, downloadfileurl % (cookie['XSRF-TOKEN'], fileobject.wjid)))
    fname = './' + path + '/' + fileobject.bt + '.' + fileobject.wjlx
    if check:
        if os.path.exists(fname):
            print('already completed')
            return
    resp = requests.get(downloadfileurl % (
        cookie['XSRF-TOKEN'], fileobject.wjid), cookies=cookie)
    if not os.path.exists(path):
        os.makedirs(path)
    with open(fname, 'wb') as f:
        f.write(resp.content)


class homework(object):
    def __init__(self, xszyid, bt, zyid, jzsj, parent: course, handled=False):
        super(homework, self).__init__()
        self.xszyid = xszyid
        self.bt = bt
        self.zyid = zyid
        self.jzsj = jzsj
        self.parent = parent
        self.handled = handled

    def __str__(self) -> str:
        return '%s %s %s %s' % (self.bt, self.zyid, self.jzsj, self.handled)

    def handinafile(path:str,zyid):
        pass
