import customtkinter
import os
import sys
import shutil
import ctypes
from functions.device_info import DeviceInfoBar
import threading
from config.version import VERSION, INTRO_TEXT
from tkinter import messagebox 
import json
import platform
import datetime

def check_disk_space():
    system_drive = os.environ.get('SystemDrive', 'C:')
    exe_path = os.path.abspath(sys.argv[0])
    program_drive = os.path.splitdrive(exe_path)[0] + '\\'
    sys_total, sys_used, sys_free = shutil.disk_usage(system_drive + '\\')
    prog_total, prog_used, prog_free = shutil.disk_usage(program_drive)
    min_gb = 2
    if sys_free < min_gb * 1024**3:
        messagebox.showwarning("磁盘空间不足", f"系统盘({system_drive}) 剩余空间不足 {min_gb}GB，当前为 {sys_free // (1024**3)} GB")
    if prog_free < min_gb * 1024**3:
        messagebox.showwarning("磁盘空间不足", f"工具箱所在盘({program_drive}) 剩余空间不足 {min_gb}GB，当前为 {prog_free // (1024**3)} GB")

def hide_console():
    if sys.platform == "win32":
        whnd = ctypes.windll.kernel32.GetConsoleWindow()
        if whnd != 0:
            ctypes.windll.user32.ShowWindow(whnd, 0)  

class App(customtkinter.CTk):
    def __init__(self):
        check_disk_space()  
        super().__init__()  
        self.warning_label = None
        self.title("流星雨工具箱,QQ3184003885,群1045528316,版本:免费离线版")
        self._update_title_with_identity_and_time()
        self.geometry("1200x700")  
        self.minsize(1000, 600)
        self.grid_rowconfigure(0, weight=1) 
        self.grid_columnconfigure(1, weight=4)  
        self.grid_columnconfigure(2, weight=1) 
        self.sidebar_frame = customtkinter.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew") 
        self.logo_label = customtkinter.CTkLabel(
            self.sidebar_frame, 
            text="功能菜单", 
            font=("微软雅黑", 20, "bold")  
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        self.menu_buttons = [
            ("主页", self.show_main_dashboard, "🏠", True),
            ("fastboot工具", self.show_fastboot_menu, "📱", True),
            ("ADB工具", self.show_adb_menu, "⚡", True),
            ("其他工具", self.show_other_tools, "🔧", True),
            ("关于", self.show_about, "ℹ️", True)
        ]
        self.menu_button_widgets = []  
        for i, (text, command, icon, show_when_not_login) in enumerate(self.menu_buttons, 1):
            button = customtkinter.CTkButton(
                self.sidebar_frame,
                text=f"{icon} {text}",
                command=command,
                width=180, 
                height=40, 
                font=("微软雅黑", 13),
                state="normal"
            )
            button.grid(row=i, column=0, padx=20, pady=6)
            self.menu_button_widgets.append((button, True, i))
        self.main_frame = customtkinter.CTkFrame(self)
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

        self.device_info = DeviceInfoBar(self)

        self.show_main_dashboard()
        
        self.after(500, self.initial_check)
        self.check_user_agreement()
        
        hide_console()
        
        log_frame = customtkinter.CTkFrame(self)
        log_frame.grid(row=0, column=2, sticky="nsew", padx=(0, 20), pady=20)

        log_header = customtkinter.CTkFrame(log_frame)
        log_header.pack(fill="x", padx=10, pady=5)

        customtkinter.CTkLabel(
            log_header,
            text="操作日志",
            font=("微软雅黑", 12, "bold")
        ).pack(side="left")

        customtkinter.CTkButton(
            log_header,
            text="清空日志",
            command=self.clear_log,
            width=60,
            height=24,
            font=("微软雅黑", 10)
        ).pack(side="right", padx=5)

        self.log_text = customtkinter.CTkTextbox(
            log_frame,
            font=("Consolas", 11)
        )
        self.log_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
    def _update_title_with_identity_and_time(self):
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        base_title = "流星雨工具箱,QQ3184003885,群1045528316,版本:免费离线版"
        self.title(f"{base_title} | 时间: {now}")
        self.after(1000, self._update_title_with_identity_and_time)

    def check_user_agreement(self):
        import os
        agreement_file = os.path.join("data", "user_agreement_accepted.json")
        if not os.path.exists("data"):
            os.makedirs("data", exist_ok=True)
        agreed = False
        if os.path.exists(agreement_file):
            try:
                with open(agreement_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    agreed = data.get("accepted", False)
            except Exception:
                agreed = False
        if not agreed:
            self.show_user_agreement_dialog(agreement_file)

    def show_user_agreement_dialog(self, agreement_file):
        agreement_text = (
            "流星雨工具箱 用户声明\n\n"
            "1. 本工具箱仅供安卓设备爱好者进行设备管理、刷机、分区操作、文件管理、资源下载等合法用途。\n"
            "2. 请勿利用本工具箱进行任何违法违规活动，包括但不限于绕过设备安全、破解、刷写非法固件、侵犯他人权益等。\n"
            "3. 刷机、分区、数据操作等功能具有一定风险，可能导致设备数据丢失、变砖、保修失效等后果。请在操作前备份重要数据，并确保已充分了解相关风险。\n"
            "4. 本工具箱部分功能涉及第三方资源下载、网络检测等，相关内容由第三方提供，工具箱不对其合法性、可用性负责。\n"
            "5. 本工具箱为免费工具，严禁商用、倒卖、二次开发、传播破解版本等行为。\n"
            "6. 使用本工具箱即表示您已知悉并同意上述声明，因使用本工具箱造成的任何后果由用户自行承担，开发者不承担任何法律责任。\n"
            "7. 如有疑问或建议，请联系作者或加入官方交流群获取帮助。\n"
            "\n作者QQ：3184003885\n官方群：1045528316\n"
            "\n你是否同意并继续使用本工具箱？"
        )
        dialog = customtkinter.CTkToplevel(self)
        dialog.title("用户声明")
        dialog.geometry("600x480")
        dialog.grab_set()
        dialog.attributes('-topmost', True)
        customtkinter.CTkLabel(
            dialog,
            text="用户声明",
            font=("微软雅黑", 20, "bold")
        ).pack(pady=15)
        text_box = customtkinter.CTkTextbox(
            dialog,
            font=("微软雅黑", 13),
            height=320,
            wrap="word"
        )
        text_box.pack(fill="both", expand=True, padx=20, pady=10)
        text_box.insert("end", agreement_text)
        text_box.configure(state="disabled")
        btn_frame = customtkinter.CTkFrame(dialog)
        btn_frame.pack(pady=20)
        def accept():
            with open(agreement_file, "w", encoding="utf-8") as f:
                json.dump({"accepted": True}, f)
            dialog.destroy()
        def reject():
            dialog.destroy()
            self.destroy()
            sys.exit(0)
        countdown_var = customtkinter.StringVar(value="(15秒后可同意)")
        accept_btn = customtkinter.CTkButton(
            btn_frame,
            text="同意并继续",
            command=None,
            width=160,
            font=("微软雅黑", 14),
            state="disabled"
        )
        accept_btn.pack(side="left", padx=20)
        customtkinter.CTkButton(
            btn_frame,
            text="不同意/退出",
            command=reject,
            width=160,
            fg_color="#FF4444",
            hover_color="#CC3333",
            font=("微软雅黑", 14)
        ).pack(side="left", padx=20)
        countdown_label = customtkinter.CTkLabel(
            btn_frame,
            textvariable=countdown_var,
            font=("微软雅黑", 12),
            text_color="gray"
        )
        countdown_label.pack(side="left", padx=10)
        def enable_accept():
            accept_btn.configure(state="normal", command=accept)
            countdown_var.set("")
        def countdown(t=15):
            if t > 0:
                countdown_var.set(f"({t}秒后可同意)")
                dialog.after(1000, lambda: countdown(t-1))
            else:
                enable_accept()
        countdown(15)
        dialog.wait_window()

    def initial_check(self):
        import requests
        import shutil
        import tkinter.messagebox as messagebox
        try:
            total, used, free = shutil.disk_usage("C:\\")
            free_gb = free / (1024 ** 3)
            if free_gb < 30:
                self.add_log(f"C盘剩余空间不足：{free_gb:.2f}GB")
                messagebox.showerror("磁盘空间不足", f"C盘剩余空间仅 {free_gb:.2f}GB，建议至少保留30GB空间！")
            else:
                self.add_log(f"C盘剩余空间：{free_gb:.2f}GB")
        except Exception as e:
            self.add_log(f"C盘空间检测失败: {str(e)}")
            messagebox.showwarning("磁盘检测", f"C盘空间检测失败: {str(e)}")

    def show_main_dashboard(self):
        """显示主控制台"""
        self.clear_main_frame()

        welcome_frame = customtkinter.CTkFrame(self.main_frame)
        welcome_frame.pack(fill="x", padx=30, pady=20)

        customtkinter.CTkLabel(
            welcome_frame,
            text="欢迎使用流星雨工具箱",
            font=("微软雅黑", 24, "bold")
        ).pack(pady=20)

        info_frame = customtkinter.CTkFrame(self.main_frame)
        info_frame.pack(fill="both", expand=True, padx=30, pady=20)

        customtkinter.CTkLabel(
            info_frame,
            text=INTRO_TEXT,  
            font=("微软雅黑", 14),
            justify="left"
        ).pack(padx=20, pady=20)

        version_label = customtkinter.CTkLabel(
            self.main_frame,
            text=f"版本: {VERSION}",
            font=("微软雅黑", 12),
            text_color="gray"
        )
        version_label.pack(side="bottom", pady=10)

    def update_device_status(self):
        """更新设备状态显示"""
        pass

    def show_flash_menu(self):
        self.clear_main_frame()

    def show_app_menu(self):
        self.clear_main_frame()

    def show_adb_menu(self):
        self.clear_main_frame()

        customtkinter.CTkLabel(
            self.main_frame,
            text="ADB 工具集",
            font=("微软雅黑", 24, "bold")
        ).pack(pady=20)

        tools_frame = customtkinter.CTkFrame(self.main_frame)
        tools_frame.pack(fill="both", expand=True, padx=30, pady=20)

        tools = [
            ("文件管理", "📂", self.show_file_manager),
            ("安装应用", "📥", self.show_app_installer),
            ("应用管理", "📱", self.show_app_manager),
            ("Shell终端", "💻", self.show_shell_terminal),
        ]

        for i, (text, icon, command) in enumerate(tools):
            row = i // 2
            col = i % 2
            
            tool_btn = customtkinter.CTkButton(
                tools_frame,
                text=f"{icon} {text}",
                command=command,
                width=250,
                height=80,
                font=("微软雅黑", 16)
            )
            tool_btn.grid(row=row, column=col, padx=15, pady=15, sticky="nsew")

        tools_frame.grid_columnconfigure(0, weight=1)
        tools_frame.grid_columnconfigure(1, weight=1)

    def show_scrcpy(self):  
        try:
            import subprocess
            scrcpy_path = "platform-tools\\scrcpy.exe"
            
            if not os.path.exists(scrcpy_path):
                self.add_log("未找到投屏程序 scrcpy.exe，请将 scrcpy.exe 放入 platform-tools 文件夹")
                messagebox.showerror("错误", "未找到投屏程序，请检查文件是否存在")
                return

            result = subprocess.run(
                ["platform-tools\\adb.exe", "devices"],
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            
            if len(result.stdout.strip().splitlines()) <= 1:
                self.add_log("未检测到设备连接，请确保设备已连接并开启 USB 调试")
                messagebox.showerror("错误", "未检测到设备连接")
                return

            self.add_log("正在启动投屏程序...")
            
            process = subprocess.Popen(
                [scrcpy_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                encoding='utf-8'
            )

            try:
                return_code = process.wait(timeout=1)
                if return_code != 0:
                    stderr_output = process.stderr.read() if process.stderr else "未知错误"
                    self.add_log(f"投屏启动失败: {stderr_output}")
                    messagebox.showerror("错误", f"投屏启动失败: {stderr_output}")
                    return
            except subprocess.TimeoutExpired:
                self.add_log("投屏程序已成功启动")
                
        except Exception as e:
            error_msg = f"启动投屏失败: {str(e)}"
            self.add_log(error_msg)
            messagebox.showerror("错误", error_msg)

    def show_file_manager(self):
        from functions.file_manager import FileManager
        manager = FileManager(self)
        manager.manage_files()

    def show_fastboot_menu(self):
        self.clear_main_frame()
        import requests
        scroll_container = customtkinter.CTkScrollableFrame(
            self.main_frame,
            label_text="FastBoot 工具集",
            label_font=("微软雅黑", 24, "bold")
        )
        scroll_container.pack(fill="both", expand=True, padx=20, pady=20)

        oplus_frame = customtkinter.CTkFrame(scroll_container)
        oplus_frame.pack(fill="x", padx=10, pady=10)
        customtkinter.CTkLabel(
            oplus_frame,
            text="欧加真刷机",
            font=("微软雅黑", 16, "bold")
        ).pack(pady=10)
        customtkinter.CTkButton(
            oplus_frame,
            text="进入欧加真刷机功能",
            command=self.show_oplus_flash,  
            width=200,
            height=50,
            font=("微软雅黑", 14)
        ).pack(pady=10)

        xiaomi_frame = customtkinter.CTkFrame(scroll_container)
        xiaomi_frame.pack(fill="x", padx=10, pady=10)
        
        customtkinter.CTkLabel(
            xiaomi_frame,
            text="小米线刷工具",
            font=("微软雅黑", 16, "bold")
        ).pack(pady=10)
        
        customtkinter.CTkButton(
            xiaomi_frame,
            text="启动小米线刷",
            command=self.show_xiaomi_flash,
            width=200,
            height=50,
            font=("微软雅黑", 14)
        ).pack(pady=10)

        customtkinter.CTkFrame(
            scroll_container,
            height=2
        ).pack(fill="x", padx=10, pady=20)

        tools_frame = customtkinter.CTkFrame(scroll_container)
        tools_frame.pack(fill="x", padx=10, pady=10)

        customtkinter.CTkLabel(
            tools_frame,
            text="分区管理工具",
            font=("微软雅黑", 16, "bold")
        ).pack(pady=10)

        buttons_frame = customtkinter.CTkFrame(tools_frame)
        buttons_frame.pack(fill="both", expand=True, padx=20, pady=10)

        customtkinter.CTkButton(
            buttons_frame,
            text="进入分区管理",
            command=self.show_partition_manager,
            width=220,
            height=60,
            font=("微软雅黑", 15)
        ).pack(pady=10)

        customtkinter.CTkLabel(
            buttons_frame,
            text="实时显示设备分区信息，包括分区名、类型等。\n支持分区刷写功能。",
            font=("微软雅黑", 12),
            text_color="gray"
        ).pack(pady=5)

    def show_xiaomi_flash(self):
        self.clear_main_frame()
        from functions.xiaomi_flash import XiaomiFlash
        flash_tool = XiaomiFlash(self)
        flash_tool.show_menu()

    def show_partition_manager(self):
        from functions.fastboot_tools import FastbootTools
        fastboot = FastbootTools(self)
        fastboot.show_menu()

    def flash_partition(self, partition):
        from functions.fastboot_tools import FastbootTools
        fastboot = FastbootTools(self)
        fastboot.flash_image(partition)

    def show_env_menu(self):
        self.clear_main_frame()
        from functions.env_check import EnvCheck
        env_tool = EnvCheck(self.main_frame)  
        env_tool.show_menu()

    def show_app_installer(self):
        from functions.app_installer import AppInstaller
        installer = AppInstaller(self)
        installer.show_installer()

    def show_app_manager(self):
        from functions.app_manager import AppManager
        manager = AppManager(self)
        manager.show_menu()
        
    def show_device_status(self):
        self.clear_main_frame()

        info_container = customtkinter.CTkScrollableFrame(
            self.main_frame,
            label_text="设备详细信息",
            label_font=("微软雅黑", 16, "bold")
        )
        info_container.pack(fill="both", expand=True, padx=20, pady=20)

        from functions.device_detector import DeviceDetector
        info = DeviceDetector.get_detailed_info()  
        
        if info:
            for category, items in info.items():
            
                customtkinter.CTkLabel(
                    info_container,
                    text=category,
                    font=("微软雅黑", 14, "bold")
                ).pack(fill="x", padx=10, pady=(15,5))
                
                category_frame = customtkinter.CTkFrame(info_container)
                category_frame.pack(fill="x", padx=10, pady=5)
                
                for key, value in items.items():
                    item_frame = customtkinter.CTkFrame(category_frame)
                    item_frame.pack(fill="x", pady=2)
                    
                    customtkinter.CTkLabel(
                        item_frame,
                        text=f"{key}:",
                        font=("微软雅黑", 12),
                        width=150,
                        anchor="w"
                    ).pack(side="left", padx=10)
                    
                    customtkinter.CTkLabel(
                        item_frame,
                        text=str(value),
                        font=("微软雅黑", 12),
                        anchor="w"
                    ).pack(side="left", padx=10, fill="x", expand=True)
        else:
            customtkinter.CTkLabel(
                info_container,
                text="未检测到设备\n请检查连接和调试模式",
                font=("微软雅黑", 14)
            ).pack(pady=30)

        customtkinter.CTkButton(
            self.main_frame,
            text="刷新信息",
            command=self.show_device_status,
            width=120
        ).pack(pady=10)

    def clear_main_frame(self): 
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    def check_login_and_execute(self, command):
        public_commands = [
            self.show_main_dashboard,
            self.show_login,
            self.show_about,
            self.show_file_manager,
            self.show_partition_manager,
            self.show_command_tool,
            self.show_oplus_flash,  
        ]
        if command in public_commands:
            command()
            return
        restricted_commands = [
            self.show_one_click_root, 
            self.show_env_menu
        ]
        if command in restricted_commands:
            user = None
            if user.get('vip_level') not in ["超级用户", "高级用户"]:
                messagebox.showwarning(
                    "需要升级",
                    "此功能仅对高级用户和超级用户开放\n请升级账号后使用"
                )
                return
        command()

    def add_log(self, message):
        """添加日志信息"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert("end", f"[{timestamp}] {message}\n")
        self.log_text.see("end")

    def clear_log(self):
        """清空日志"""
        self.log_text.delete("1.0", "end")

    def show_other_tools(self):
        """显示其他工具界面"""
        from functions.other_tools import OtherTools
        other_tools = OtherTools(self)
        other_tools.show_menu()

    def check_remote_apps(self):
        """检测远程软件"""
        try:
            from functions.remote_detector import RemoteDetector
            detected_apps = RemoteDetector.check_remote_apps()
            
            if detected_apps:
                user = None
                
                if not user or user.get('vip_level') != "超级用户":
                    warning_text = (
                        f"⚠️ 警告: 检测到远程软件 ({', '.join(detected_apps)})\n"
                        "此工具收费，禁止商用\n"
                        "请勿用此工具做任何违法行为"
                    )
                    if hasattr(self, 'warning_label') and self.warning_label:
                        self.warning_label.configure(text=warning_text, text_color="red")
                else:
                    if hasattr(self, 'warning_label') and self.warning_label:
                        self.warning_label.configure(text="")
            else:
                if hasattr(self, 'warning_label') and self.warning_label:
                    self.warning_label.configure(text="")
        except Exception as e:
            print(f"Remote app check error: {e}")
        finally:
            # 使用更长的检测间隔，避免频繁检测
            if not self.winfo_exists():  # 检查窗口是否还存在
                return
            self.after(30000, self.check_remote_apps)  # 改为30秒检测一次

    def show_about(self):
        """显示关于界面"""
        from config.about import AUTHOR_INFO, DESCRIPTION, SPONSOR_URL
        
        self.clear_main_frame()
        
        about_container = customtkinter.CTkScrollableFrame(
            self.main_frame,
            label_text="关于",
            label_font=("微软雅黑", 24, "bold")
        )
        about_container.pack(fill="both", expand=True, padx=20, pady=20)

        author_frame = customtkinter.CTkFrame(about_container)
        author_frame.pack(fill="x", padx=10, pady=10)
        
        customtkinter.CTkLabel(
            author_frame,
            text="作者信息",
            font=("微软雅黑", 16, "bold")
        ).pack(pady=10)
        
        info = AUTHOR_INFO.copy()
        
        for key, value in info.items():
            item_frame = customtkinter.CTkFrame(author_frame)
            item_frame.pack(fill="x", padx=20, pady=2)
            
            customtkinter.CTkLabel(
                item_frame,
                text=f"{key}:",
                font=("微软雅黑", 14),
                width=100,
                anchor="w"
            ).pack(side="left", padx=10)
            
            if key == "主页":
                btn = customtkinter.CTkButton(
                    item_frame,
                    text=value,
                    command=lambda: self._open_url(value),
                    font=("微软雅黑", 14),
                    fg_color="transparent",
                    text_color="#1F538D",
                    hover_color="#E5F3FF"
                )
                btn.pack(side="left", padx=10)
            else:
                customtkinter.CTkLabel(
                    item_frame,
                    text=value,
                    font=("微软雅黑", 14),
                    anchor="w"
                ).pack(side="left", padx=10)

        desc_frame = customtkinter.CTkFrame(about_container)
        desc_frame.pack(fill="x", padx=10, pady=(20,10))
        
        customtkinter.CTkLabel(
            desc_frame,
            text="工具说明",
            font=("微软雅黑", 16, "bold")
        ).pack(pady=10)
        
        customtkinter.CTkLabel(
            desc_frame,
            text=DESCRIPTION,
            font=("微软雅黑", 14),
            justify="left",
            wraplength=600
        ).pack(padx=20, pady=10)

        sponsor_frame = customtkinter.CTkFrame(about_container)
        sponsor_frame.pack(fill="x", padx=10, pady=10)
        
        customtkinter.CTkButton(
            sponsor_frame,
            text="💝 赞助支持",
            command=lambda: self._open_url(SPONSOR_URL),
            font=("微软雅黑", 14),
            fg_color="#FF6B6B",
            hover_color="#FF4444"
        ).pack(pady=10)

    def _open_url(self, url):
        """打开URL链接"""
        import webbrowser
        webbrowser.open(url)

    def show_partition_tools(self):
        """显示分区操作工具"""
        from functions.partition_tools import PartitionTools
        tools = PartitionTools(self)
        tools.show_menu()

    def show_gki_flash(self):
        """显示GKI刷入界面"""
        from functions.gki_flash import GKIFlash
        gki_tool = GKIFlash(self)
        gki_tool.show_menu()

    def show_shell_terminal(self):
        """显示安卓Shell终端界面"""
        terminal_window = customtkinter.CTkToplevel(self)
        terminal_window.title("安卓Shell终端")
        terminal_window.geometry("800x600")
        terminal_window.minsize(600, 400)
        
        terminal_window.attributes('-topmost', True)
        terminal_window.focus_force()
        
        main_frame = customtkinter.CTkFrame(terminal_window)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        title_label = customtkinter.CTkLabel(
            main_frame,
            text="安卓Shell终端",
            font=("微软雅黑", 16, "bold")
        )
        title_label.pack(pady=(10, 5))
        
        status_frame = customtkinter.CTkFrame(main_frame)
        status_frame.pack(fill="x", padx=10, pady=5)
        
        status_label = customtkinter.CTkLabel(
            status_frame,
            text="正在检测设备...",
            font=("微软雅黑", 12),
            text_color="orange"
        )
        status_label.pack(pady=5)
        
        output_frame = customtkinter.CTkFrame(main_frame)
        output_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        output_label = customtkinter.CTkLabel(
            output_frame,
            text="终端输出",
            font=("微软雅黑", 12, "bold")
        )
        output_label.pack(pady=5)
        
        output_text = customtkinter.CTkTextbox(
            output_frame,
            font=("Consolas", 11),
            wrap="word"
        )
        output_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        input_frame = customtkinter.CTkFrame(main_frame)
        input_frame.pack(fill="x", padx=10, pady=5)
        
        input_label = customtkinter.CTkLabel(
            input_frame,
            text="输入命令:",
            font=("微软雅黑", 12)
        )
        input_label.pack(pady=5)
        
        command_entry = customtkinter.CTkEntry(
            input_frame,
            placeholder_text="输入shell命令，如: ls, pwd, cat /proc/version 等",
            font=("Consolas", 11)
        )
        command_entry.pack(fill="x", padx=10, pady=(0, 10))
        
        button_frame = customtkinter.CTkFrame(main_frame)
        button_frame.pack(fill="x", padx=10, pady=5)
        
        def check_device():
            try:
                import subprocess
                result = subprocess.run(
                    ["platform-tools\\adb.exe", "devices"],
                    capture_output=True,
                    text=True,
                    encoding='utf-8'
                )
                
                lines = result.stdout.strip().splitlines()
                if len(lines) <= 1:
                    status_label.configure(
                        text="❌ 未检测到设备连接",
                        text_color="red"
                    )
                    return False
                
                connected_devices = []
                for line in lines[1:]:  
                    if line.strip() and '\tdevice' in line:
                        device_id = line.split('\t')[0]
                        connected_devices.append(device_id)
                
                if connected_devices:
                    status_label.configure(
                        text=f"✅ 已连接设备: {', '.join(connected_devices)}",
                        text_color="green"
                    )
                    return True
                else:
                    status_label.configure(
                        text="⚠️ 设备未授权，请检查USB调试授权",
                        text_color="orange"
                    )
                    return False
                    
            except Exception as e:
                status_label.configure(
                    text=f"❌ 检测失败: {str(e)}",
                    text_color="red"
                )
                return False
        
        def execute_command():
            command = command_entry.get().strip()
            if not command:
                return
            
            command_entry.delete(0, "end")
            
            output_text.insert("end", f"\n$ {command}\n")
            output_text.see("end")
            
            try:
                import subprocess
                import threading
                
                def run_command():
                    try:
                        result = subprocess.run(
                            ["platform-tools\\adb.exe", "shell", command],
                            capture_output=True,
                            text=True,
                            encoding='utf-8',
                            timeout=30  # 30秒超时
                        )
                        
                        terminal_window.after(0, lambda: update_output(result))
                        
                    except subprocess.TimeoutExpired:
                        terminal_window.after(0, lambda: output_text.insert("end", "命令执行超时\n"))
                        terminal_window.after(0, lambda: output_text.see("end"))
                    except Exception as e:
                        terminal_window.after(0, lambda: output_text.insert("end", f"执行错误: {str(e)}\n"))
                        terminal_window.after(0, lambda: output_text.see("end"))
                
                threading.Thread(target=run_command, daemon=True).start()
                
            except Exception as e:
                output_text.insert("end", f"执行错误: {str(e)}\n")
                output_text.see("end")
        
        def update_output(result):
            if result.stdout:
                output_text.insert("end", result.stdout)
            if result.stderr:
                output_text.insert("end", f"错误: {result.stderr}")
            output_text.insert("end", "\n")
            output_text.see("end")
        
        def clear_output():
            output_text.delete("1.0", "end")
        
        def get_device_info():
            commands = [
                "getprop ro.product.model",
                "getprop ro.build.version.release",
                "getprop ro.build.version.sdk",
                "whoami",
                "pwd"
            ]
            
            output_text.insert("end", "=== 设备信息 ===\n")
            for cmd in commands:
                output_text.insert("end", f"$ {cmd}\n")
                try:
                    import subprocess
                    result = subprocess.run(
                        ["platform-tools\\adb.exe", "shell", cmd],
                        capture_output=True,
                        text=True,
                        encoding='utf-8',
                        timeout=5
                    )
                    if result.stdout.strip():
                        output_text.insert("end", result.stdout.strip() + "\n")
                    else:
                        output_text.insert("end", "(无输出)\n")
                except Exception as e:
                    output_text.insert("end", f"错误: {str(e)}\n")
            output_text.insert("end", "==============\n\n")
            output_text.see("end")
        
        customtkinter.CTkButton(
            button_frame,
            text="执行命令",
            command=execute_command,
            width=100,
            height=35,
            font=("微软雅黑", 12)
        ).pack(side="left", padx=5)
        
        customtkinter.CTkButton(
            button_frame,
            text="设备信息",
            command=get_device_info,
            width=100,
            height=35,
            font=("微软雅黑", 12)
        ).pack(side="left", padx=5)
        
        customtkinter.CTkButton(
            button_frame,
            text="刷新状态",
            command=check_device,
            width=100,
            height=35,
            font=("微软雅黑", 12)
        ).pack(side="left", padx=5)
        
        customtkinter.CTkButton(
            button_frame,
            text="清空输出",
            command=clear_output,
            width=100,
            height=35,
            font=("微软雅黑", 12)
        ).pack(side="left", padx=5)
        
        command_entry.bind("<Return>", lambda event: execute_command())
        
        check_device()
        
        help_text = """
=== 使用说明 ===
1. 确保设备已连接并开启USB调试
2. 在输入框中输入shell命令
3. 按回车键或点击"执行命令"按钮
4. 常用命令示例:
   - ls: 列出文件
   - pwd: 显示当前目录
   - cat /proc/version: 查看系统版本
   - getprop: 查看系统属性
   - pm list packages: 列出已安装应用
   - dumpsys: 查看系统服务信息
================
"""
        output_text.insert("end", help_text)
        output_text.see("end")
        
        self.add_log("打开安卓Shell终端")

    def show_command_tool(self):
        """显示自定义命令工具界面"""
        from functions.other_tools import OtherTools
        other_tools = OtherTools(self)
        other_tools.show_command_tool()

    def launch_rustdesk(self):
        import os
        import webbrowser
        import requests
        exe_path = os.path.join("tools", "RustDesk.exe")
        if os.path.exists(exe_path):
            os.startfile(exe_path)
        else:
            if not os.path.exists("tools"):
                os.makedirs("tools", exist_ok=True)
            from tkinter import messagebox
            try:
                messagebox.showinfo(
                    "RustDesk未找到",
                    "未检测到 tools/RustDesk.exe，正在自动下载..."
                )
                url = "https://zyz.yulovehan.top/d/1/rustdesk.exe"
                resp = requests.get(url, stream=True, timeout=30)
                total = int(resp.headers.get('content-length', 0))
                with open(exe_path, 'wb') as f:
                    downloaded = 0
                    for chunk in resp.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                if os.path.exists(exe_path) and os.path.getsize(exe_path) > 1024*1024:
                    messagebox.showinfo("下载完成", "RustDesk已下载，正在启动...")
                    os.startfile(exe_path)
                    return
                else:
                    raise Exception("下载文件异常或过小")
            except Exception as e:
                messagebox.showinfo(
                    "RustDesk下载失败",
                    f"自动下载失败: {str(e)}\n将打开RustDesk官网下载页面，请手动下载并放入tools目录。"
                )
                webbrowser.open("https://rustdesk.com/zh/")

    def show_oplus_flash(self):
        from functions.oplus_flash_logic import OplusFlashLogic
        logic = OplusFlashLogic(self)
        logic.show_menu()

if __name__ == "__main__":
    import subprocess
    from functions.loading_animation import LoadingAnimation
    import shutil
    import tkinter.messagebox as messagebox

    def kill_adb_fastboot(log_func):
        for proc_name in ["adb.exe", "fastboot.exe"]:
            try:
                subprocess.run(["taskkill", "/F", "/IM", proc_name], capture_output=True)
                log_func(f"已结束进程: {proc_name}")
            except Exception as e:
                log_func(f"结束进程{proc_name}失败: {e}")

    def check_disk_space_with_log(log_func):
        import os
        system_drive = os.environ.get('SystemDrive', 'C:')
        sys_total, sys_used, sys_free = shutil.disk_usage(system_drive + '\\')
        sys_free_gb = sys_free / (1024 ** 3)
        if sys_free_gb < 2:
            log_func(f"系统盘({system_drive})剩余空间不足：{sys_free_gb:.2f}GB")
            messagebox.showerror("磁盘空间不足", f"系统盘({system_drive})剩余空间仅 {sys_free_gb:.2f}GB，建议至少保留2GB空间！")
        else:
            log_func(f"系统盘({system_drive})剩余空间：{sys_free_gb:.2f}GB")
        exe_path = os.path.abspath(sys.argv[0])
        program_drive = os.path.splitdrive(exe_path)[0] + '\\'
        prog_total, prog_used, prog_free = shutil.disk_usage(program_drive)
        prog_free_gb = prog_free / (1024 ** 3)
        if prog_free_gb < 2:
            log_func(f"工具箱所在盘({program_drive})剩余空间不足：{prog_free_gb:.2f}GB")
            messagebox.showerror("磁盘空间不足", f"工具箱所在盘({program_drive})剩余空间仅 {prog_free_gb:.2f}GB，建议至少保留2GB空间！")
        else:
            log_func(f"工具箱所在盘({program_drive})剩余空间：{prog_free_gb:.2f}GB")

    loading = LoadingAnimation()
    loading.run_with_checks(lambda: check_disk_space_with_log(print))
    app = App()
    app.mainloop()