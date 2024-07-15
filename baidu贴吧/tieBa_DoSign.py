import requests, re, json, os, sys, urllib.parse, time, threading
from datetime import datetime
from lxml import etree

# 获取当前文件的目录
current_dir = os.path.dirname(os.path.abspath(__file__))
# 获取项目根目录
project_root = os.path.dirname(current_dir)
# 将项目根目录添加到 sys.path
sys.path.append(project_root)
from utils import email_sender


def get_count():
    timestamp_with_microseconds = int(datetime.now().timestamp() * 1000)
    params = {'v': str(timestamp_with_microseconds)}
    response = requests.get('https://tieba.baidu.com/f/like/mylike', params=params, cookies=cookies, headers=headers)
    tree = etree.HTML(response.text)
    time.sleep(1)
    tree_list = tree.xpath('//div[@class="forum_table"]/table/tr')
    count = len(tree_list) - 1
    name_list = [tree_list[i].xpath('./td[1]/a/text()')[0] for i in range(1, count + 1)]
    return name_list


def sign_thread(name, results, lock):
    message = ''
    try:
        url_name = urllib.parse.quote(name)
        url = f'https://tieba.baidu.com/f?ie=utf-8&kw={url_name}&fr=search'
        response = requests.get(url)
        tree = etree.HTML(response.text)
        time.sleep(1)
        tbs = tree.xpath('/html/head/script[1]')[0].text
        tbs_data = re.search(r'var PageData = ({.*?});', tbs, re.DOTALL)
        if tbs_data:
            cleaned_json = tbs_data.group(1).replace("'", '"')
            page_data_dict = json.loads(cleaned_json)
            tbs_value = page_data_dict['tbs']

        data = {'ie': 'utf-8', 'kw': name, 'tbs': tbs_value}
        response = requests.post('https://tieba.baidu.com/sign/add', cookies=cookies, headers=headers, data=data)
        json_data = json.loads(response.text)
        if json_data["no"] == 0:
            message = f'{name}吧签到成功'
        elif json_data["no"] == 1101:
            message = f'{name}吧今天已经签到过了'
    except Exception as e:
        message = f'{name}吧签到失败'

    with lock:
        results.append(message)


def main():
    start_time = time.time()
    results = []
    lock = threading.Lock()
    name_list = get_count()
    threads = []

    for name in name_list:
        thread = threading.Thread(target=sign_thread, args=(name, results, lock))
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()

    end_time = time.time()
    total_time = end_time - start_time
    results.append(f"所有任务完成总耗时：{total_time:.2f}秒")
    email_sender.send_QQ_email_plain('\n'.join(results))


if __name__ == '__main__':
    if os.getenv('EMAIL_ADDRESS') == '' or os.getenv('BDUSS_BFESS') == '' or os.getenv('STOKEN') == '':
        print('请确保环境变量设置正确（邮箱地址、BDUSS_BFESS、STOKEN）')
        exit()

    cookies = {
        'BDUSS_BFESS': os.getenv('BDUSS_BFESS'),
        'STOKEN': os.getenv('STOKEN'),
    }
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0'
    }
    main()
