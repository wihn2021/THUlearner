import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
import base64


class mailposter(object):
    def __init__(self, host, user, pasw):
        super(mailposter, self).__init__()
        self.host = host
        self.user = user
        self.pasw = pasw
        self.sender = 'auto-send-files'
        self.receiver = ['xxxxx']

    def sendafile(self, path):
        msg = MIMEMultipart()
        msg['From'] = Header(self.sender, 'utf-8')
        msg['To'] = Header("you", 'utf-8')
        msg['Subject'] = Header(self.sender, 'utf-8')
        att1 = MIMEText(open(path, 'rb').read(), 'base64', 'utf-8')
        att1["Content-Type"] = 'application/octet-stream'
        att1["Content-Disposition"] = 'attachment; filename="%s"' % (path,)
        msg.attach(att1)
        try:
            smtpObj = smtplib.SMTP()
            smtpObj.connect(self.host, 25)  # 25 为 SMTP 端口号
            smtpObj.login(self.user, self.pasw)
            smtpObj.sendmail(self.sender, self.receiver, msg.as_string())
            print("邮件发送成功")
        except smtplib.SMTPException:
            print("Error: 无法发送邮件")
