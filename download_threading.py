import os
import re
import time
import requests
from bs4 import BeautifulSoup
from time import sleep
from queue import Queue
from threading import Thread
from datetime import datetime
# from selenium import webdriver

URL = "http://gall.dcinside.com"
HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'}
DOWNLOAD = "agal_download"

class DownloadWorker(Thread):

    def __init__(self, queue):
        Thread.__init__(self)
        self.queue = queue
    
    def run(self):
        while True:
            hassan_obj = self.queue.get()

            title, url ,download_path = rich_get_title_and_url(hassan_obj)
            each_post = get_each_post_page(url)
            imgs = extract_img_from_post(each_post)
            download_img_from_list(imgs, download_path, title, url)

            self.queue.task_done()

"""
Integer -> [bsObj]
    return all the post with given page number
"""
def get_post_list(page_num=0):
    post_list_url = requests.get(f"http://gall.dcinside.com/board/lists/?id=idolmaster&page={page_num}&exception_mode=recommend",  headers=HEADERS)
    post_list_soup = BeautifulSoup(post_list_url.content, features="html.parser")
    post_list = post_list_soup.select("tbody .ub-content .gall_tit a")
    return post_list[::2]

def rich_get_post_list(page_num=0):
    try:
        post_list_url = requests.get(f"http://gall.dcinside.com/board/lists/?id=idolmaster&page={page_num}&exception_mode=recommend",  headers=HEADERS)
        post_list_soup = BeautifulSoup(post_list_url.content, features="html.parser")
        post_list = post_list_soup.select("tbody .ub-content")
    except:
        post_list = []
    
    return post_list[::2]

"""
[bsObj] -> [bsObj]
    filter [bsObj] that has 핫산 in the title
"""
def only_hassan(post_list):
    return [x for x in post_list if "핫산" in x.getText()]

def get_title_and_url(bsObj):
    post_title = bsObj.getText()
    post_title = edited_title(post_title).strip()
    post_url = bsObj.get("href")
    post_url = URL + post_url
    download_path = f"{DOWNLOAD}/{post_title}"

    return post_title, post_url, download_path

def rich_get_title_and_url(bsObj):
    all_links = bsObj.select("a")[0]

    post_title = all_links.getText()
    post_title = edited_title(post_title).strip()
    post_url = all_links.get("href")
    post_url = URL + post_url

    date = bsObj.find(attrs={"class" : "gall_date"}).get("title")
    date_time = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
    date_time = date_time.strftime("%Y%m%d")


    download_path = f"{DOWNLOAD}/[{date_time}]{post_title}"

    return post_title, post_url ,download_path

def get_each_post_page(postUrl):
    post_url = requests.get(postUrl,  headers=HEADERS)
    post_soup = BeautifulSoup(post_url.content, features="html.parser")
    return post_soup

"""
bsObj -> 
"""
def extract_img_from_post(bsObj):
    imgs = bsObj.select(".inner .writing_view_box div img")
    return imgs

def download_img_from_list(imgs, download_path, title, url):
    if not os.path.exists(download_path):
        try:
            os.makedirs(download_path)
            print(f"---- [처리중]{download_path}")
            specific_header = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36', 'Referer' : f"{url}"}
            count = 1
            for img in imgs:
                img_src = img.get("src")
                try:
                    img_file = requests.get(img_src,  headers=specific_header)
                    sleep(0.01)
                    open(f"{download_path}/{title}_{count}.png", "wb").write(img_file.content)
                    count += 1
                except:
                    print(f"There was error with{title}")
        except:
                print(f"There was error with{title}")
            
    else:
        print(f"------ [중복]{download_path}")


"""
 String -> String
    takes title in and reformat it as approper dirctory name
"""   
def edited_title(title):
    return re.sub(r'\\|\:|\?|\*|\"|\<|\>|\||\/|\.',"" ,title )

"""
For trace back

post_page = get_post_list(1)
rich_page = rich_get_post_list(1)
hassans = only_hassan(rich_page)

title, url, download_path = rich_get_title_and_url(hassans[0])
each_post = get_each_post_page(url)
imgs = extract_img_from_post(each_post)
download_img_from_list(imgs, download_path, title, url)
       
"""


if __name__ == "__main__":
    st = time.time()
    print("hi")

    if not os.path.exists(DOWNLOAD):
        os.makedirs(DOWNLOAD)
    # 645 is the end of the list on Feb 17th 
    # you can find the end from this ref a href="/board/lists/?id=idolmaster&amp;page=645&amp;exception_mode=recommend" class="page_end">끝</a>

    queue = Queue(100000)

    for i in range(10):
        worker = DownloadWorker(queue)
        worker.daemon = True
        worker.start()

    for page in range(10):

        post_page = rich_get_post_list(page)
        hassans = only_hassan(post_page)
        """
        legacy

        for i in hassans:
            title, url, download_path = get_title_and_url(i)
            each_post = get_each_post_page(url)
            imgs = extract_img_from_post(each_post)
            download_img_from_list(imgs, download_path, title, url)
        """
        
        for i in hassans:
            queue.put(i)
            if(queue.full()):
                print("fukkkk")
                queue.join()
        print(f"the {page} th iteration.")

    queue.join()
    print(f"it takes {time.time() - st} s")
       
    