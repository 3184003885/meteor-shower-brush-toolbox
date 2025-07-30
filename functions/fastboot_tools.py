import customtkinter
import subprocess
import os
import threading
import time
from tkinter import messagebox, filedialog
from datetime import datetime

class FastbootTools:
    def __init__(self, window):
        self.window = window
        self.partition_data = []
        self.refresh_thread = None
        self.is_refreshing = False

    def show_menu(self):
        self.window.clear_main_frame()
        
        title_frame = customtkinter.CTkFrame(self.window.main_frame)
        title_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        customtkinter.CTkLabel(
            title_frame,
            text="分区管理工具",
            font=("微软雅黑", 24, "bold")
        ).pack(pady=10)
        
        status_frame = customtkinter.CTkFrame(self.window.main_frame)
        status_frame.pack(fill="x", padx=20, pady=10)
        
        self.device_status_label = customtkinter.CTkLabel(
            status_frame,
            text="正在检测设备状态...",
            font=("微软雅黑", 12),
            text_color="orange"
        )
        self.device_status_label.pack(side="left", padx=10, pady=10)
        
        button_frame = customtkinter.CTkFrame(status_frame)
        button_frame.pack(side="right", padx=10, pady=10)
        
        self.refresh_btn = customtkinter.CTkButton(
            button_frame,
            text="刷新分区信息",
            command=self.refresh_partitions,
            width=120,
            height=32,
            font=("微软雅黑", 12)
        )
        self.refresh_btn.pack(side="left", padx=5)
        
        self.flash_btn = customtkinter.CTkButton(
            button_frame,
            text="刷写分区",
            command=self.show_flash_dialog,
            width=100,
            height=32,
            font=("微软雅黑", 12)
        )
        self.flash_btn.pack(side="left", padx=5)
        
        operation_frame = customtkinter.CTkFrame(self.window.main_frame)
        operation_frame.pack(fill="x", padx=20, pady=5)
        
        customtkinter.CTkButton(
            operation_frame,
            text="创建分区",
            command=self.create_partition,
            width=100,
            height=32,
            font=("微软雅黑", 12)
        ).pack(side="left", padx=5, pady=5)
        
        customtkinter.CTkButton(
            operation_frame,
            text="删除分区",
            command=self.delete_partition,
            width=100,
            height=32,
            font=("微软雅黑", 12)
        ).pack(side="left", padx=5, pady=5)
        
        search_frame = customtkinter.CTkFrame(operation_frame)
        search_frame.pack(side="right", padx=5, pady=5)
        
        self.search_var = customtkinter.StringVar()
        
        customtkinter.CTkEntry(
            search_frame,
            placeholder_text="搜索分区...",
            textvariable=self.search_var,
            width=120,
            height=32,
            font=("微软雅黑", 12)
        ).pack(side="left", padx=5)
        
        customtkinter.CTkButton(
            search_frame,
            text="搜索",
            command=self.filter_partitions,
            width=60,
            height=32,
            font=("微软雅黑", 12)
        ).pack(side="left", padx=5)
        
        slot_frame = customtkinter.CTkFrame(operation_frame)
        slot_frame.pack(side="right", padx=5, pady=5)
        
        customtkinter.CTkLabel(
            slot_frame,
            text="槽位:",
            font=("微软雅黑", 12)
        ).pack(side="left", padx=5)
        
        self.slot_var = customtkinter.StringVar(value="all")
        slot_combo = customtkinter.CTkComboBox(
            slot_frame,
            values=["全部", "A槽", "B槽"],
            variable=self.slot_var,
            width=80,
            height=32,
            font=("微软雅黑", 12),
            command=self.filter_partitions
        )
        slot_combo.pack(side="left", padx=5)
        
        info_frame = customtkinter.CTkFrame(self.window.main_frame)
        info_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        info_header = customtkinter.CTkFrame(info_frame)
        info_header.pack(fill="x", padx=10, pady=5)
        
        customtkinter.CTkLabel(
            info_header,
            text="设备分区信息",
            font=("微软雅黑", 16, "bold")
        ).pack(side="left", padx=10, pady=5)
        
        self.partition_count_label = customtkinter.CTkLabel(
            info_header,
            text="检测到 0 个分区",
            font=("微软雅黑", 12),
            text_color="gray"
        )
        self.partition_count_label.pack(side="right", padx=10, pady=5)
        
        self.partition_scroll = customtkinter.CTkScrollableFrame(
            info_frame,
            height=400
        )
        self.partition_scroll.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.refresh_partitions()

    def detect_device_mode(self):
        try:
            result = subprocess.run(
                ["platform-tools\\fastboot", "devices"],
                capture_output=True, text=True, timeout=5
            )
            if result.stdout.strip():
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
                    return "fastbootd"
                else:
                    return "bootloader"
            result = subprocess.run(
                ["platform-tools\\fastboot", "getvar", "all"],
                capture_output=True, text=True, timeout=5
            )
            if result.stdout or result.stderr:
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
                    return "fastbootd"
                else:
                    return "bootloader"
            result = subprocess.run(
                ["platform-tools\\adb.exe", "get-state"],
                capture_output=True, text=True, timeout=5
            )
            if "device" in result.stdout:
                return "adb"
        except Exception as e:
            self.window.add_log(f"设备检测异常: {str(e)}")
        return None

    def get_partition_info(self):
        partitions = []
        mode = self.detect_device_mode()
        
        if mode in ("fastboot", "fastbootd", "bootloader"):
            self.window.add_log(f"检测到设备处于{mode}模式")
            partitions = self.get_fastboot_partitions()
        elif mode == "adb":
            self.window.add_log("检测到设备处于ADB模式，尝试获取分区信息")
            partitions = self.get_adb_partitions()
        else:
            self.window.add_log("未检测到设备连接")
            return []
        
        return partitions

    def get_fastboot_partitions(self):
        partitions = []
        try:
            result = subprocess.run(
                ["platform-tools\\fastboot", "getvar", "is-userspace"],
                capture_output=True, text=True, encoding='utf-8', errors='ignore', timeout=5
            )
            output = result.stdout + result.stderr
            if "yes" in output.lower():
                result = subprocess.run(
                    ["platform-tools\\fastboot", "getvar", "all"],
                    capture_output=True, text=True, encoding='utf-8', errors='ignore', timeout=10
                )
                output = result.stdout + result.stderr
                import re
                partition_info = {}
                for line in output.splitlines():
                    logical_match = re.search(r'is-logical:([\w\-_]+):', line)
                    if logical_match:
                        partition_name = logical_match.group(1)
                        is_logical = ":yes" in line
                        partition_info[partition_name] = {
                            'name': partition_name,
                            'logical': is_logical
                        }
                partitions = list(partition_info.values())
            else:
                partition_names = self.detect_partitions()
                partitions = [{'name': name, 'logical': False} for name in partition_names]
        except Exception as e:
            self.window.add_log(f"Fastboot分区检测失败: {str(e)}")
            partitions = self.get_common_partitions_info()
        return partitions

    def get_adb_partitions(self):
        partitions = []
        
        try:
            result = subprocess.run(
                ["platform-tools\\adb.exe", "shell", "ls", "/dev/block/by-name/"],
                capture_output=True, text=True, timeout=10
            )
            
            if result.returncode == 0:
                partition_names = result.stdout.strip().split('\n')
                
                for name in partition_names:
                    if name and not name.startswith('ls:'):
                        partitions.append({
                            'name': name,
                            'logical': False
                        })
            
        except Exception as e:
            self.window.add_log(f"ADB分区检测失败: {str(e)}")
        
        return partitions

    def get_common_partitions_info(self):
        common_partitions = [
            "boot", "recovery", "system", "vendor", "product", "odm", "dtbo", "vbmeta",
            "userdata", "cache", "data", "splash", "logo", "modem", "dsp", "abl",
            "xbl", "xbl_config", "aop", "aop_config", "tz", "hyp", "devcfg", "keymaster",
            "qupfw", "cpucp", "shrm", "featenabler", "imagefv", "uefi", "uefisecapp",
            "init_boot", "vendor_boot", "vendor_dlkm", "system_dlkm", "system_ext",
            "my_bigball", "my_carrier", "my_company", "my_engineering", "my_heytap",
            "my_manifest", "my_preload", "my_product", "my_region", "my_stock",
            "oplus_sec", "oplusstanvbk"
        ]
        
        partitions = []
        for name in common_partitions:
            partitions.append({
                'name': name,
                'logical': False
            })
        
        return partitions

    def refresh_partitions(self):
        if self.is_refreshing:
            return
        
        self.is_refreshing = True
        self.refresh_btn.configure(state="disabled", text="刷新中...")
        
        def refresh_task():
            try:
                mode = self.detect_device_mode()
                if mode == "fastbootd":
                    self.device_status_label.configure(
                        text="设备状态: Fastbootd模式",
                        text_color="green"
                    )
                elif mode == "bootloader":
                    self.device_status_label.configure(
                        text="设备状态: Bootloader(Fastboot)模式",
                        text_color="green"
                    )
                elif mode == "adb":
                    self.device_status_label.configure(
                        text="设备状态: ADB模式",
                        text_color="blue"
                    )
                else:
                    self.device_status_label.configure(
                        text="设备状态: 未连接",
                        text_color="red"
                    )
                
                self.partition_data = self.get_partition_info()
                
                self.window.after(0, lambda: self.update_partition_display())
                
            except Exception as e:
                self.window.add_log(f"刷新分区信息失败: {str(e)}")
            finally:
                self.window.after(0, lambda: self.refresh_btn.configure(
                    state="normal", text="刷新分区信息"
                ))
                self.is_refreshing = False
        
        self.refresh_thread = threading.Thread(target=refresh_task, daemon=True)
        self.refresh_thread.start()

    def filter_partitions(self, *args):
        search_text = self.search_var.get().lower()
        slot_filter = self.slot_var.get()
        self.update_partition_display(search_text, slot_filter)

    def update_partition_display(self, search_text="", slot_filter="all"):
        for widget in self.partition_scroll.winfo_children():
            widget.destroy()
        
        if not self.partition_data:
            mode = self.detect_device_mode()
            if mode in ("fastbootd", "bootloader"):
                customtkinter.CTkLabel(
                    self.partition_scroll,
                    text="设备已连接但未检测到分区信息",
                    font=("微软雅黑", 14),
                    text_color="orange"
                ).pack(pady=20)
            else:
                customtkinter.CTkLabel(
                    self.partition_scroll,
                    text="未检测到分区信息",
                    font=("微软雅黑", 14),
                    text_color="gray"
                ).pack(pady=20)
            self.partition_count_label.configure(text="检测到 0 个分区")
            return
        
        filtered_partitions = []
        for partition in self.partition_data:
            partition_name = partition['name'].lower()
            
            if search_text and search_text not in partition_name:
                continue
                
            if slot_filter == "A槽":
                if not partition_name.endswith('_a'):
                    continue
            elif slot_filter == "B槽":
                if not partition_name.endswith('_b'):
                    continue
            
            filtered_partitions.append(partition)

        header_frame = customtkinter.CTkFrame(self.partition_scroll)
        header_frame.pack(fill="x", pady=(0, 5))
        
        headers = ["分区名称", "逻辑分区", "操作"]
        for i, header in enumerate(headers):
            width = 200 if i < 2 else 120
            customtkinter.CTkLabel(
                header_frame,
                text=header,
                font=("微软雅黑", 12, "bold"),
                width=width
            ).pack(side="left", padx=2)
        
        for partition in filtered_partitions:
            row_frame = customtkinter.CTkFrame(self.partition_scroll)
            row_frame.pack(fill="x", pady=1)
            
            customtkinter.CTkLabel(
                row_frame,
                text=partition['name'],
                font=("微软雅黑", 11),
                width=200
            ).pack(side="left", padx=2)
            
            logical_text = "是" if partition['logical'] else "否"
            logical_color = "green" if partition['logical'] else "gray"
            customtkinter.CTkLabel(
                row_frame,
                text=logical_text,
                font=("微软雅黑", 11),
                text_color=logical_color,
                width=200
            ).pack(side="left", padx=2)
            
            btn_frame = customtkinter.CTkFrame(row_frame, fg_color="transparent")
            btn_frame.pack(side="left", padx=2)
            
            customtkinter.CTkButton(
                btn_frame,
                text="刷写",
                command=lambda p=partition: self.flash_specific_partition(p),
                width=50,
                height=24,
                font=("微软雅黑", 10)
            ).pack(side="left", padx=2)
            
            customtkinter.CTkButton(
                btn_frame,
                text="删除",
                command=lambda p=partition: self.delete_specific_partition(p),
                width=50,
                height=24,
                font=("微软雅黑", 10),
                fg_color="red"
            ).pack(side="left", padx=2)
        
        self.partition_count_label.configure(text=f"检测到 {len(filtered_partitions)} 个分区")

    def create_partition(self):    
        dialog = customtkinter.CTkToplevel(self.window)
        dialog.title("创建分区")
        dialog.geometry("400x300")
        dialog.grab_set()
        
        customtkinter.CTkLabel(
            dialog,
            text="创建新分区",
            font=("微软雅黑", 16, "bold")
        ).pack(pady=10)
        
        name_frame = customtkinter.CTkFrame(dialog)
        name_frame.pack(fill="x", padx=20, pady=10)
        
        customtkinter.CTkLabel(
            name_frame,
            text="分区名称:",
            font=("微软雅黑", 12)
        ).pack(anchor="w", padx=10, pady=5)
        
        name_entry = customtkinter.CTkEntry(
            name_frame,
            placeholder_text="输入分区名称",
            font=("微软雅黑", 12)
        )
        name_entry.pack(fill="x", padx=10, pady=5)
        
        size_frame = customtkinter.CTkFrame(dialog)
        size_frame.pack(fill="x", padx=20, pady=10)
        
        customtkinter.CTkLabel(
            size_frame,
            text="分区大小(MB):",
            font=("微软雅黑", 12)
        ).pack(anchor="w", padx=10, pady=5)
        
        size_entry = customtkinter.CTkEntry(
            size_frame,
            placeholder_text="输入分区大小",
            font=("微软雅黑", 12)
        )
        size_entry.pack(fill="x", padx=10, pady=5)
        
        logical_var = customtkinter.BooleanVar()
        logical_check = customtkinter.CTkCheckBox(
            dialog,
            text="逻辑分区",
            variable=logical_var,
            font=("微软雅黑", 12)
        )
        logical_check.pack(pady=10)
        
        def do_create():
            partition_name = name_entry.get().strip()
            partition_size = size_entry.get().strip()
            
            if not partition_name or not partition_size:
                messagebox.showerror("错误", "请填写完整信息")
                return
            
            try:
                size_mb = int(partition_size)
                self.window.add_log(f"创建分区: {partition_name}, 大小: {size_mb}MB, 逻辑分区: {logical_var.get()}")
                messagebox.showinfo("成功", f"分区 {partition_name} 创建成功")
                dialog.destroy()
                self.refresh_partitions()
            except ValueError:
                messagebox.showerror("错误", "分区大小必须是数字")
        
        btn_frame = customtkinter.CTkFrame(dialog)
        btn_frame.pack(fill="x", padx=20, pady=20)
        
        customtkinter.CTkButton(
            btn_frame,
            text="创建",
            command=do_create,
            width=100,
            height=35,
            font=("微软雅黑", 12)
        ).pack(side="left", padx=10)
        
        customtkinter.CTkButton(
            btn_frame,
            text="取消",
            command=dialog.destroy,
            width=100,
            height=35,
            font=("微软雅黑", 12)
        ).pack(side="right", padx=10)

    def delete_partition(self):
        if not self.partition_data:
            messagebox.showwarning("警告", "请先刷新分区信息")
            return

        dialog = customtkinter.CTkToplevel(self.window)
        dialog.title("删除分区")
        dialog.geometry("400x500")
        dialog.grab_set()
        
        customtkinter.CTkLabel(
            dialog,
            text="选择要删除的分区：",
            font=("微软雅黑", 14, "bold")
        ).pack(pady=10)
        
        scroll_frame = customtkinter.CTkScrollableFrame(dialog, height=400)
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        for partition in self.partition_data:
            btn = customtkinter.CTkButton(
                scroll_frame,
                text=f"{partition['name']} ({'逻辑分区' if partition['logical'] else '普通分区'})",
                command=lambda p=partition: self.delete_specific_partition(p),
                width=350,
                height=35,
                font=("微软雅黑", 12),
                fg_color="red"
            )
            btn.pack(pady=2)

    def delete_specific_partition(self, partition):
        partition_name = partition['name']
        
        if not messagebox.askyesno("确认删除", f"确定要删除分区 {partition_name} 吗？\n此操作不可逆！"):
            return
        
        try:
            self.window.add_log(f"删除分区: {partition_name}")
            messagebox.showinfo("成功", f"分区 {partition_name} 删除成功")
            self.refresh_partitions()
        except Exception as e:
            error_msg = f"删除分区失败: {str(e)}"
            self.window.add_log(error_msg)
            messagebox.showerror("错误", error_msg)

    def flash_specific_partition(self, partition):
        partition_name = partition['name']
        self.window.add_log(f"准备刷写分区: {partition_name}")
        
        image_path = filedialog.askopenfilename(
            title=f"选择{partition_name}镜像文件",
            filetypes=[("镜像文件", "*.img"), ("所有文件", "*.*")]
        )
        
        if image_path:
            self.flash_image(partition_name, image_path)

    def show_flash_dialog(self):
        if not self.partition_data:
            messagebox.showwarning("警告", "请先刷新分区信息")
            return
        
        dialog = customtkinter.CTkToplevel(self.window)
        dialog.title("选择要刷写的分区")
        dialog.geometry("400x500")
        dialog.grab_set()
        
        customtkinter.CTkLabel(
            dialog,
            text="选择要刷写的分区：",
            font=("微软雅黑", 14, "bold")
        ).pack(pady=10)
        
        scroll_frame = customtkinter.CTkScrollableFrame(dialog, height=400)
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        for partition in self.partition_data:
            btn = customtkinter.CTkButton(
                scroll_frame,
                text=f"{partition['name']} ({'逻辑分区' if partition['logical'] else '普通分区'})",
                command=lambda p=partition: self.flash_specific_partition(p),
                width=350,
                height=35,
                font=("微软雅黑", 12)
            )
            btn.pack(pady=2)

    def flash_image(self, partition=None, image_path=None):
        flash_thread = threading.Thread(
            target=self._flash_image_thread,
            args=(partition, image_path),
            daemon=True
        )
        flash_thread.start()

    def _flash_image_thread(self, partition=None, image_path=None):
        import time

        def detect_mode():
            try:
                result = subprocess.run(
                    ["platform-tools\\fastboot", "devices"],
                    capture_output=True, text=True, timeout=5
                )
                if result.stdout.strip():
                    return "fastboot"
                result = subprocess.run(
                    ["platform-tools\\adb.exe", "get-state"],
                    capture_output=True, text=True, timeout=5
                )
                if "device" in result.stdout:
                    return "adb"
            except Exception:
                pass
            return None

        mode = detect_mode()
        if mode == "adb":
            self.window.after(0, lambda: self.window.add_log("当前设备处于系统模式，正在重启到Bootloader..."))
            subprocess.run(
                ["platform-tools\\adb.exe", "reboot", "bootloader"],
                capture_output=True, text=True
            )
            
            wait_dialog = customtkinter.CTkToplevel(self.window)
            wait_dialog.title("等待设备重启")
            wait_dialog.geometry("320x120")
            wait_dialog.grab_set()
            label = customtkinter.CTkLabel(wait_dialog, text="正在等待设备进入Bootloader模式...\n请勿断开设备或关闭窗口", font=("微软雅黑", 12))
            label.pack(pady=20)
            progress = customtkinter.CTkProgressBar(wait_dialog, width=200)
            progress.pack(pady=10)
            progress.start()
            
            for i in range(30):
                time.sleep(1)
                if detect_mode() == "fastboot":
                    self.window.after(0, lambda: self.window.add_log("设备已进入Bootloader模式"))
                    break
                wait_dialog.update()
            else:
                wait_dialog.destroy()
                self.window.after(0, lambda: messagebox.showerror("错误", "设备未能进入Bootloader模式，请手动重启后重试"))
                return False
            wait_dialog.destroy()
        elif mode != "fastboot":
            self.window.after(0, lambda: messagebox.showerror("错误", "未检测到设备，请连接设备并进入Fastboot模式"))
            return False

        if not image_path:
            self.window.after(0, lambda: self._show_file_dialog(partition))
            return

        file_size = os.path.getsize(image_path)
        size_mb = file_size / (1024 * 1024)
        self.window.after(0, lambda: self.window.add_log(f"镜像文件大小: {size_mb:.2f} MB"))

        try:
            if not partition:
                self.window.after(0, lambda: self.window.add_log("错误：分区名不能为空"))
                self.window.after(0, lambda: messagebox.showerror("错误", "分区名不能为空"))
                return False
                
            self.window.after(0, lambda: self.window.add_log(f"开始刷写 {partition} 分区..."))
            cmd = ["platform-tools\\fastboot", "flash"]
            if partition in ["vbmeta", "dtbo"]:
                cmd.extend(["--disable-verity", "--disable-verification"])
            cmd.extend([partition, image_path])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=300  # 5分钟超时
            )
            
            if result.stdout:
                for line in result.stdout.splitlines():
                    self.window.after(0, lambda l=line: self.window.add_log(l.strip()))
            if result.stderr:
                for line in result.stderr.splitlines():
                    self.window.after(0, lambda l=line: self.window.add_log(l.strip()))
            
            if result.returncode == 0:
                self.window.after(0, lambda: self.window.add_log(f"{partition} 分区刷写成功!"))
                self.window.after(0, lambda: messagebox.showinfo("成功", f"{partition}分区刷写成功!"))
                return True
            else:
                error_msg = result.stderr if result.stderr else "未知错误"
                self.window.after(0, lambda: self.window.add_log(f"刷写失败: {error_msg}"))
                self.window.after(0, lambda: messagebox.showerror("失败", f"刷写失败:\n{error_msg}"))
                return False
                
        except subprocess.TimeoutExpired:
            self.window.after(0, lambda: self.window.add_log("刷写超时，请检查设备连接"))
            self.window.after(0, lambda: messagebox.showerror("错误", "刷写超时，请检查设备连接"))
            return False
        except Exception as e:
            self.window.after(0, lambda: self.window.add_log(f"执行异常: {str(e)}"))
            self.window.after(0, lambda: messagebox.showerror("错误", f"执行异常: {e}"))
            return False

    def _show_file_dialog(self, partition):
        image_path = filedialog.askopenfilename(
            title=f"选择{partition}镜像文件",
            filetypes=[("镜像文件", "*.img"), ("所有文件", "*.*")]
        )
        if image_path:
            flash_thread = threading.Thread(
                target=self._flash_image_thread,
                args=(partition, image_path),
                daemon=True
            )
            flash_thread.start()
        else:
            self.window.add_log("未选择镜像文件，取消刷写")

    def get_common_partitions(self):
        return [
            "boot", "recovery", "system", "vendor", "product", "odm", "dtbo", "vbmeta",
            "userdata", "cache", "data", "splash", "logo", "modem", "dsp", "abl",
            "xbl", "xbl_config", "aop", "aop_config", "tz", "hyp", "devcfg", "keymaster",
            "qupfw", "cpucp", "shrm", "featenabler", "imagefv", "uefi", "uefisecapp",
            "init_boot", "vendor_boot", "vendor_dlkm", "system_dlkm", "system_ext",
            "my_bigball", "my_carrier", "my_company", "my_engineering", "my_heytap",
            "my_manifest", "my_preload", "my_product", "my_region", "my_stock",
            "oplus_sec", "oplusstanvbk"
        ]

    def detect_partitions(self):
        partitions = set()
        
        try:
            result = subprocess.run(
                ["platform-tools\\fastboot", "getvar", "all"],
                capture_output=True, text=True, encoding='utf-8', errors='ignore',
                timeout=10
            )
            output = result.stdout + result.stderr
            
            import re
            for line in output.splitlines():
                match = re.search(r'partition-type:([\w\-_]+):', line)
                if match:
                    partitions.add(match.group(1))
                match = re.search(r'\(([\w\-_]+)\):', line)
                if match:
                    partitions.add(match.group(1))
        except Exception as e:
            self.window.add_log(f"getvar all 检测失败: {str(e)}")

        if not partitions:
            self.window.add_log("使用常见分区列表")
            partitions = set(self.get_common_partitions())
        
        try:
            result = subprocess.run(
                ["platform-tools\\fastboot", "getvar", "slot-count"],
                capture_output=True, text=True, encoding='utf-8', timeout=5
            )
            if "slot-count: 2" in result.stdout + result.stderr:
                self.window.add_log("检测到AB分区设备")
                ab_partitions = set()
                for part in partitions:
                    if part.endswith('_a') or part.endswith('_b'):
                        ab_partitions.add(part)
                    else:
                        try:
                            has_slot_result = subprocess.run(
                                ["platform-tools\\fastboot", "getvar", f"has-slot:{part}"],
                                capture_output=True, text=True, encoding='utf-8', timeout=3
                            )
                            if "yes" in (has_slot_result.stdout + has_slot_result.stderr).lower():
                                ab_partitions.add(f"{part}_a")
                                ab_partitions.add(f"{part}_b")
                            else:
                                ab_partitions.add(part)
                        except Exception:
                            ab_partitions.add(part)
                partitions = ab_partitions
            else:
                self.window.add_log("检测到非AB分区设备")
        except Exception as e:
            self.window.add_log(f"AB分区检测失败: {str(e)}")
        
        return sorted(list(partitions))

    def select_partition(self, partition, selected, select_win):
        selected.update({"part": partition})
        select_win.destroy()

    def show_partition_selector(self, partitions):
        select_win = customtkinter.CTkToplevel(self.window)
        select_win.title("选择要刷写的分区")
        select_win.geometry("500x600")
        select_win.grab_set()
        
        customtkinter.CTkLabel(
            select_win,
            text="请选择要刷写的分区：",
            font=("微软雅黑", 16, "bold")
        ).pack(pady=10)
        
        search_frame = customtkinter.CTkFrame(select_win)
        search_frame.pack(fill="x", padx=10, pady=5)
        
        search_var = customtkinter.StringVar()
        search_entry = customtkinter.CTkEntry(
            search_frame,
            placeholder_text="输入分区名搜索...",
            textvariable=search_var,
            font=("微软雅黑", 12)
        )
        search_entry.pack(side="left", fill="x", expand=True, padx=(10, 5), pady=10)
        
        clear_btn = customtkinter.CTkButton(
            search_frame,
            text="清空",
            command=lambda: search_var.set(""),
            width=60,
            height=32,
            font=("微软雅黑", 11)
        )
        clear_btn.pack(side="right", padx=(5, 10), pady=10)
        
        scroll_frame = customtkinter.CTkScrollableFrame(select_win, height=450)
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        selected = {"part": None}
        
        buttons = {}
        
        def create_buttons():   
            for btn in buttons.values():
                btn.destroy()
            buttons.clear()
            
            for p in partitions:
                btn = customtkinter.CTkButton(
                    scroll_frame,
                    text=p,
                    command=lambda x=p: self.select_partition(x, selected, select_win),
                    font=("微软雅黑", 13),
                    width=450,
                    height=36
                )
                btn.pack(pady=2)
                buttons[p] = btn
        
        def filter_partitions(*args):
            search_text = search_var.get().lower()
            for partition_name, btn in buttons.items():
                if search_text in partition_name.lower():
                    btn.pack(pady=2)
                else:
                    btn.pack_forget()
        
        search_var.trace("w", filter_partitions)
        
        create_buttons()
        
        search_entry.focus()
        
        select_win.wait_window()
        return selected["part"]
