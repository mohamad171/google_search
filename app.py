import sys
import time
from ui import *
from PyQt5.QtWidgets import *
from threading import Thread,Event
from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.common.by import By
from zipfile import ZipFile
from os import remove
from os.path import exists, abspath, join as _join
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import sys
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeyEvent
from random import choice
from tinydb import TinyDB, Query
from urllib.request import urlopen
import re as r

import logging
logger = logging.getLogger(__name__)
class App:
    proxy_list = []
    proxy_set = False

    black_list = []
    black_set = False
    is_start = False
    th = None


    domain_list = []
    keyword_list = []

    manifest_json = """{
        "version": "1.0.0",
        "manifest_version": 2,
        "name": "Chrome Proxy",
        "permissions": [
            "proxy",
            "tabs",
            "unlimitedStorage",
            "storage",
            "<all_urls>",
            "webRequest",
            "webRequestBlocking"
        ],
        "background": {
            "scripts": ["background.js"]
        },
        "minimum_chrome_version":"22.0.0"
    }"""
    

    app_db = TinyDB("app_db.json",indent=4)
    domain_table = app_db.table("domains")
    keyword_table = app_db.table("keywords")
    task_table = app_db.table("tasks")
    FORMAT = '%(asctime)s %(message)s'
    logging.basicConfig(filename='app.log', level=logging.INFO,format=FORMAT)


    q = Query()

    def __init__(self) -> None:
        pass

    def run_ui(self):
        self.app = QtWidgets.QApplication(sys.argv)
        MainWindow = QtWidgets.QMainWindow()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(MainWindow)
        MainWindow.show()
        self.ui.proxies_btn.clicked.connect(self.getproxyfiles)
        self.ui.domain_btn.clicked.connect(self.add_domain)
        self.ui.keyword_btn.clicked.connect(self.add_keyword)
        self.ui.createtask_btn.clicked.connect(self.add_task)

        self.ui.remove_domain_btn.clicked.connect(self.remove_domain)
        self.ui.remove_keyword_btn.clicked.connect(self.remove_keyword)
        self.ui.start_task.clicked.connect(self.start_check_url)
        self.init_table()
        self.load_keywords()
        self.load_domains()
        self.ui.xpath_input.setText('//*[@class="cz3goc BmP5tf"]')
        self.ui.run_count_input.setText('1')
        # self.ui.select_black_list.clicked.connect(self.getblacklistfiles)
        # self.ui.submit_btn.clicked.connect(self.start_check_url)
        sys.exit(self.app.exec_())
        
    def show_alert(self,title: str = "", message: str = ""):
        _msg = QMessageBox()
        _msg.setInformativeText(message)
        _msg.setWindowTitle(title)
        _msg.exec_()

    def getproxyfiles(self):
      dlg = QFileDialog()
      dlg.setFileMode(QFileDialog.AnyFile)

      if dlg.exec_():
         filenames = dlg.selectedFiles()
         if len(filenames) > 0:
            self.ui.proxies_label.setText(filenames[0].split("/")[-1])
            with open(filenames[0],"r") as f:
                lines = f.readlines()
                self.proxy_list.clear()
                for line in lines:
                    if line != "":
                        self.proxy_list.append(line)
                        self.proxy_set = True

    def remove_domain(self):
        for item in self.ui.domain_list.selectedItems():
            self.domain_table.remove(self.q.name == item.text())
            self.load_domains()
            

    def remove_keyword(self):
        for item in self.ui.keyword_list.selectedItems():
            self.keyword_table.remove(self.q.name == item.text())
            self.load_keywords()

    def load_domains(self):
        self.ui.domain_list.clear()
        for domain in self.domain_table.all():
            self.ui.domain_list.addItem(domain["name"])

    def load_keywords(self):
        self.ui.keyword_list.clear()
        for keyword in self.keyword_table.all():
            self.ui.keyword_list.addItem(keyword["name"])
    
    def init_table(self):
        self.load_tasks()
    
    def load_tasks(self):
        self.ui.task_table.clear()
        for index,task in enumerate(self.task_table.all()):
            count = 0
            self.ui.task_table.insertRow(index)
            for value in task.values():
                self.ui.task_table.setItem(index,count,QTableWidgetItem(str(value)))
                count += 1



    def add_domain(self):
        text = self.ui.domain_input.text()
        query = self.domain_table.search(self.q.name == text)
        if len(text.strip()) > 0 and len(query) == 0:
            self.domain_table.insert({"name":text})
            self.load_domains()
            self.ui.domain_input.clear()
        else:
            self.show_alert("لطفا دامنه را وارد کنید")
            
    def add_keyword(self):
        text = self.ui.keyword_input.text()
        query = self.keyword_table.search(self.q.name == text)
        if len(text.strip()) > 0 and len(query) == 0:
            self.keyword_table.insert({"name":text})
            self.load_keywords()
            self.ui.keyword_input.clear()
        else:
            self.show_alert("لطفا کلمه کلیدی را وارد کنید")

    def add_task(self):
        selected_domain = self.ui.domain_list.selectedItems()[0].text() if len(self.ui.domain_list.selectedItems()) > 0 else None 
        selected_keyword = self.ui.keyword_list.selectedItems()[0].text() if len(self.ui.keyword_list.selectedItems()) > 0 else None 
        stay = self.ui.stay_input.text() if len(self.ui.stay_input.text().strip()) > 0 and self.ui.stay_input.text().isnumeric() else 0
        click_count = self.ui.click_input.text() if len(self.ui.click_input.text().strip()) > 0 and self.ui.click_input.text().isnumeric() else 0
        class_name = self.ui.class_input.text()
        run_count = self.ui.run_count_input.text()
        xpath = self.ui.xpath_input.text()


        if int(click_count) > 0 and int(stay) > 0 and selected_domain and selected_keyword and int(run_count) > 0:
            self.task_table.insert({
                "domain":selected_domain,
                "keyword":selected_keyword,
                "stay":int(stay),
                "click_count":int(click_count),
                "class_name":class_name,
                "run_count":int(run_count),
                "xpath":xpath,
                "status":"NS"
            })
            self.ui.stay_input.clear()
            self.ui.click_input.clear()
            self.ui.class_input.clear()
            self.load_tasks()

        else:
            self.show_alert("Error")





    def getblacklistfiles(self):
        dlg = QFileDialog()
        dlg.setFileMode(QFileDialog.AnyFile)
            
        if dlg.exec_():
            filenames = dlg.selectedFiles()
            if len(filenames) > 0:
                self.ui.blacklist_label.setText(filenames[0].split("/")[-1])
                with open(filenames[0],"r") as f:
                    lines = f.readlines()
                    self.black_list.clear()
                    for line in lines:
                        if line != "":
                            self.black_list.append(line)
                            self.black_set = True

    def get_chromedriver(self,use_proxy = False, user_agent = None, proxy = None):
        chrome_options = ChromeOptions()
        
        if use_proxy:
            background_js = """var config = {
            mode: "fixed_servers",
            rules: {
            singleProxy: {
                scheme: "http",
                host: "%s",
                port: parseInt(%s)
            },
            bypassList: ["localhost"]
            }
        };
    chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});
    function callbackFn(details) {
        return {
            authCredentials: {
                username: "%s",
                password: "%s"
            }
        };
    }
    chrome.webRequest.onAuthRequired.addListener(
                callbackFn,
                {urls: ["<all_urls>"]},
                ['blocking']
    );""" % proxy if len(proxy) == 4 else (str(proxy[0]).strip(), str(proxy[1]).strip().replace("\n",""), "", "")
            pluginfile = self.resource_path('proxy_auth_plugin.zip')

            with ZipFile(pluginfile, 'w') as zp:
                zp.writestr("manifest.json", self.manifest_json)
                zp.writestr("background.js", background_js)
            chrome_options.add_extension(pluginfile)
        
        if user_agent:
            chrome_options.add_argument('--user-agent=%s' % user_agent)
        
        driver = Chrome(
            options=
            chrome_options,
        )
        return driver

    def getIP(self):
        d = str(urlopen('http://checkip.dyndns.com/')
                .read())

        return r.compile(r'Address: (\d+\.\d+\.\d+\.\d+)').search(d).group(1)

    def resource_path(self,relative_path):
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = abspath(".")

        return _join(base_path, relative_path)

    def start_check_url(self):
        if self.is_start:
            return
        
        for task in self.task_table.search(self.q.status == "NS"):
            
            self.process = Thread(target=self.while_start_check_url, args=(task,),daemon=True)
            self.process.start()
            self.ui.start_task.setText(" اجرا شد")
            # self.while_start_check_url(task)
            self.task_table.remove(doc_ids=[task.doc_id])
            self.load_tasks()

    def while_start_check_url(self,task):
        count = 0
        while count < task["run_count"]:
            proxy_index = 0
            if self.proxy_set:
                if proxy_index == len(self.proxy_list):
                    proxy_index = 0

                try:
                    proxies = tuple(choice(self.proxy_list).replace("\n","").split(":"))
                    proxy_index += 1
                except:
                    proxy_index = 0
                self.url_check(
                task,
                proxies=proxies,
                proxy_status=True,
                black_list = self.black_list,

                )
            else:
                self.url_check(
                    task,
                    black_list = self.black_list,
                    )
            logger.info(f"IP:{self.getIP()} ---- open {task['domain']} for {count+1} time/s...")
            count += 1
    def close_dialog(self,driver):
        try:
            element = driver.find_element(By.XPATH,"//*[@id='W0wltc']")
            if element:
                element.click()
        except:
            pass

        try:
            element = driver.find_element(By.XPATH,"/html/body/div[2]/div[1]/div[3]/form[1]/input[12]")
            if element:
                element.click()
        except:
            pass


        count = 0
    
    def open_links(self,driver,task,black_list):
        original_window = driver.current_window_handle
        count = 0
        for i in range(0,3):
            url = f"https://www.google.com/search?q={task['keyword']}&start={i*10}"
            driver.get(url)
            if "g-recaptcha-response" in driver.page_source or "That's an error" in driver.page_source:
                return
            if i == 0:
                self.close_dialog(driver=driver)
            # for search in driver.find_elements(By.XPATH,f"//a[contains(@href,'{domain}')]"):
            #     href = search.get_attribute("href")
            for search in driver.find_elements(By.XPATH,task["xpath"]):
                href = search.get_attribute("data-pcu")
                if href not in black_list and task["domain"] in href:
                    if count < task["click_count"]:
                        ActionChains(driver).move_to_element(search).key_down(Keys.CONTROL).click(search).key_up(Keys.CONTROL).perform()
                        count += 1
            time.sleep(3)
        for tab in driver.window_handles:
            if tab != original_window:
                driver.switch_to.window(tab)
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                logger.info(f"IP:{self.getIP()} ---- Scroll to endof page at {href}...")
                if task["class_name"] != "":
                    cl = task["class_name"]
                    elements = driver.find_elements(By.XPATH,f"//*[contains(@class,'{cl}'])")
                    for e in elements:
                        e.click()
                        logger.info(f"IP:{self.getIP()} ---- Click on element with class {cl} at {href}...")
                time.sleep(task["stay"])

    def url_check(
            self,
        task: dict = None,  proxy_status: bool = False,
        proxies: tuple = (), time_sleep: int = 10,
        black_list: bool = False, black_word: list = [
            "detected unusual traffic",
            "is blocked",
            "Your client does not have permission"
        ]
    ):
        global close_app
        
        
        if not proxy_status:
            driver = self.get_chromedriver(False,user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 10_3 like Mac OS X) AppleWebKit/602.1.50 (KHTML, like Gecko) CriOS/56.0.2924.75 Mobile/14E5239e Safari/602.1")
        else:
            driver = self.get_chromedriver(True, proxy=proxies,user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 10_3 like Mac OS X) AppleWebKit/602.1.50 (KHTML, like Gecko) CriOS/56.0.2924.75 Mobile/14E5239e Safari/602.1")
            
        self.open_links(driver,task,black_list)
        driver.quit()

if __name__ == "__main__":
    app = App()
    app.run_ui()
    