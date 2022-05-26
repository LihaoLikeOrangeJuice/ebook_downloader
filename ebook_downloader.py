import time

import requests
from loguru import logger
from lxml import html

end_url = input("请输入小说目录的网址:")
referer = url = input("请输入小说第一章的网址:")
base_url = url.split("com")[0] + "com"

with open("XPATH.txt", "r") as file:
    domain_xpath_list = file.read().split("\n")

save_xpath = True

for domain_xpath in domain_xpath_list:
    domain_xpath = domain_xpath.split(" ")
    if base_url == domain_xpath[0]:
        title_xpath = domain_xpath[1]
        content_xpath = domain_xpath[2]
        save_xpath = False

if save_xpath:
    content_xpath = input("请输入小说第一章的页面中小说内容所在的div标签的XPATH"
                          "(不支持由br分隔小说内容的网站):")
    title_xpath = input("请输入小说第一章的页面中章节名称所在标签的文字内容的XPATH:")

begin_time = time.time()
logger.info("开始下载")

s = requests.session()
title = ""
file = open("./ebook.txt", "w")
file.close()

while True:
    headers = {
        "User-Agent":
        "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Mobile Safari/537.36 Edg/100.0.1185.50",
        "Referer": referer
    }

    while True:
        try:
            page = s.get(url, headers=headers, timeout=5)
            logger.info("成功获取到页面")
            break
        except Exception as e:
            logger.warning("获取页面失败\n" + str(e))

    tree = html.fromstring(page.content)
    content_text_list = tree.xpath(content_xpath + "/p/text()")

    with open("./ebook.txt", "a") as file:
        if title != tree.xpath(title_xpath)[0]:
            title = tree.xpath(title_xpath)[0]
            logger.info("标题:\t" + title)
            file.write("\n" + title + '\n')

        for content_text in content_text_list[0:-1]:
            file.write(content_text + "\n")

    referer = url
    url = base_url + tree.xpath("//a[contains(text(), '下一章')]/@href")[0]
    logger.info("下一页链接:" + url + "\n")

    if url == end_url:
        logger.info("小说下载完成")
        break

if save_xpath:
    with open("XPATH.txt", "a") as file:
        file.write(base_url + " " + title_xpath + " " + content_xpath + "\n")

total_time = time.time() - begin_time
logger.info("总耗时（单位：分钟）:" + str(int(total_time / 60)))
