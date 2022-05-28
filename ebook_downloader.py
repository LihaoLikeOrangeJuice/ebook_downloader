import re
import time

import requests
from loguru import logger
from lxml import html

referer = end_url = input("请输入小说目录的网址:")
url = input("请输入小说第一章的网址:")
begin_time = time.time()
split_url = url.split("/")
base_url = split_url[0] + "/" + split_url[1] + "/" + split_url[2]

with open("XPATH.txt", "r") as file:
    domain_xpath_list = file.read().split("\n")

save_xpath = True

for domain_xpath in domain_xpath_list[0:-1]:
    domain_xpath = domain_xpath.split(" ")
    if base_url == domain_xpath[0]:
        title_xpath = domain_xpath[1]
        content_xpath = domain_xpath[2]
        logger.info(f"符合网址{domain_xpath[0]},使用已收录的XPATH进行爬取")
        save_xpath = False

s = requests.session()
title = ""
file = open("./ebook.txt", "w")
file.close()
content_method = 1
href_method = 1

headers = {
    "User-Agent":
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.64 Safari/537.36 Edg/101.0.1210.53",
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

if save_xpath:
    logger.info("正在智能匹配XPATH")
    find_title_xpath = find_content_xpath = False
    for domain_xpath in domain_xpath_list[0:-1]:
        domain_xpath = domain_xpath.split(" ")
        if not find_content_xpath and not find_title_xpath:
            if len(tree.xpath(domain_xpath[2])):
                content_xpath = domain_xpath[2]
                find_content_xpath = True
            if len(tree.xpath(domain_xpath[1])):
                title_xpath = domain_xpath[1]
                find_title_xpath = True
        elif find_content_xpath and not find_title_xpath:
            if len(tree.xpath(domain_xpath[1])):
                title_xpath = domain_xpath[1]
                find_title_xpath = True
        elif not find_content_xpath and find_title_xpath:
            if len(tree.xpath(domain_xpath[2])):
                content_xpath = domain_xpath[2]
                find_content_xpath = True

        if find_content_xpath and find_title_xpath:
            save_xpath = False
            logger.info("XPATH匹配成功")
            break

if save_xpath:
    logger.info("XPATH匹配失败")

if not save_xpath:
    pass
elif save_xpath and not find_content_xpath and not find_title_xpath:
    content_xpath = input("请输入小说第一章的页面中小说内容所在的div标签的XPATH:")
    title_xpath = input("请输入小说第一章的页面中章节名称所在标签的文字内容的XPATH:")
elif save_xpath and find_content_xpath and not find_title_xpath:
    title_xpath = input("请输入小说第一章的页面中章节名称所在标签的文字内容的XPATH:")
elif save_xpath and not find_content_xpath and find_title_xpath:
    content_xpath = input("请输入小说第一章的页面中小说内容所在的div标签的XPATH:")

logger.info(f"标题XPATH:{title_xpath}")
logger.info(f"内容XPATH:{content_xpath}")
logger.info("开始下载小说")

while True:
    headers = {
        "User-Agent":
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.64 Safari/537.36 Edg/101.0.1210.53",
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

    if content_method == 1:
        content_text_list = tree.xpath(content_xpath + "/p/text()")
        if not len(content_text_list):
            content_text_list = tree.xpath(content_xpath + "/text()")
            content_method = 2
    elif content_method == 2:
        content_text_list = tree.xpath(content_xpath + "/text()")
        if not len(content_text_list):
            content_text_list = tree.xpath(content_xpath + "/p/text()")
            content_method = 1

    with open("./ebook.txt", "a") as file:
        if title != tree.xpath(title_xpath)[0]:
            title = tree.xpath(title_xpath)[0]
            logger.info("标题:\t" + title)
            file.write("\n" + title + '\n')

        for content_text in content_text_list:
            file.write(content_text + "\n")

    referer = url

    if href_method == 1:
        try:
            href = tree.xpath("//a[contains(text(), '下一章')]/@href")[0]
        except Exception:
            href = tree.xpath("//a[contains(text(), '下一页')]/@href")[0]
            href_method = 2
    elif href_method == 2:
        try:
            href = tree.xpath("//a[contains(text(), '下一页')]/@href")[0]
        except Exception:
            href = tree.xpath("//a[contains(text(), '下一章')]/@href")[0]
            href_method = 1

    if len(re.findall("http", href)):
        url = href
    elif len(re.findall("/", href)):
        url = base_url + href
    else:
        url = url.split("/")
        new_url = ""
        for partof_url in url[0:-1]:
            new_url = new_url + partof_url + "/"
        new_url += href
        url = new_url

    logger.info("下一页链接:" + url + "\n")

    if url == end_url:
        logger.info("小说下载完成")
        break

if save_xpath:
    with open("XPATH.txt", "a") as file:
        file.write(base_url + " " + title_xpath + " " + content_xpath + "\n")

total_time = time.time() - begin_time
logger.info("总耗时（单位：分钟）:" + str(int(total_time / 60)))
