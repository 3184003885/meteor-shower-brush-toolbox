import sys
import time
import threading
import ctypes

class LoadingAnimation:
    def __init__(self):
        self.stop_flag = False
        self.animation_thread = None
        self.status = ""
        self.status_lock = threading.Lock()
        
    def set_status(self, status):
        with self.status_lock:
            self.status = status
    
    def _animate(self):
        animation = "|/-\\"
        idx = 0
        while not self.stop_flag:
            with self.status_lock:
                status_text = self.status
            sys.stdout.write('\r正在加载程序... ' + animation[idx % len(animation)] + (f" | {status_text}" if status_text else ""))
            sys.stdout.flush()
            idx += 1
            time.sleep(0.1)
            
    def start(self):
        console = ctypes.windll.kernel32.GetConsoleWindow()
        if console:
            ctypes.windll.user32.ShowWindow(console, 1)  
            
        self.stop_flag = False
        self.animation_thread = threading.Thread(target=self._animate)
        self.animation_thread.daemon = True
        self.animation_thread.start()
        
    def stop(self):
        self.stop_flag = True
        if self.animation_thread:
            self.animation_thread.join()
        sys.stdout.write('\r程序加载完成!    \n')
        sys.stdout.flush()

    def run_with_checks(self, check_func):
        self.start()
        try:
            check_func()
        finally:
            self.stop()
