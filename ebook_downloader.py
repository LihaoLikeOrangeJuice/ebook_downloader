import re
import time

import requests
from loguru import logger
from lxml import html

referer = input("请输入小说目录的网址:")
url = input("请输入小说第一章的网址:")
end_url = input("请输入小说最后一章的网址:")

split_url = url.split("/")
base_url = split_url[0] + "/" + split_url[1] + "/" + split_url[2]

begin_time = time.time()
s = requests.session()
file = open("./ebook.txt", "w")
file.close()

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

logger.info("正在智能匹配XPATH")
find_title_xpath = find_content_xpath = False

with open("title_xpath.txt", "r") as file:
    title_xpath_list = file.read().split(" ")
with open("content_xpath.txt", "r") as file:
    content_xpath_list = file.read().split(" ")

for tx in title_xpath_list[0:-1]:
    title = tree.xpath(tx)
    if len(title):
        title = title[0]
    else:
        continue
    if len(re.findall(
            "章", title)) and (len(re.findall("\d", title))
                              or len(re.findall("[零一二三四五六七八九十百千万亿]", title))
                              or len(re.findall("[零壹贰叁肆伍陆柒捌玖拾佰仟万亿]", title))):
        title_xpath = tx
        find_title_xpath = True
        break
if not find_title_xpath:
    for tx in title_xpath_list[0:-1]:
        title = tree.xpath(tx)
        if len(title):
            title = title[0]
        else:
            continue
        title = tree.xpath(tx)[0]
        if len(re.findall("\d", title)) or len(
                re.findall("[零一二三四五六七八九十百千万亿]", title)) or len(
                    re.findall("[零壹贰叁肆伍陆柒捌玖拾佰仟万亿]", title)):
            title_xpath = tx
            find_title_xpath = True
            break

for cx in content_xpath_list[0:-1]:
    if len(tree.xpath(cx + "/p/text()")) > 20 or len(
            tree.xpath(cx + "/text()")) > 20:
        content_xpath = cx
        find_content_xpath = True
        break

if find_content_xpath and find_title_xpath:
    save_xpath = False
    logger.info("XPATH匹配成功")
else:
    save_xpath = True
    logger.info("XPATH匹配失败")

if save_xpath and not find_content_xpath and not find_title_xpath:
    content_xpath = input("请输入小说第一章的页面中小说内容所在的标签(一般是div标签)的XPATH:")
    title_xpath = input("请输入小说第一章的页面中章节名称所在标签的文字内容的XPATH:")
elif save_xpath and find_content_xpath and not find_title_xpath:
    title_xpath = input("请输入小说第一章的页面中章节名称所在标签的文字内容的XPATH:")
elif save_xpath and not find_content_xpath and find_title_xpath:
    content_xpath = input("请输入小说第一章的页面中小说内容所在的标签(一般是div标签)的XPATH:")

logger.info(f"标题XPATH:{title_xpath}")
logger.info(f"内容XPATH:{content_xpath}")

if len(tree.xpath(content_xpath + "/p/text()")) > 20:
    content_method = 1
elif len(tree.xpath(content_xpath + "/text()")) > 20:
    content_method = 2
else:
    logger.error("内容XPATH无法定位到元素或定位到的元素过少")
    logger.info(
        f"\"/p/text()\"方法定位到的元素数量:{len(tree.xpath(content_xpath + '/p/text()'))}"
    )
    logger.info(
        f"\"/text()\"方法定位到的元素数量:{len(tree.xpath(content_xpath + '/text()'))}")

if len(tree.xpath("//a[contains(text(), '下一章')]/@href")):
    href_method = 1
elif len(tree.xpath("//a[contains(text(), '下一页')]/@href")):
    href_method = 2
else:
    logger.error("无法找到下一章的连接")

logger.info("开始下载小说\n")

finish_task = False
title = ""

while True:
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
    elif content_method == 2:
        content_text_list = tree.xpath(content_xpath + "/text()")

    with open("./ebook.txt", "a") as file:
        if title != tree.xpath(title_xpath)[0]:
            title = tree.xpath(title_xpath)[0]
            logger.info("标题:\t" + title)
            file.write("\n" + title + '\n')

        for content_text in content_text_list:
            file.write(content_text + "\n")

    referer = url

    if href_method == 1:
        href = tree.xpath("//a[contains(text(), '下一章')]/@href")[0]
    elif href_method == 2:
        href = tree.xpath("//a[contains(text(), '下一页')]/@href")[0]

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

    if finish_task:
        logger.info("小说下载完成")
        break

    if url == end_url:
        finish_task = True

if save_xpath and not find_content_xpath and not find_title_xpath:
    with open("title_xpath.txt", "a") as file:
        file.write(title_xpath + " ")
    with open("content_xpath.txt", "a") as file:
        file.write(content_xpath + " ")
elif save_xpath and find_content_xpath and not find_title_xpath:
    with open("title_xpath.txt", "a") as file:
        file.write(title_xpath + " ")
elif save_xpath and not find_content_xpath and find_title_xpath:
    with open("content_xpath.txt", "a") as file:
        file.write(content_xpath + " ")

total_time = time.time() - begin_time
logger.info(f"总耗时: {str(int(total_time / 60))}分钟{str(int(total_time % 60))}秒")
