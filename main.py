from utils import THUer

print('input your username')
un = input()
print('input your password')
pw = input()
u = THUer(un, pw)
print('======download all files demo======')
u.getallfiledownload()
