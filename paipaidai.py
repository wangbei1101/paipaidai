# coding=utf-8
import urllib
import urllib2
import cookielib
import json
import time
import re
from bs4 import BeautifulSoup

__author__ = 'wangbei01'

ISOTIMEFORMAT='%Y-%m-%d %X'
__filename = 'cookie.txt'
# 声明一个MozillaCookieJar对象实例来保存cookie，之后写入文件
__cookie = cookielib.MozillaCookieJar(__filename)
__opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(__cookie))

__login_url = 'https://ac.ppdai.com/User/Login'
__login_data = urllib.urlencode(
    {"IsAsync": "true", "Redirect": "", "UserName": "18510917075", "Password": "yourPassword",
     "ValidateCode": "2684", "RememberMe": "false"})

__lending_list_url = 'http://invdebt.ppdai.com/buy/list?monthGroup=3%2C&rate=16&levelCategory=2&sortType=&levels=%2CB%2CC%2C&lastDueDays=&isShowMore=true&minAmount=30&maxAmount=90&minPastDueDay=&maxPastDueDay=&minPastDueNumber=&maxPastDueNumber=&special='
__lending_data = urllib.urlencode({"levelCategory": "2", "levels": ",A,B,", "special": "", "lastDueDays": "",
                                   "monthGroup": "", "rate": "16", "minAmount": "30", "maxAmount": "80", "sortType": "",
                                   "minPastDueNumber": "", "maxPastDueNumber": "", "isShowMore": "true",
                                   "pageIndex": "1"})

# 债权原始等级
__credit_code = ['AA', 'A', 'B', 'C']
# 债权当前等级
__current_credit_code = ['AA', 'A', 'B', 'C']
# 投资url
__invest_url = 'http://invdebt.ppdai.com/buy/buyDebt'


def login(url, data):
    res = __opener.open(url, data)
    # 保存cookie到cookie.txt中
    __cookie.save(ignore_discard=True, ignore_expires=True)
    if res.getcode() == 200:
        print('login request success!')
        resText = res.read()
        print(resText)
        result = json.loads(resText)
        if result['Code'] == 1:
            print('login sucess')
            return True
        else:
            print ('login error')
            return False
    else:
        print('login request failed!')
        return False

def getTotalPage():
    res = __opener.open(__lending_list_url)
    if res.getcode() == 200:
        resText = res.read()
        soup = BeautifulSoup(resText, "lxml")
        totalPage = re.findall("\d+",soup.select('span.pagerstatus')[0].string)[0]
        return int(totalPage)

def buyList(page):
    res = __opener.open(__lending_list_url + '&pageIndex=' + str(page))
    if res.getcode() == 200:
        resText = res.read()
        # print(resText)
        # print('-------------------------------------------------------------------------------------------')
        soup = BeautifulSoup(resText, "lxml")
        lis = soup.select('div.outerBorrowList li')
        result = []
        for index, li in enumerate(lis):
            # print str(index)
            # print(li)
            if index % 2 == 0:
                tag = {}
                creditcode = li.div['creditcode']
                currentcreditcode = li.div['currentcreditcode']
                debtdealid = li.div['debtdealid']
                interest = li.select('div.originalinterest')[0].string

                tag['creditcode'] = creditcode
                tag['currentcreditcode'] = currentcreditcode
                tag['debtdealid'] = debtdealid
                tag['interest'] = interest.strip().replace('\n', '').replace(' ', '')[:-1]
            else:
                originalinterest = li.select('p.fc_orange')[0].string
                amount = li.find_all('p', class_="detail")[2].string
                rateAmount = li.find_all('p', class_="detail")[3].string
                discount = li.find_all('p', class_="detail")[5].string
                overdueTime = li.find_all('p', class_="detail")[6].string

                tag['originalinterest'] = originalinterest.strip()[:-1]
                tag['amount'] = amount.strip()[1:]
                tag['rateAmount'] = rateAmount.strip()[1:]
                tag['discount'] = discount.strip()[:-1]
                tag['overdueTime'] = overdueTime.strip()[:-1]
                result.append(tag)
        # sorted(result.items(), lambda x, y: cmp(x[1], y[1]))
        return result
    else:
        print('request buyList failed!')


def invest(invest_post_url, lending):
    post_data = urllib.urlencode({"preferencedegree": "-1", "debtDealId": lending['debtdealid']})
    res = __opener.open(invest_post_url, post_data)
    if res.getcode() == 200:
        res_text = res.read()
        # print(res_text)
        result = json.loads(res_text)
        if result['Code'] == 1:
            print(lending)
            print(time.strftime(ISOTIMEFORMAT, time.localtime()) + 'invest sucess!')
        elif result['Code'] == 2:
            print result['Message']
            print time.strftime(ISOTIMEFORMAT, time.localtime()) + '线程睡眠30分钟'
            # 休眠30分钟
            time.sleep(60 * 30)
        else:
            print (time.strftime(ISOTIMEFORMAT, time.localtime()) + 'invest failed!')
    else:
        print('invest request failed!')


if __name__ == '__main__':
    loginResult = login(__login_url, __login_data)
    if loginResult:
        while True:
            try:
                # 休眠3秒
                time.sleep(3)
                totalPage = getTotalPage()
                for page in range(1, totalPage + 1):
                    list = buyList(page)
                    # print('查询到的所有标如下------------------------------------------------------------------->>>')
                    # print list
                    # print('                 -------------------------------------------------------------------<<<')
                    for lending in list:
                        if lending['creditcode'] in __credit_code and lending[
                            'currentcreditcode'] in __current_credit_code and float(lending['amount']) < 100 and float(
                            lending['overdueTime']) == 0 and float(
                            lending['discount']) < -10:
                            invest(__invest_url, lending)
            except Exception, e:
                print "[Error]: ", e
