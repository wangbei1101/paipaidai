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

__loan_list_url = 'http://invest.ppdai.com/loan/listnew?LoanCategoryId=4&CreditCodes=3%2C4%2C5%2C&ListTypes=&Rates=&Months=&AuthInfo=4%2C&BorrowCount=&didibid=&SortType=0&MinAmount=0&MaxAmount=0'
__loan_data = urllib.urlencode({"levelCategory": "2", "levels": ",A,B,",})

# 债权原始等级
__credit_code = ['AA', 'A', 'B']

# 投资url
__invest_url = 'http://invest.ppdai.com/Bid/Bid'


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
    res = __opener.open(__loan_list_url)
    if res.getcode() == 200:
        resText = res.read()
        soup = BeautifulSoup(resText, "lxml")
        totalPage = 1
        if len(soup.select('span.pagerstatus')) > 0:
            totalPage = re.findall("\d+", soup.select('span.pagerstatus')[0].string)[0]
        return int(totalPage)

def getLoanUrlList():
    res = __opener.open(__loan_list_url)
    if res.getcode() == 200:
        resText = res.read()
        # print(resText)
        # print('-------------------------------------------------------------------------------------------')
        soup = BeautifulSoup(resText, "lxml")
        loan_url_tag_list = soup.find_all(href=re.compile("info\?id="))
        result = []
        for loan_url_tag in loan_url_tag_list:
            # print loan_url_tag['href']
            result.append(loan_url_tag['href'])
        return result
    else:
        print('get loan url list failed!')

def getLoan(url):
    res = __opener.open(url)
    if res.getcode() == 200:
        resText = res.read()
        # print(resText)
        # print('-------------------------------------------------------------------------------------------')
        soup = BeautifulSoup(resText, "lxml")
        loan = {}
        loan['loan_id'] = url.split('id=')[1]
        money_left = soup.select("div.newLendDetailMoneyLeft dd")
        if len(money_left) == 3:
            #借款金额
            loan['amount'] = re.sub("\D", "", money_left[0].text)
            #年利率（%）
            loan['rate'] = re.findall("\d+", money_left[1].text)[0]
            #期限
            loan['term'] = re.findall("\d+", money_left[2].text)[0]
        #投标进度
        process = soup.find_all(id='process')
        loan['process'] = re.findall("\d+", process[0]['style'])[0]

        tab_contain = soup.select("div.tab-contain")

        flex = tab_contain[2].select(".flex span")
        #成功借款次数
        loan['borrow_times'] = re.sub("\D", "", flex[0].text)
        #成功还款次数
        loan['repay_times'] = re.sub("\D", "", flex[3].text)
        #正常还清次数
        loan['normal_repay_times'] = re.sub("\D", "", flex[4].text)
        #累计借款金额
        loan['accumulated_borrow_amount'] = flex[7].text.replace('\n', '').replace(',', '')[1:]
        #待还金额
        loan['still_borrow_amount'] = re.findall(r'-?\d+\.?\d*e?-?\d*?', flex[8].text)[0]
        #单笔最高借款金额
        loan['max_borrow_amount'] = flex[10].text.replace('\n', '').replace(',', '')[1:]
        # print loan
        return loan
    else:
        print('get loan failed!')


def invest(loan):
    post_data = urllib.urlencode({"Reason": "", "Amount": "50", "ListingId": loan['loan_id'], "UrlReferrer": "1", "SubListType": "0"})
    res = __opener.open(__invest_url, post_data)
    if res.getcode() == 200:
        res_text = res.read()
        # print(res_text)
        result = json.loads(res_text)
        if result['Code'] == 1:
            print(loan)
            print(time.strftime(ISOTIMEFORMAT, time.localtime()) + ' invest sucess!')
        elif result['Message'] == u"您的账户余额不够，请先充值！":
            print str(result['Code']) + result['Message']
            print time.strftime(ISOTIMEFORMAT, time.localtime()) + ' 线程睡眠30分钟'
            # 休眠30分钟
            time.sleep(60 * 30)
        else:
            print str(result['Code']) + result['Message']
            print (time.strftime(ISOTIMEFORMAT, time.localtime()) + ' invest failed!')
    else:
        print('invest request failed!')


if __name__ == '__main__':
    loginResult = login(__login_url, __login_data)
    if loginResult:
        loan_ids = []
        while True:
            try:
                # 休眠3秒
                time.sleep(3)
                loan_url_list = getLoanUrlList()
                for loan_url in loan_url_list[::-1]:
                    l = {}
                    l['loan_id'] = loan_url.split('id=')[1]
                    if l['loan_id'] not in loan_ids:
                        # invest(l)
                        # loan_ids.append(l['loan_id'])
                        # if len(loan_ids) == 100:
                        #     loan_ids = []
                        # 来不及分析标的详情，只能是拿到标的就投
                        loan = getLoan(loan_url)
                        if float(loan['amount']) < 30000 and loan['repay_times'] == loan['normal_repay_times'] and float(loan['still_borrow_amount']) < 10000:
                        # if loan['repay_times'] == loan['normal_repay_times']:
                            invest(loan)
                            loan_ids.append(loan['loan_id'])
                            if len(loan_ids) == 100:
                                loan_ids = []
            except Exception, e:
                print "[Error]: ", e
