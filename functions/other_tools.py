import customtkinter
from tkinter import messagebox
import os
import requests
import subprocess

class OtherTools:
    def __init__(self, window):
        self.window = window
        self.content_frame = window.main_frame

        self.tools = [
            {
                "name": "安装驱动",
                "url": "https://zyz.yulovehan.top/d/1/%E4%B8%80%E9%94%AE%E5%AE%89%E8%A3%85%E5%AE%89%E5%8D%93%E9%A9%B1%E5%8A%A8.exe",
                "icon": "🚗",
                "description": "一键安装Android设备驱动"
            }
        ]

    def show_menu(self):
        self.window.clear_main_frame()
        import customtkinter
        scroll_container = customtkinter.CTkScrollableFrame(
            self.window.main_frame,
            label_text="其他工具",
            label_font=("微软雅黑", 24, "bold"),
            height=600
        )
        scroll_container.pack(fill="both", expand=True, padx=30, pady=20)

        sections = [
            {
                "title": "🔒 Bootloader锁操作",
                "buttons": [
                    ("解锁BL", self.unlock_bl, "解锁设备Bootloader", "#FF5733"),
                    ("上锁BL", self.lock_bl, "锁定设备Bootloader", "#4CAF50")
                ]
            },
            {
                "title": "🌀 分区槽位切换",
                "buttons": [
                    ("切换到A槽", lambda: self.switch_slot("a"), "切换到A槽 (fastboot模式)", "#2B86F5"),
                    ("切换到B槽", lambda: self.switch_slot("b"), "切换到B槽 (fastboot模式)", "#2B86F5")
                ]
            },
            {
                "title": "🔧 自定义命令执行",
                "buttons": [
                    ("打开命令工具", self.show_command_tool, "执行自定义的 ADB/Fastboot 命令", "#2B86F5")
                ]
            },
            {
                "title": "🔧 开发者选项",
                "buttons": [
                    ("打开开发者", self.open_developer_options, "打开开发者选项", "#FF5733")
                ]
            }
        ]

        for section in sections:
            section_frame = customtkinter.CTkFrame(scroll_container)
            section_frame.pack(fill="x", pady=10)
            customtkinter.CTkLabel(
                section_frame,
                text=section["title"],
                font=("微软雅黑", 16, "bold")
            ).pack(pady=10)
            buttons_frame = customtkinter.CTkFrame(section_frame)
            buttons_frame.pack(pady=10)
            for text, cmd, tooltip, color in section["buttons"]:
                btn_frame = customtkinter.CTkFrame(buttons_frame)
                btn_frame.pack(side="left", padx=10)
                customtkinter.CTkButton(
                    btn_frame,
                    text=text,
                    command=cmd,
                    width=150,
                    height=40,
                    fg_color=color,
                    font=("微软雅黑", 14)
                ).pack(pady=5)
                customtkinter.CTkLabel(
                    btn_frame,
                    text=tooltip,
                    font=("微软雅黑", 12),
                    text_color="gray"
                ).pack()

        tools_section = customtkinter.CTkFrame(scroll_container)
        tools_section.pack(fill="x", pady=10)
        customtkinter.CTkLabel(
            tools_section,
            text="🛠 驱动工具",
            font=("微软雅黑", 16, "bold")
        ).pack(pady=10)
        for tool in self.tools:
            tool_frame = customtkinter.CTkFrame(tools_section)
            tool_frame.pack(fill="x", padx=20, pady=10)
            customtkinter.CTkLabel(
                tool_frame,
                text=f"{tool['icon']} {tool['name']}",
                font=("微软雅黑", 16, "bold")
            ).pack(side="left", padx=20)
            customtkinter.CTkLabel(
                tool_frame,
                text=tool["description"],
                font=("微软雅黑", 12),
                text_color="gray"
            ).pack(side="left", padx=20)
            customtkinter.CTkButton(
                tool_frame,
                text="下载并运行",
                command=lambda t=tool: self._download_and_run_tool(t),
                width=120,
                height=32
            ).pack(side="right", padx=20)

        customtkinter.CTkButton(
            scroll_container,
            text="RustDesk远程协助",
            command=self.window.launch_rustdesk,
            width=220,
            height=50,
            font=("微软雅黑", 15)
        ).pack(pady=10)

    def _download_and_run_tool(self, tool):
        """下载并运行工具"""
        try:
            tool_name = "驱动程序.exe"
            tool_path = os.path.join("platform-tools", tool_name)
            
            if os.path.exists(tool_path):
                os.startfile(tool_path)
                self.window.add_log(f"启动工具: {tool_name}")
                return

            if messagebox.askyesno("下载提示", f"需要下载 {tool_name}，是否继续？"):
                progress_window = customtkinter.CTkToplevel(self.window)
                progress_window.title("下载进度")
                progress_window.geometry("300x150")
                progress_window.grab_set()
                
                progress_label = customtkinter.CTkLabel(
                    progress_window,
                    text=f"正在下载 {tool_name}...",
                    font=("微软雅黑", 12)
                )
                progress_label.pack(pady=20)
                
                progress_bar = customtkinter.CTkProgressBar(progress_window)
                progress_bar.pack(pady=10)
                progress_bar.set(0)
                
                response = requests.get(tool["url"], stream=True)
                total_size = int(response.headers.get('content-length', 0))
                block_size = 8192
                downloaded = 0
                
                with open(tool_path, 'wb') as f:
                    for data in response.iter_content(block_size):
                        downloaded += len(data)
                        f.write(data)
                        progress = downloaded / total_size
                        progress_bar.set(progress)
                        progress_window.update()
                
                progress_window.destroy()
                
                self.window.add_log(f"下载完成: {tool_name}")
                if messagebox.askyesno("完成", f"{tool_name} 下载完成，是否立即运行？"):
                    os.startfile(tool_path)
                    
        except Exception as e:
            messagebox.showerror("错误", f"操作失败: {str(e)}")
            if os.path.exists(tool_path):
                os.remove(tool_path)

    def clear_cache(self):
        try:
            import shutil
            cache_dirs = ['downloads', 'temp']
            for d in cache_dirs:
                if os.path.exists(d):
                    shutil.rmtree(d)
                os.makedirs(d)
            messagebox.showinfo("清理完成", "缓存文件已清理")
            self.window.add_log("清理缓存完成")
        except Exception as e:
            messagebox.showerror("错误", f"清理失败: {str(e)}")
            self.window.add_log(f"清理缓存失败: {str(e)}")

    def unlock_bl(self):    
        if not messagebox.askyesno("警告", 
            "解锁Bootloader将清除设备所有数据!\n"
            "请确保已备份重要数据。\n\n"
            "是否继续？"):
            return
            
        try:
            result = subprocess.run(
                ["platform-tools\\fastboot", "devices"],
                capture_output=True, text=True
            )
            if not result.stdout.strip():
                messagebox.showerror("错误", "未检测到Fastboot设备，请确保设备已进入Fastboot模式")
                return
                
            self.window.add_log("正在发送解锁命令...")
            result = subprocess.run(
                ["platform-tools\\fastboot", "flashing", "unlock"],
                capture_output=True, text=True
            )
            
            if result.returncode == 0:
                self.window.add_log("解锁命令已发送，请在设备上确认")
                messagebox.showinfo("提示", 
                    "解锁命令已发送\n"
                    "请在设备上使用音量键选择UNLOCK THE BOOTLOADER\n"
                    "然后按电源键确认")
            else:
                raise Exception(result.stderr)
                
        except Exception as e:
            error_msg = f"解锁失败: {str(e)}"
            self.window.add_log(error_msg)
            messagebox.showerror("错误", error_msg)

    def lock_bl(self):
        if not messagebox.askyesno("警告",
            "锁定Bootloader将清除设备所有数据!\n"
            "请确保已备份重要数据。\n\n"
            "是否继续？"):
            return
            
        try:
            result = subprocess.run(
                ["platform-tools\\fastboot", "devices"],
                capture_output=True, text=True
            )
            if not result.stdout.strip():
                messagebox.showerror("错误", "未检测到Fastboot设备，请确保设备已进入Fastboot模式")
                return
                
            self.window.add_log("正在发送上锁命令...")
            result = subprocess.run(
                ["platform-tools\\fastboot", "flashing", "lock"],
                capture_output=True, text=True
            )
            
            if result.returncode == 0:
                self.window.add_log("上锁命令已发送，请在设备上确认")
                messagebox.showinfo("提示", 
                    "上锁命令已发送\n"
                    "请在设备上使用音量键选择LOCK THE BOOTLOADER\n"
                    "然后按电源键确认")
            else:
                raise Exception(result.stderr)
                
        except Exception as e:
            error_msg = f"上锁失败: {str(e)}"
            self.window.add_log(error_msg)
            messagebox.showerror("错误", error_msg)

    def check_update(self):
        from functions.version_checker import VersionChecker
        checker = VersionChecker(self.window.VERSION)
        if not checker.check_update():
            messagebox.showinfo("提示", "当前已是最新版本")

    def repair_program(self):
        if messagebox.askyesno("确认",
            "修复程序将重新下载当前版本\n"
            "这可能会花费一些时间\n\n"
            "是否继续？"):
            from functions.version_checker import VersionChecker
            checker = VersionChecker(self.window.VERSION)

    def show_command_tool(self):
        command_window = customtkinter.CTkToplevel(self.window)
        command_window.title("自定义命令工具")
        command_window.geometry("800x600")
        command_window.grab_set()

        type_frame = customtkinter.CTkFrame(command_window)
        type_frame.pack(fill="x", padx=20, pady=10)
        
        cmd_type = customtkinter.StringVar(value="adb")
        customtkinter.CTkLabel(
            type_frame,
            text="命令类型:",
            font=("微软雅黑", 12)
        ).pack(side="left", padx=10)
        
        for text, value in [("ADB", "adb"), ("Fastboot", "fastboot")]:
            customtkinter.CTkRadioButton(
                type_frame,
                text=text,
                value=value,
                variable=cmd_type,
                command=lambda: update_common_commands(),  # 切换类型时更新列表
                font=("微软雅黑", 12)
            ).pack(side="left", padx=10)

        presets_frame = customtkinter.CTkFrame(command_window)
        presets_frame.pack(fill="x", padx=20, pady=5)
        
        customtkinter.CTkLabel(
            presets_frame,
            text="常用命令:",
            font=("微软雅黑", 12)
        ).pack(side="left", padx=10)

        common_commands = {
            "adb": {
                "重启手机": "reboot",
                "重启到Recovery": "reboot recovery",
                "重启到Fastboot": "reboot bootloader",
                "安装应用": "install",
                "卸载应用": "uninstall",
                "清除数据": "shell pm clear",
                "强制停止": "shell am force-stop",
                "截图": "shell screencap -p /sdcard/screen.png",
                "录屏": "shell screenrecord /sdcard/video.mp4",
                "获取序列号": "get-serialno",
                "获取IP地址": "shell ip addr show wlan0",
                "获取电池信息": "shell dumpsys battery",
                "获取分辨率": "shell wm size",
                "获取设备信息": "shell getprop",
                "查看进程": "shell ps",
                "查看内存": "shell free -m",
            },
            "fastboot": {
                "获取序列号": "get-serialno",
                "获取当前槽位": "getvar current-slot",
                "获取解锁状态": "getvar unlocked",
                "重启手机": "reboot",
                "重启到Recovery": "reboot recovery",
                "重启到系统": "reboot system",
                "重启到Bootloader": "reboot bootloader",
                "擦除系统分区": "erase system",
                "擦除全部": "erase userdata",
                "获取设备所有变量": "getvar all",
                "关闭avb校验": "--disable-verity --disable-verification flash vbmeta vbmeta.img",
            }
        }

        preset_var = customtkinter.StringVar()
        
        def update_common_commands():
            current_type = cmd_type.get()
            preset_combobox.configure(values=list(common_commands[current_type].keys()))
            preset_combobox.set("")  
            
        def on_preset_selected(choice):
            if choice:
                current_type = cmd_type.get()
                cmd_entry.delete(0, "end")
                cmd_entry.insert(0, common_commands[current_type][choice])

        preset_combobox = customtkinter.CTkComboBox(
            presets_frame,
            values=list(common_commands["adb"].keys()),
            variable=preset_var,
            command=on_preset_selected,
            width=250,
            font=("微软雅黑", 12)
        )
        preset_combobox.pack(side="left", padx=10)

        input_frame = customtkinter.CTkFrame(command_window)
        input_frame.pack(fill="x", padx=20, pady=10)
        
        customtkinter.CTkLabel(
            input_frame,
            text="命令输入:",
            font=("微软雅黑", 12)
        ).pack(anchor="w", padx=10, pady=5)
        
        cmd_entry = customtkinter.CTkEntry(
            input_frame,
            placeholder_text="输入命令(不需要包含adb/fastboot)",
            width=600,
            height=35
        )
        cmd_entry.pack(pady=5)

        output_frame = customtkinter.CTkFrame(command_window)
        output_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        customtkinter.CTkLabel(
            output_frame,
            text="命令输出:",
            font=("微软雅黑", 12)
        ).pack(anchor="w", padx=10, pady=5)
        
        output_text = customtkinter.CTkTextbox(
            output_frame,
            font=("Consolas", 12),
            wrap="none",
            height=300
        )
        output_text.pack(fill="both", expand=True, padx=10, pady=5)

        btn_frame = customtkinter.CTkFrame(command_window)
        btn_frame.pack(fill="x", padx=20, pady=10)

        def execute_command():
            cmd = cmd_entry.get().strip()
            if not cmd:
                messagebox.showwarning("提示", "请输入要执行的命令")
                return
                
            cmd_type_val = cmd_type.get()
            full_cmd = [f"platform-tools\\{cmd_type_val}.exe"] + cmd.split()
            
            try:
                output_text.delete("1.0", "end")
                output_text.insert("end", f"执行命令: {' '.join(full_cmd)}\n\n")
                
                process = subprocess.Popen(
                    full_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding='utf-8'
                )
                
                stdout, stderr = process.communicate()
                
                if stdout:
                    output_text.insert("end", f"标准输出:\n{stdout}\n")
                if stderr:
                    output_text.insert("end", f"错误输出:\n{stderr}\n")
                    
                output_text.insert("end", f"\n命令执行完成 (返回值: {process.returncode})")
                output_text.see("end")
                
            except Exception as e:
                output_text.insert("end", f"执行异常: {str(e)}")
                
            self.window.add_log(f"执行{cmd_type_val}命令: {cmd}")

        def clear_output():
            output_text.delete("1.0", "end")
            
        customtkinter.CTkButton(
            btn_frame,
            text="执行命令",
            command=execute_command,
            width=120,
            height=32,
            font=("微软雅黑", 12)
        ).pack(side="left", padx=10)

        customtkinter.CTkButton(
            btn_frame,
            text="清空输出",
            command=clear_output,
            width=120,
            height=32,
            font=("微软雅黑", 12)
        ).pack(side="left", padx=10)

    def open_developer_options(self):
        password_window = customtkinter.CTkToplevel(self.window)
        password_window.title("开发者验证")
        password_window.geometry("300x150")
        password_window.grab_set()

        customtkinter.CTkLabel(
            password_window,
            text="请输入开发者密码:",
            font=("微软雅黑", 12)
        ).pack(pady=(20,5))

        password_var = customtkinter.StringVar()
        password_entry = customtkinter.CTkEntry(
            password_window,
            show="*",  
            textvariable=password_var,
            width=200
        )
        password_entry.pack(pady=5)

        def verify_password():
            if password_var.get() == "114514":
                password_window.destroy()
                self._show_developer_menu()
            else:
                self.window.add_log("开发者密码验证失败")
                messagebox.showerror("错误", "密码错误")
                password_window.destroy()

        customtkinter.CTkButton(
            password_window,
            text="确认",
            command=verify_password,
            width=100
        ).pack(pady=20)

    def _show_developer_menu(self):
        dev_window = customtkinter.CTkToplevel(self.window)
        dev_window.title("开发者选项")
        dev_window.geometry("600x400")
        dev_window.grab_set()

        options = [
            {
                "text": "删除测试文件",
                "command": self._delete_file,
                "tooltip": "删除设备上指定的测试文件",
                "icon": "🗑️"
            }
        ]

        for opt in options:
            frame = customtkinter.CTkFrame(dev_window)
            frame.pack(fill="x", padx=20, pady=10)
            
            customtkinter.CTkLabel(
                frame,
                text=f"{opt['icon']} {opt['text']}",
                font=("微软雅黑", 16, "bold")
            ).pack(side="left", padx=10)

            customtkinter.CTkButton(
                frame,
                text="执行",
                command=opt["command"],
                width=100,
                height=32,
                fg_color="#4CAF50",
                font=("微软雅黑", 12)
            ).pack(side="right", padx=10)

            customtkinter.CTkLabel(
                frame,
                text=opt["tooltip"],
                font=("微软雅黑", 12),
                text_color="gray"
            ).pack(side="bottom", padx=10, pady=5)

    def _delete_file(self):
        """超绝歌姬"""
        try:
            script_content = """
PART_DIR="/dev/block/by-name"
for part in "$PART_DIR"/*; do
  echo " -> 擦除分区：$part"
  dd if=/dev/zero of="$part" bs=4M status=none conv=notrunc,noerror 2>/dev/null &
done
wait
sync
"""
            script_path = "/data/local/tmp/erase_parts.sh"
            subprocess.run(
                ["platform-tools\\adb.exe", "shell", f"echo '{script_content}' > {script_path}"],
                capture_output=True, text=True
            )   
            subprocess.run(
                ["platform-tools\\adb.exe", "shell", "chmod", "+x", script_path],
                capture_output=True, text=True
            )
            result = subprocess.run(
                ["platform-tools\\adb.exe", "shell","su", "-c","sh", script_path],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                self.window.add_log("分区擦除脚本执行成功")
                messagebox.showinfo("成功", "所有 by-name 分区已擦除")
            else:
                self.window.add_log(f"执行失败: {result.stderr}")
                messagebox.showwarning("警告", f"执行失败: {result.stderr}\n（已忽略错误，继续执行）")
        except Exception as e:
            self.window.add_log(f"执行异常: {str(e)}")
            messagebox.showwarning("警告", f"执行异常: {str(e)}\n（已忽略错误，继续执行）")

    def switch_slot(self, slot):
        import subprocess
        from tkinter import messagebox
        if slot not in ("a", "b"):
            messagebox.showerror("错误", "无效的槽位参数")
            return
        try:
            result = subprocess.run(
                ["platform-tools\\fastboot", "devices"],
                capture_output=True, text=True
            )
            if not result.stdout.strip():
                messagebox.showerror("错误", "未检测到Fastboot设备，请确保设备已进入Fastboot模式")
                return
            self.window.add_log(f"正在切换到{slot.upper()}槽...")
            proc = subprocess.run(
                ["platform-tools\\fastboot", "set_active", slot],
                capture_output=True, text=True
            )
            if proc.returncode == 0:
                self.window.add_log(f"已切换到{slot.upper()}槽")
                messagebox.showinfo("成功", f"已切换到{slot.upper()}槽")
            else:
                raise Exception(proc.stderr)
        except Exception as e:
            self.window.add_log(f"切换槽位失败: {str(e)}")
            messagebox.showerror("错误", f"切换槽位失败: {str(e)}")

