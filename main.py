from bs4 import BeautifulSoup
import yaml
import requests
import smtplib, ssl
from loguru import logger
import os
from email.mime.text import MIMEText
from email.header import Header

logger.add("info.log", level="TRACE", rotation="1 week")

url = "http://ico.tju.edu.cn/xwzx/xmxx/xsjwjlxm/index.html"
base = "http://ico.tju.edu.cn/xwzx/xmxx/xsjwjlxm"

filename = "saver.md"

with open('config.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

account = config['account']
password = config['password']
smtp_server = config['smtp_server']
receiver = config['receiver']

assert len(account) == 0 or len(password) == 0 or len(smtp_server) == 0 or len(receiver) == 0, f"config.yaml Error"
    

def send_mail(account, password, receiver, msg):
    """
        Send Mail when new notices are posted

    Args:
        account (): 
        password (): 
        receiver (): 
        msg (): 

    Returns: 0 for success , 1 for failed
    """
    global smtp_server
    # Try to log in to server and send email
    try:
        server = smtplib.SMTP(smtp_server)
        server.login(account, password)
        logger.debug("Loggin Complete")
        title = msg[msg.find('] ')+2:msg.rfind('(')-1]
        url  = msg[msg.rfind('(')+1:msg.rfind(')')]
 
        html = requests.get(url)
        html.encoding='GBK'
    
        message = MIMEText(f'{msg}\n{html.text}', 'plain', 'utf-8')
        message['From'] = Header("天大留学交流内容自动更新", 'utf-8')   # 发送者
        message['To'] =  Header("刘锦帆", 'utf-8')        # 接收者
        subject = f'!!{title}'
        message['Subject'] = Header(subject, 'utf-8')
        server.sendmail(account, receiver, message.as_string())

    except Exception as e:
        # Print any error messages to stdout
        logger.error(e)
        return 1
    finally:
        server.quit() 
    return 0 


def get_first_page():
    global url, base
    """
    默认只访问第一页
    若新增项目数量大于或等于 21 个
    则递归访问下一页

    Returns: A List of Project Items
        - Each in Markdown URL Format:
            `[[PublicDate] Title](URL)`
    """
    html = requests.get(url)
    html.encoding='GBK'
    
    bs = BeautifulSoup(html.text, 'lxml')
    
    bs = bs.find('ul',{"class":"text_list3"})
    lists = bs.find_all('li')
    
    ret = []

    for i in lists:
        date = i.find('span').text
        a = i.find('a')
        tmp = a['href']
        tmp = tmp[tmp.find('.')+1:]
        url = f"{base}{tmp}"
        title = a['title']
        saver = f"* [{date} {title}]({url})\n"
        ret.append(saver)

    return ret


def get_saved_content():
    with open(filename, "r") as f:
        content = f.readlines()
    return content


if __name__ == "__main__":
    if os.path.exists(filename):
        logger.debug(f"{filename} Exists")
        saved = get_saved_content()
        ret = get_first_page()
        for i in ret:
            if i in saved:
                # logger.info(f"{i} is saved")
                pass
            else:
                logger.debug(f"{i} NOT SAVED")
                # Send Email 
                if send_mail(account, password, receiver, i):
                    logger.error("Send Email Error")
                else:
                    logger.debug("Send Email Success")
                    with open(filename, 'a') as f:
                        f.write(i)
    else:
        """ First Time """
        ret = get_first_page()
        with open(filename, 'w') as f:
            for i in ret:
                f.write(i)
        logger.debug(f"Save ret to {filename}")

