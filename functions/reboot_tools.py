import customtkinter
from tkinter import messagebox

class RebootTools:
    def __init__(self):
        pass

    def reboot(self, window, mode="system"):
        """执行重启命令"""
        import subprocess
        try:
            window.add_log(f"正在执行重启到{mode}模式...")

            if mode == "system":
                adb_cmd = ["platform-tools\\adb.exe", "reboot"]
            elif mode == "bootloader":
                adb_cmd = ["platform-tools\\adb.exe", "reboot", "bootloader"]
            elif mode == "recovery":
                adb_cmd = ["platform-tools\\adb.exe", "reboot", "recovery"]
            elif mode == "edl":
                adb_cmd = ["platform-tools\\adb.exe", "reboot", "edl"]
            elif mode == "shutdown":
                adb_cmd = ["platform-tools\\adb.exe", "shell", "reboot", "-p"]
            elif mode == "fastboot":
                adb_cmd = ["platform-tools\\adb.exe", "reboot", "fastboot"]
            else:
                adb_cmd = ["platform-tools\\adb.exe", "reboot"]

            try:
                adb_result = subprocess.run(adb_cmd, capture_output=True, timeout=1)
                if adb_result.returncode == 0:
                    window.add_log("重启命令发送成功")
            except:
                pass

            if mode == "system":
                fb_cmd = ["platform-tools\\fastboot", "reboot"]
            elif mode == "bootloader":
                fb_cmd = ["platform-tools\\fastboot", "reboot-bootloader"]
            elif mode == "recovery":
                fb_cmd = ["platform-tools\\fastboot", "reboot", "recovery"]
            elif mode == "edl":
                fb_cmd = ["platform-tools\\fastboot", "reboot", "edl"]
            elif mode == "fastboot":
                fb_cmd = ["platform-tools\\fastboot", "reboot", "fastboot"]
            elif mode == "shutdown":
                fb_cmd = ["platform-tools\\fastboot", "oem", "poweroff"]
            else:
                fb_cmd = ["platform-tools\\fastboot", "reboot"]

            try:
                subprocess.run(fb_cmd, capture_output=True, timeout=1)
            except:
                pass

            messagebox.showinfo("成功", f"已发送{mode}重启命令")
            window.add_log(f"重启到{mode}模式的命令已执行完成")

        except Exception as e:
            error_msg = f"执行异常: {str(e)}"
            window.add_log(f"重启失败 - {error_msg}")
            messagebox.showerror("错误", error_msg)

    def show_menu(self, window):
        """显示重启选项菜单"""
        window.clear_main_frame()
        
        customtkinter.CTkLabel(
            window.main_frame,
            text="重启选项",
            font=("微软雅黑", 24, "bold")
        ).pack(pady=20)

        buttons_frame = customtkinter.CTkFrame(window.main_frame)
        buttons_frame.pack(fill="both", expand=True, padx=30, pady=20)
        
        buttons_frame.grid_columnconfigure(0, weight=1)
        buttons_frame.grid_columnconfigure(1, weight=1)
        
        options = [
            ("重启到系统", "system", "🔄 正常重启到系统"),
            ("重启到Bootloader", "bootloader", "⚡ 重启到引导模式"),
            ("重启到Fastboot", "fastboot", "📱 重启到线刷模式"),
            ("重启到Recovery", "recovery", "🔧 重启到恢复模式"),
            ("重启到EDL", "edl", "🛠 重启到9008下载模式"),
            ("正常关机", "shutdown", "⭕ 关闭设备电源")
        ]

        for index, (text, mode, tooltip) in enumerate(options):
            row = index // 2
            col = index % 2

            button = customtkinter.CTkButton(
                buttons_frame,
                text=text,
                command=lambda m=mode: self.reboot(window, m),  
                width=200,
                height=60,
                font=("微软雅黑", 14)
            )
            button.grid(row=row*2, column=col, padx=15, pady=15, sticky="nsew")

            customtkinter.CTkLabel(
                buttons_frame,
                text=tooltip,
                font=("微软雅黑", 12),
                text_color="gray"
            ).grid(row=row*2+1, column=col, pady=(0, 15))

        window.add_log("已打开重启选项菜单")
