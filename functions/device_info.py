import tkinter as tk
from tkinter import ttk
import subprocess
import threading
import queue
import customtkinter
import requests
from functions.reboot_tools import RebootTools

class DeviceInfoBar:
    def __init__(self, root):
        self.root = root
        self.status_frame = tk.Frame(root, relief=tk.SUNKEN, bd=1)
        self.status_frame.grid(row=1, column=0, columnspan=3, sticky="ew", padx=5)
        
        self.status_label = tk.Label(
            self.status_frame,
            text="正在检测设备...",
            anchor=tk.W,
            padx=10,
            font=("微软雅黑", 9)
        )
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.reboot_btn_frame = tk.Frame(self.status_frame)
        self.reboot_btn_frame.pack(side=tk.RIGHT, padx=5)
        
        self.ctk_reboot_btns = []
        btn_cfg = [
            ("重启系统", "system"),
            ("重启Recovery", "recovery"),
            ("重启Bootloader", "bootloader"),
            ("重启Fastbootd", "fastbootd")
        ]
        for text, mode in btn_cfg:
            btn = customtkinter.CTkButton(
                master=self.reboot_btn_frame,
                text=text,
                width=100,
                height=24,
                font=("微软雅黑", 10),
                command=lambda m=mode: RebootTools().reboot(self.root, m)
            )
            btn.pack(side=tk.LEFT, padx=2)
            self.ctk_reboot_btns.append(btn)
        
        self.driver_btn_frame = tk.Frame(self.status_frame)
        self.driver_btn = customtkinter.CTkButton(
            master=self.driver_btn_frame,
            text="安装驱动",
            width=80,
            height=24,
            font=("微软雅黑", 10),
            command=self.install_driver
        )
        self.driver_btn.pack(side=tk.LEFT, padx=2)
        self.driver_btn_frame.pack_forget()
        
        self.arrow_frame = tk.Frame(self.status_frame)
        self.arrow_label = tk.Label(
            self.arrow_frame,
            text="➡",
            font=("微软雅黑", 24),
            fg="orange",
            bg=self.status_frame.cget("bg")
        )
        self.arrow_label.pack(side=tk.RIGHT, padx=5)
        self.arrow_frame.pack_forget()
        
        self.scrcpy_btn_frame = tk.Frame(self.status_frame)
        self.scrcpy_btn = customtkinter.CTkButton(
            master=self.scrcpy_btn_frame,
            text="🎥 投屏",
            width=80,
            height=24,
            font=("微软雅黑", 10),
            command=self.show_scrcpy
        )
        self.scrcpy_btn.pack(side=tk.LEFT, padx=2)
        self.scrcpy_btn_frame.pack_forget()
        
        self.update_queue = queue.Queue()
        self.stop_flag = False
        
        self.device_ever_detected = False
        
        self.unlock_asked = False
        
        self.detector_thread = threading.Thread(target=self._device_monitor, daemon=True)
        self.detector_thread.start()
        
        self._check_queue()
        
        self.root.after(1000, self._initial_device_check)
        
        self.root.bind_all("<Destroy>", self._on_destroy)
    
    def install_driver(self):
        try:
            import os
            import requests
            from tkinter import messagebox
            
            tool_name = "驱动程序.exe"
            tool_path = os.path.join("platform-tools", tool_name)
            
            if os.path.exists(tool_path):
                os.startfile(tool_path)
                self.root.add_log(f"启动工具: {tool_name}")
                return

            driver_url = "https://zyz.yulovehan.top/d/1/%E4%B8%80%E9%94%AE%E5%AE%89%E8%A3%85%E5%AE%89%E5%8D%93%E9%A9%B1%E5%8A%A8.exe"
            
            if messagebox.askyesno("下载提示", f"需要下载 {tool_name}，是否继续？"):
                progress_window = customtkinter.CTkToplevel(self.root)
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
                
                response = requests.get(driver_url, stream=True)
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
                
                self.root.add_log(f"下载完成: {tool_name}")
                if messagebox.askyesno("完成", f"{tool_name} 下载完成，是否立即运行？"):
                    os.startfile(tool_path)
                    
        except Exception as e:
            self.root.add_log(f"驱动安装失败: {str(e)}")
            if 'tool_path' in locals() and os.path.exists(tool_path):
                os.remove(tool_path)
    
    def show_scrcpy(self):
        try:
            import os
            import subprocess
            from tkinter import messagebox
            
            scrcpy_path = "platform-tools\\scrcpy.exe"
            
            if not os.path.exists(scrcpy_path):
                self.root.add_log("未找到投屏程序 scrcpy.exe，请将 scrcpy.exe 放入 platform-tools 文件夹")
                messagebox.showerror("错误", "未找到投屏程序，请检查文件是否存在")
                return

            result = subprocess.run(
                ["platform-tools\\adb.exe", "devices"],
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            
            if len(result.stdout.strip().splitlines()) <= 1:
                self.root.add_log("未检测到设备连接，请确保设备已连接并开启 USB 调试")
                messagebox.showerror("错误", "未检测到设备连接")
                return

            self.root.add_log("正在启动投屏程序...")
            
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
                    self.root.add_log(f"投屏启动失败: {stderr_output}")
                    messagebox.showerror("错误", f"投屏启动失败: {stderr_output}")
                    return
            except subprocess.TimeoutExpired:
                self.root.add_log("投屏程序已成功启动")
                
        except Exception as e:
            error_msg = f"启动投屏失败: {str(e)}"
            self.root.add_log(error_msg)
            messagebox.showerror("错误", error_msg)
    
    def _device_monitor(self):
        import time, subprocess
        while not self.stop_flag:
            try:
                fb_info = self._get_fastboot_info()
                if fb_info:
                    self.update_queue.put((" | ".join(fb_info), "green"))
                elif self._check_adb_connected():
                    adb_info = self._get_adb_info()
                    ver_result = subprocess.run(
                        ["platform-tools\\adb.exe", "shell", "getprop", "ro.build.display.id"],
                        capture_output=True, text=True
                    )
                    if ver_result.returncode == 0:
                        display_id = ver_result.stdout.strip()
                        adb_info.append(f"系统版本号: {display_id}")
                    self.update_queue.put((" | ".join(adb_info), "green"))
                else:
                    self.update_queue.put(("设备未连接", "red"))
            except Exception as e:
                self.update_queue.put((f"设备检测异常: {str(e)}", "red"))
            time.sleep(3)

    def _check_queue(self):
        try:
            if not self.update_queue.empty():
                text, color = self.update_queue.get_nowait()
                self.status_label.config(text=text, fg=color)

                if "设备未连接" in text or "未检测到设备" in text:
                    self.driver_btn_frame.pack(side=tk.RIGHT, padx=5)
                    self.scrcpy_btn_frame.pack_forget()
                    
                    if not self.device_ever_detected:
                        self.arrow_frame.pack(side=tk.RIGHT, padx=5)
                else:
                    self.device_ever_detected = True
                    self.driver_btn_frame.pack_forget()
                    self.scrcpy_btn_frame.pack(side=tk.RIGHT, padx=5)
                    self.arrow_frame.pack_forget()
                    
        except queue.Empty:
            pass
            
        if not self.stop_flag:
            self.root.after(500, self._check_queue)

    def _initial_device_check(self):
        try:
            if not self._check_adb_connected() and not self._get_fastboot_info():
                if not self.device_ever_detected:
                    self.driver_btn_frame.pack(side=tk.RIGHT, padx=5)
                    self.arrow_frame.pack(side=tk.RIGHT, padx=5)
        except Exception as e:
            if not self.device_ever_detected:
                self.driver_btn_frame.pack(side=tk.RIGHT, padx=5)
                self.arrow_frame.pack(side=tk.RIGHT, padx=5)

    def _on_destroy(self, event):
        if event.widget == self.root:
            self.stop_flag = True

    def update_info(self):
        try:
            fb_info = self._get_fastboot_info()
            if fb_info:
                self.status_label.config(
                    text=" | ".join(fb_info),
                    fg="green"
                )
                
            elif self._check_adb_connected():
                adb_info = self._get_adb_info()
                if adb_info:
                    try:
                        root_result = subprocess.run(
                            ["platform-tools\\adb.exe", "shell", "su", "-c", "id"],
                            capture_output=True, text=True,
                            timeout=1
                        )
                        if "uid=0" in root_result.stdout:   
                            slot_result = subprocess.run(
                                ["platform-tools\\adb.exe", "shell", "getprop", "ro.boot.slot_suffix"],
                                capture_output=True, text=True
                            )
                            slot = slot_result.stdout.strip()
                            if slot in ["_a", "_b"]:
                                adb_info.append(f"Root状态: 已获取 ({slot.upper()[1:]}槽)")
                            else:
                                adb_info.append("Root状态: 已获取")
                        else:
                            adb_info.append("Root状态: 未获取")
                    except:
                        adb_info.append("Root状态: 未获取")
                    
                    self.status_label.config(
                        text=" | ".join(adb_info),
                        fg="green"
                    )
            else:
                self.status_label.config(
                    text="设备未连接",
                    fg="red"
                )
                
        except Exception as e:
            self.status_label.config(
                text=f"设备检测异常: {str(e)}",
                fg="red"
            )
            
        self.root.after(5000, self.update_info)
    
    def _check_adb_connected(self):
        try:
            result = subprocess.run(
                ["platform-tools\\adb.exe", "devices"],
                capture_output=True, text=True
            )
            return len(result.stdout.strip().splitlines()) > 1
        except:
            return False
            
    def _get_adb_info(self):
        info = []
        try:
            prop_result = subprocess.run(
                ["platform-tools\\adb.exe", "shell", "getprop"],
                capture_output=True, text=True,
                encoding='utf-8'
            )
            
            if prop_result.returncode == 0:
                for line in prop_result.stdout.splitlines():
                    if "[ro.product.model]" in line:
                        model = line.split("[")[2].strip("[]")
                        info.append(f"机型: {model}")
                    elif "[ro.build.version.release]" in line:
                        android_ver = line.split("[")[2].strip("[]") 
                        sdk_ver = ""
                        for prop_line in prop_result.stdout.splitlines():
                            if "[ro.build.version.sdk]" in prop_line:
                                sdk_ver = f"(API {prop_line.split('[')[2].strip('[]')})"
                                break
                        info.append(f"安卓: {android_ver}{sdk_ver}")
                        
            battery_result = subprocess.run(
                ["platform-tools\\adb.exe", "shell", "dumpsys", "battery"],
                capture_output=True, text=True,
                encoding='utf-8'
            )
            
            if battery_result.returncode == 0:
                for line in battery_result.stdout.splitlines():
                    if "level:" in line:
                        level = line.split("level:", 1)[1].strip()
                        charging = any("status: 2" in l for l in battery_result.stdout.splitlines())
                        info.append(f"电量: {level}% ({'充电中' if charging else '放电'})")
                        break

            try:
                root_result = subprocess.run(
                    ["platform-tools\\adb.exe", "shell", "su", "-c", "id"],
                    capture_output=True, text=True,
                    timeout=1
                )
                if "uid=0" in root_result.stdout:
                    slot_result = subprocess.run(
                        ["platform-tools\\adb.exe", "shell", "getprop", "ro.boot.slot_suffix"],
                        capture_output=True, text=True
                    )
                    slot = slot_result.stdout.strip()
                    if slot in ["_a", "_b"]:
                        info.append(f"ROOT状态: 已获取({slot.upper()[1:]}槽)")
                    else:
                        info.append("ROOT状态: 已获取")
                else:
                    info.append("ROOT状态: 未获取")
            except:
                info.append("ROOT状态: 未获取")
                        
        except Exception:
            pass
                    
        return info
    
    def _get_fastboot_info(self):
        info = []
        try:
            devices = subprocess.run(
                ["platform-tools\\fastboot", "devices"],
                capture_output=True, text=True
            )
            if not devices.stdout.strip():
                return []
                
            is_userspace = False
            try:
                userspace_result = subprocess.run(
                    ["platform-tools\\fastboot", "getvar", "is-userspace"],
                    capture_output=True, text=True, timeout=3
                )
                if "yes" in (userspace_result.stdout + userspace_result.stderr).lower():
                    is_userspace = True
            except Exception:
                pass
            if is_userspace:
                info.append("Fastbootd模式")
            else:
                info.append("Bootloader(Fastboot)模式")
            
            slot_result = subprocess.run(
                ["platform-tools\\fastboot", "getvar", "current-slot"],
                capture_output=True, text=True
            )
            for line in slot_result.stdout.splitlines() + slot_result.stderr.splitlines():
                if "current-slot:" in line.lower():
                    slot = line.split(":")[-1].strip()
                    if slot in ['a', 'b']:
                        info.append(f"AB分区({slot.upper()}槽)")
                        break
            else:
                info.append("单分区")
                
            unlock_result = subprocess.run(
                ["platform-tools\\fastboot", "oem", "device-info"],
                capture_output=True, text=True
            )
            output = unlock_result.stdout + unlock_result.stderr
            if "Device unlocked: true" in output:
                info.append("已解锁")
            elif "Device unlocked: false" in output:
                info.append("未解锁")   
                if not self.unlock_asked:
                    self.unlock_asked = True
                    self.root.after(0, self._ask_unlock)
            return info
        except Exception:
            if devices.stdout.strip():
                return ["Fastboot模式 (已连接)"]
            return []
    
    def _ask_unlock(self):
        try:
            from tkinter import messagebox
            
            result = messagebox.askyesno(
                "设备解锁",
                "检测到您的设备处于Fastboot模式且未解锁。\n\n"
                "解锁设备可以：\n"
                "• 刷入第三方Recovery\n"
                "• 安装Magisk获取ROOT权限\n"
                "• 刷入第三方ROM\n\n"
                "⚠️ 警告：解锁会清除设备所有数据！\n\n"
                "是否现在解锁设备？"
            )
            
            if result:
                self.root.add_log("用户选择解锁设备，正在执行解锁命令...")
                self._execute_unlock()
            else:
                self.root.add_log("用户取消解锁操作")
                
        except Exception as e:
            self.root.add_log(f"解锁询问失败: {str(e)}")
    
    def _execute_unlock(self):
        try:
            import subprocess
            from tkinter import messagebox
            
            result = subprocess.run(
                ["platform-tools\\fastboot.exe", "flash", "unlock"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                self.root.add_log("解锁命令执行成功")
                messagebox.showinfo(
                    "解锁成功", 
                    "设备解锁命令已执行成功！\n\n"
                    "请在设备上确认解锁操作，然后设备将自动重启。\n"
                    "解锁完成后，您就可以进行刷机等操作了。"
                )
            else:
                error_msg = result.stderr if result.stderr else "未知错误"
                self.root.add_log(f"解锁命令执行失败: {error_msg}")
                messagebox.showerror(
                    "解锁失败",
                    f"解锁命令执行失败:\n{error_msg}\n\n"
                    "请检查设备是否支持解锁，或尝试手动解锁。"
                )
                
        except subprocess.TimeoutExpired:
            self.root.add_log("解锁命令执行超时")
            messagebox.showerror(
                "解锁超时",
                "解锁命令执行超时，请检查设备连接状态。"
            )
        except Exception as e:
            self.root.add_log(f"解锁执行异常: {str(e)}")
            messagebox.showerror(
                "解锁异常",
                f"解锁过程中发生异常:\n{str(e)}"
            )
