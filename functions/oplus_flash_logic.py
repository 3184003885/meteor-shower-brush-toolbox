import customtkinter
from tkinter import filedialog, messagebox
import os
import subprocess
import threading
import re
import shutil
import time
from functions.oplus_flash_errors import FASTBOOT_ERROR_HINTS

class OplusFlashLogic:
    def __init__(self, window):
        self.window = window
        # 移除会员和登录校验，所有用户均可使用
        self.img_dir = ""
        self.img_files = []
        self.state = "init"  # 当前流程状态
        self._lock = threading.Lock()  # 添加线程锁

    def show_menu(self):
        self.window.clear_main_frame()
        customtkinter.CTkLabel(
            self.window.main_frame,
            text="欧加真刷机",
            font=("微软雅黑", 24, "bold")
        ).pack(pady=20)

        # 只保留普通刷写模式，无重构逻辑分区选项
        btn_frame = customtkinter.CTkFrame(self.window.main_frame)
        btn_frame.pack(pady=20)

        self.step_btn = customtkinter.CTkButton(
            btn_frame,
            text="① 选择镜像文件夹（点击开始）",
            command=self.step_select_img_dir,
            width=320,
            height=48,
            font=("微软雅黑", 15)
        )
        self.step_btn.pack(side="left", padx=(0, 10))

        # 刷机包下载按钮
        customtkinter.CTkButton(
            btn_frame,
            text="刷机包(用内嵌下载器)",
            command=lambda: self._open_url("https://yulovehan.top/rom_search.php"),
            width=110,
            height=36,
            font=("微软雅黑", 12)
        ).pack(side="left", padx=(10, 0))

        self._show_special_tools(btn_frame)

        self.img_list_frame = customtkinter.CTkScrollableFrame(
            self.window.main_frame,
            height=200 
        )
        self.img_list_frame.pack(fill="both", expand=True, padx=30, pady=10)

        self.current_step = 1

    def _show_special_tools(self, parent):
        """特殊功能折叠框"""
        # 折叠按钮和内容框
        self.special_tools_expanded = False
        special_frame = customtkinter.CTkFrame(parent, fg_color="#f5f5f5", border_width=1, border_color="#cccccc")
        special_frame.pack(side="left", padx=10)

        def toggle():
            self.special_tools_expanded = not self.special_tools_expanded
            if self.special_tools_expanded:
                expand_btn.configure(text="▼ 高级功能")
                content_frame.pack(fill="x", padx=5, pady=5)
            else:
                expand_btn.configure(text="▶ 高级功能")
                content_frame.forget()

        expand_btn = customtkinter.CTkButton(
            special_frame,
            text="▶ 高级功能",
            width=120,
            height=32,
            font=("微软雅黑", 13),
            fg_color="#e0e0e0",
            text_color="black",
            command=toggle
        )
        expand_btn.pack(fill="x", padx=5, pady=5)

        content_frame = customtkinter.CTkFrame(special_frame, fg_color="#fafafa")
        # 默认收起，不pack

        # 高级功能按钮
        customtkinter.CTkButton(
            content_frame,
            text="解包刷机包",
            command=self.unpack_payload,
            width=140,
            height=32,
            font=("微软雅黑", 12)
        ).pack(fill="x", padx=5, pady=3)

        customtkinter.CTkButton(
            content_frame,
            text="fastbootd修复",
            command=self.fastbootd_repair_choice,
            width=180,
            height=32,
            font=("微软雅黑", 12)
        ).pack(fill="x", padx=5, pady=3)

    def fastbootd_repair_choice(self):
        import customtkinter
        from tkinter import filedialog, messagebox
        win = customtkinter.CTkToplevel(self.window)
        win.title("选择修复方式")
        win.geometry("360x260")
        win.resizable(False, False)
        win.attributes("-topmost", True)
        label = customtkinter.CTkLabel(win, text="请选择fastbootd修复方式：", font=("微软雅黑", 15, "bold"))
        label.pack(pady=18)
        def choose_folder():
            win.destroy()
            folder_path = filedialog.askdirectory(title="选择包含img文件的文件夹")
            if folder_path:
                self.fastbootd_repair(folder_path)
        def choose_payload():
            win.destroy()
            self.extract_needed_partitions_from_payload()
        btn1 = customtkinter.CTkButton(win, text="选择img文件夹修复", font=("微软雅黑", 13), width=220, height=38, command=choose_folder)
        btn1.pack(pady=7)
        btn2 = customtkinter.CTkButton(win, text="选择payload自动修复", font=("微软雅黑", 13), width=220, height=38, command=choose_payload)
        btn2.pack(pady=7)

    def extract_needed_partitions_from_payload(self):
        from tkinter import filedialog
        payload_path = filedialog.askopenfilename(
            title="选择payload.bin或zip文件",
            filetypes=[("Payload文件", "*.bin *.zip"), ("所有文件", "*.*")]
        )
        if not payload_path:
            return
        self._show_extract_progress()
        import threading
        threading.Thread(target=self._thread_extract_needed_partitions, args=(payload_path,), daemon=True).start()

    def _auto_fastbootd_repair_and_cleanup(self):
        import threading
        def repair_and_cleanup():
            self.fastbootd_repair()
            # 修复完成后40秒再删除
            import os, shutil, time
            out_dir = "修复分区"
            try:
                time.sleep(50)
                if os.path.exists(out_dir):
                    shutil.rmtree(out_dir)
            except Exception:
                pass
        threading.Thread(target=repair_and_cleanup, daemon=True).start()

    def _show_extract_progress(self):
        for widget in self.img_list_frame.winfo_children():
            widget.destroy()
        customtkinter.CTkLabel(
            self.img_list_frame,
            text="分区提取进度",
            font=("微软雅黑", 14, "bold")
        ).pack(pady=5)
        self.extract_progress = customtkinter.CTkProgressBar(self.img_list_frame, width=400)
        self.extract_progress.pack(pady=10)
        self.extract_progress.set(0)
        self.extract_status = customtkinter.CTkLabel(
            self.img_list_frame,
            text="准备提取...",
            font=("微软雅黑", 12)
        )
        self.extract_status.pack()

    def safe_update_status(self, text):
        try:
            if hasattr(self, 'extract_status') and self.extract_status.winfo_exists():
                self.extract_status.configure(text=text)
        except Exception:
            pass

    def _safe_messagebox_error(self, msg):
        try:
            if hasattr(self, 'extract_status') and self.extract_status.winfo_exists():
                from tkinter import messagebox
                messagebox.showerror("错误", msg)
        except Exception:
            pass

    def _safe_messagebox_info(self, msg):
        try:
            if hasattr(self, 'extract_status') and self.extract_status.winfo_exists():
                from tkinter import messagebox
                messagebox.showinfo("完成", msg)
        except Exception:
            pass

    def _thread_extract_needed_partitions(self, payload_path):
        import subprocess, os, zipfile, tempfile, shutil, traceback
        from tkinter import messagebox
        try:
            # 处理zip文件
            if payload_path.lower().endswith('.zip'):
                with zipfile.ZipFile(payload_path, 'r') as zip_ref:
                    if 'payload.bin' not in zip_ref.namelist():
                        self.window.after(0, lambda: self._safe_messagebox_error("zip中未找到payload.bin"))
                        return
                    temp_dir = tempfile.mkdtemp()
                    zip_ref.extract('payload.bin', temp_dir)
                    payload_path = os.path.join(temp_dir, 'payload.bin')
            # 自动识别平台
            try:
                getvar = subprocess.run(
                    ["platform-tools\\fastboot", "getvar", "hardware"],
                    capture_output=True, text=True, encoding='utf-8', errors='ignore'
                )
                hw_info = (getvar.stdout + getvar.stderr).lower()
            except Exception as e:
                hw_info = ""
            if "mt" in hw_info or "mediatek" in hw_info:
                key_parts = [
                    "boot", "lk", "dtbo", "md1img", "vbmeta", "vendor_boot"
                ]
            else:
                key_parts = [
                    "boot", "recovery", "dtbo", "modem", "vbmeta", "vendor_boot"
                ]
            out_dir = "修复分区"
            os.makedirs(out_dir, exist_ok=True)
            failed_parts = []
            total = len(key_parts)
            for idx, part in enumerate(key_parts, 1):
                self.window.after(0, lambda p=part, i=idx, t=total: self.safe_update_status(f"正在提取分区: {p} ({i}/{t})"))
                self.window.after(0, lambda i=idx, t=total: self.extract_progress.set(i / t))
                cmd = [
                    "platform-tools\\payload-dumper-go.exe",
                    "-o", out_dir,
                    "-p", part,
                    payload_path
                ]
                result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
                if result.returncode != 0:
                    failed_parts.append(part)
            self.window.after(0, lambda: self.extract_progress.set(1))
            if failed_parts:
                self.window.after(0, lambda: self.extract_status.configure(text=f"以下分区提取失败: {', '.join(failed_parts)}"))
                self.window.after(0, lambda: self._safe_messagebox_error(f"以下分区提取失败: {', '.join(failed_parts)}"))
                return
            else:
                self.window.after(0, lambda: self.extract_status.configure(text="分区提取完成，自动进入修复流程"))
                # 自动补全 .img 后缀
                for part in key_parts:
                    src = os.path.join(out_dir, part)
                    dst = os.path.join(out_dir, part + ".img")
                    if os.path.exists(src) and not os.path.exists(dst):
                        try:
                            os.rename(src, dst)
                        except Exception:
                            pass
                self.window.after(0, lambda: self._safe_messagebox_info(f"分区提取完成，自动进入修复流程"))
                self.window.after(0, self._auto_fastbootd_repair_and_cleanup)
        except Exception as e:
            self.window.after(0, lambda: self._safe_messagebox_error(f"下载或提取失败: {str(e)}"))

    def step_select_img_dir(self):
        dir_path = filedialog.askdirectory(title="选择包含img文件的文件夹")
        if not dir_path:
            return
        self.img_dir = dir_path
        # 新增：统计文件夹总大小
        total_size = 0
        for root, dirs, files in os.walk(dir_path):
            for f in files:
                fp = os.path.join(root, f)
                try:
                    total_size += os.path.getsize(fp)
                except Exception:
                    pass
        size_gb = total_size / (1024 ** 3)
        if size_gb < 5:
            messagebox.showerror("刷机包体积过小", f"刷机包文件夹总大小为{size_gb:.2f}GB，可能不完整，请检查后重试。")
            self.window.add_log(f"刷机包体积过小：{size_gb:.2f}GB，已终止流程")
            return
        with self._lock:
            self.img_files = [f for f in os.listdir(dir_path) if f.lower().endswith('.img')]
        # 新增：img文件数量校验
        if len(self.img_files) < 30:
            messagebox.showerror("img文件数量过少", f"检测到img文件数量为{len(self.img_files)}，可能不是完整刷机包，请检查后重试。")
            self.window.add_log(f"img文件数量过少：{len(self.img_files)}，已终止流程")
            return
        
        self.window.add_log(f"选择镜像文件夹: {dir_path}")
        with self._lock:
            self.img_files = [f for f in os.listdir(dir_path) if f.lower().endswith('.img')]
        
        # 跳过preloader_raw分区
        original_count = len(self.img_files)
        self.img_files = [f for f in self.img_files if 'preloader_raw' not in f.lower()]
        if original_count > len(self.img_files):
            skipped_count = original_count - len(self.img_files)
            self.window.add_log(f'已跳过preloader_raw分区：{skipped_count}个文件')
        
        img_files_str = f"检测到img文件: {', '.join(self.img_files) if self.img_files else '无'}"
        self.window.add_log(img_files_str)
        if not hasattr(self, "flash_log_lines"):
            self.flash_log_lines = []
        self.flash_log_lines.append(img_files_str)
        self.show_img_list()
        self.current_step = 2
        self.step_btn.configure(
            text="② 检测设备并重启到fastbootd（点击继续）",
            command=self.step_check_and_reboot_to_fastbootd
        )

    def show_img_list(self):
        for widget in self.img_list_frame.winfo_children():
            widget.destroy()
        if not self.img_files:
            customtkinter.CTkLabel(
                self.img_list_frame,
                text="未找到img文件",
                font=("微软雅黑", 13),
                text_color="orange"
            ).pack(pady=10)
            return
        customtkinter.CTkLabel(
            self.img_list_frame,
            text="检测到以下img文件：",
            font=("微软雅黑", 14, "bold")
        ).pack(pady=5)
        for f in self.img_files:
            customtkinter.CTkLabel(
                self.img_list_frame,
                text=f,
                font=("微软雅黑", 12)
            ).pack(anchor="w", padx=20)

    def step_check_and_reboot_to_fastbootd(self):
        import threading
        threading.Thread(target=self._thread_check_and_reboot_to_fastbootd, daemon=True).start()

    def _thread_check_and_reboot_to_fastbootd(self):
        state = self._detect_device_state()
        import time
        def recheck_state(target_state, on_success, on_fail):
            time.sleep(5)
            state2 = self._detect_device_state()
            if state2 == target_state:
                self.window.add_log(f"复查：设备依然处于{target_state}模式。")
                on_success()
            else:
                self.window.add_log(f"复查失败：设备未保持在{target_state}模式，当前为{state2 or '未知'}。")
                self.window.after(0, lambda: self._safe_messagebox_error(f"设备未保持在{target_state}模式，当前为{state2 or '未知'}。"))
        
        if state == "adb":
            self.window.add_log("当前设备在系统模式，准备重启到fastbootd...")
            subprocess.run(
                ["platform-tools\\adb.exe", "reboot", "fastboot"],
                capture_output=True, text=True
            )
            # 等待进入fastbootd
        elif state == "fastboot":
            self.window.add_log("当前设备在fastboot模式，准备重启到fastbootd...")
            subprocess.run(
                ["platform-tools\\fastboot", "reboot", "fastboot"],
                capture_output=True, text=True
            )
            # 等待进入fastbootd
        elif state == "fastbootd":
            self.window.add_log("设备已在fastbootd模式。")
            # 复查fastbootd
            recheck_state("fastbootd", lambda: self.window.after(0, self.step_to_list_logical_partitions), lambda: None)
            return
        else:
            self.window.add_log("未检测到设备，请检查连接。")
            self.window.after(0, lambda: self._safe_messagebox_error("未检测到设备，请检查连接。"))
            return

        # 等待进入fastbootd
        for i in range(60):
            state = self._detect_device_state()
            if state == "fastbootd":
                self.window.add_log("设备已进入fastbootd模式。")
                # 复查fastbootd
                recheck_state("fastbootd", lambda: self.window.after(0, self.step_to_list_logical_partitions), lambda: None)
                return
            elif state == "fastboot":
                self.window.add_log("检测到设备处于Bootloader（fastboot）模式，立即提示修复。")
                def do_repair():
                    self.window.after(0, self.fastbootd_repair)
                self.window.after(0, lambda: (
                    messagebox.askyesno(
                        "修复提示",
                        f"检测到设备处于Bootloader（fastboot）模式，是否进行fastbootd修复？"
                    ) and do_repair()
                ))
                return
            time.sleep(1)
        # 超时后再次检测当前状态
        final_state = self._detect_device_state()
        self.window.add_log("检测超时，未进入fastbootd模式。当前状态：" + (final_state or '未知'))
        def do_repair():
            self.window.after(0, self.fastbootd_repair)
        self.window.after(0, lambda: (
            messagebox.askyesno(
                "修复提示",
                f"检测超时，当前检测到设备状态为：{final_state or '未知'}。\n是否进行fastbootd修复？"
            ) and do_repair()
        ))

    def _detect_device_state(self):
        # 检查adb
        try:
            adb_result = subprocess.run(
                ["platform-tools\\adb.exe", "get-state"],
                capture_output=True, text=True
            )
            if "device" in adb_result.stdout:
                return "adb"
        except Exception:
            pass
        
        # 检查fastbootd
        try:
            fb_result = subprocess.run(
                ["platform-tools\\fastboot", "getvar", "is-userspace"],
                capture_output=True, text=True
            )
            output = fb_result.stdout + fb_result.stderr
            if "is-userspace: yes" in output.lower():
                return "fastbootd"
            elif "is-userspace: no" in output.lower():
                return "fastboot"
        except Exception:
            pass
        
        # 检查fastboot
        try:
            fb_devices = subprocess.run(
                ["platform-tools\\fastboot", "devices"],
                capture_output=True, text=True
            )
            if fb_devices.stdout.strip():
                return "fastboot"
        except Exception:
            pass
        
        return None

    def step_to_list_logical_partitions(self):
        self.current_step = 3
        self.step_btn.configure(
            text="③ 检测分区表（点击继续）",
            state="normal",
            command=self._do_list_logical_partitions
        )

    def _do_list_logical_partitions(self):
        import re
        try:
            # 获取设备分区信息
            result = subprocess.run(
                ["platform-tools\\fastboot", "getvar", "all"],
                capture_output=True, text=True
            )
            output = result.stdout + result.stderr
            # 解析所有逻辑分区（带cow和不带cow）
            logical_matches = re.findall(r"is-logical:([\w\-_]+):yes", output)
            all_logical = set()
            cow_logical = set()
            for part in logical_matches:
                all_logical.add(part)
                if part.endswith("-cow"):
                    cow_logical.add(part)
            non_cow_logical = set([p for p in all_logical if not p.endswith("-cow")])
            # 检测当前槽位
            current_slot = "a"
            try:
                slot_result = subprocess.run(
                    ["platform-tools\\fastboot", "getvar", "current-slot"],
                    capture_output=True, text=True
                )
                for line in (slot_result.stdout + slot_result.stderr).splitlines():
                    if "current-slot:" in line.lower():
                        slot_val = line.split(":")[-1].strip()
                        if slot_val in ["a", "b"]:
                            current_slot = slot_val
                            break
            except Exception as e:
                self.window.add_log(f"检测当前槽位失败: {str(e)}，默认使用A槽")
            self.window.add_log(f"当前槽位: {current_slot.upper()}")
            # 启动分区补全线程（无论是否缺少都执行）
            threading.Thread(target=self._auto_fill_partitions, daemon=True).start()
            # 如果启用重构逻辑分区刷写
            if hasattr(self, "rebuild_logical_partitions") and self.rebuild_logical_partitions:
                self._rebuild_logical_info = {
                    "all_logical": all_logical,
                    "cow_logical": cow_logical,
                    "non_cow_logical": non_cow_logical,
                    "current_slot": current_slot
                }
                msg = (
                    f"检测到所有逻辑分区: {', '.join(all_logical)}\n"
                    f"COW分区: {', '.join(cow_logical) if cow_logical else '无'}\n"
                    f"将要重建的分区: {', '.join(non_cow_logical)}"
                )
                self.window.add_log("[重构逻辑分区刷写] " + msg.replace("\n", " "))
                messagebox.showinfo("逻辑分区检测", msg + "\n\n请点击第④步进行逻辑分区重构。")
                self.step_btn.configure(
                    text="④ 重构逻辑分区（点击执行）",
                    state="normal",
                    command=self.step_rebuild_logical_partitions
                )
                return
            # ...原有逻辑分区检测流程...
            # 检测当前槽位
            current_slot = "a"  # 默认值
            try:
                slot_result = subprocess.run(
                    ["platform-tools\\fastboot", "getvar", "current-slot"],
                    capture_output=True, text=True
                )
                for line in (slot_result.stdout + slot_result.stderr).splitlines():
                    if "current-slot:" in line.lower():
                        slot_val = line.split(":")[-1].strip()
                        if slot_val in ["a", "b"]:
                            current_slot = slot_val
                            break
            except Exception as e:
                self.window.add_log(f"检测当前槽位失败: {str(e)}，默认使用A槽")
            self.window.add_log(f"当前槽位: {current_slot.upper()}")
            logical_parts = []
            cow_partitions_to_erase = []  
            lines_with_is_logical = [line for line in output.split('\n') if 'is-logical:' in line]
            patterns_to_try = [
                r"is-logical:([\w\-_]+-cow):yes",     # 匹配cow分区
            ]
            cow_matches = []
            for pattern in patterns_to_try:
                matches = re.findall(pattern, output)
                if matches:
                    cow_matches = matches
                    break
            all_matches = cow_matches
            # 只打印检测到的cow分区，不做任何处理
            logical_parts = []
            for partition in all_matches:
                logical_parts.append(partition)  # 直接原样加入
            self.cow_partitions_to_erase = logical_parts
            self.flash_log_lines = []
            msg = "检测到以下cow分区：\n" + "\n".join(logical_parts)
            self.window.add_log(msg)
            self.flash_log_lines.append(msg)
            self.step_btn.configure(
                text="④ 擦除逻辑分区（点击执行）",
                state="normal",
                command=lambda: self.delete_logical_partitions(logical_parts)
            )
        except Exception:
            pass

    def _auto_fill_partitions(self):
        """自动补全分区（my_company.img、my_preload.img等），始终执行，独立线程，日志主线程刷新"""
        auto_fill = {
            "my_company": "my_company.img",
            "my_preload": "my_preload.img"
        }
        auto_fill_url = {
            "my_company": "https://zyz.yulovehan.top/d/1/my_company.img",
            "my_preload": "https://zyz.yulovehan.top/d/1/my_preload.img"
        }
        img_files_lower = [f.lower() for f in self.img_files]
        for part_base, img_name in auto_fill.items():
            dest_img = os.path.join(self.img_dir, img_name)
            if not os.path.exists(dest_img):
                try:
                    self.window.after(0, lambda pb=part_base: self.window.add_log(f"正在从网络下载分区 {pb} ..."))
                    import requests
                    url = auto_fill_url[part_base]
                    resp = requests.get(url, stream=True, timeout=15)
                    with open(dest_img, "wb") as f:
                        for chunk in resp.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                    self.window.after(0, lambda pb=part_base, di=dest_img: self.window.add_log(f"已下载分区 {pb} 到 {di}"))
                    with self._lock:
                        self.img_files.append(img_name)
                except Exception as e:
                    self.window.after(0, lambda pb=part_base, err=str(e): self.window.add_log(f"自动补全分区 {pb} 下载失败: {err}"))
            else:
                self.window.after(0, lambda pb=part_base, di=dest_img: self.window.add_log(f"分区 {pb} 检查完成，文件已存在: {di}"))
                with self._lock:
                    if img_name not in self.img_files:
                        self.img_files.append(img_name)

    def delete_logical_partitions(self, logical_parts):
        import threading
        threading.Thread(target=self._thread_delete_logical_partitions, args=(logical_parts,), daemon=True).start()

    def _thread_delete_logical_partitions(self, logical_parts):
        try:
            # 开始记录实时日志
            self.show_realtime_log_window()
            # 检测当前槽位
            current_slot = "a"  # 默认值
            try:
                slot_result = subprocess.run(
                    ["platform-tools\\fastboot", "getvar", "current-slot"],
                    capture_output=True, text=True
                )
                for line in (slot_result.stdout + slot_result.stderr).splitlines():
                    if "current-slot:" in line.lower():
                        slot_val = line.split(":")[-1].strip()
                        if slot_val in ["a", "b"]:
                            current_slot = slot_val
                            break
            except Exception as e:
                self.window.add_log(f"检测当前槽位失败: {str(e)}，默认使用A槽")
            self.window.add_log(f"当前槽位: {current_slot.upper()}")
            # 擦除COW分区
            if hasattr(self, 'cow_partitions_to_erase') and self.cow_partitions_to_erase:
                self.window.add_log("开始擦除COW分区...")
                erased_count = 0
                failed_count = 0
                for cow_partition in self.cow_partitions_to_erase:
                    self.window.add_log(f"正在擦除COW分区: {cow_partition}")
                    self.flash_log_lines.append(f"正在擦除COW分区: {cow_partition}")
                    try:
                        ret = subprocess.run(
                            ["platform-tools\\fastboot", "delete-logical-partition", cow_partition],
                            capture_output=True, text=True
                        )
                        if ret.returncode == 0:
                            self.window.add_log(f"成功擦除COW分区: {cow_partition}")
                            self.flash_log_lines.append(f"成功擦除COW分区: {cow_partition}")
                            erased_count += 1
                        else:
                            self.window.add_log(f"擦除COW分区失败: {cow_partition} - {ret.stderr}")
                            self.flash_log_lines.append(f"擦除COW分区失败: {cow_partition} - {ret.stderr}")
                            failed_count += 1
                    except Exception as e:
                        self.window.add_log(f"擦除COW分区异常: {cow_partition} - {str(e)}")
                        self.flash_log_lines.append(f"擦除COW分区异常: {cow_partition} - {str(e)}")
                        failed_count += 1
                self.window.add_log(f"COW分区擦除完成，成功: {erased_count} 个，失败: {failed_count} 个")
                self.flash_log_lines.append(f"COW分区擦除完成，成功: {erased_count} 个，失败: {failed_count} 个")
                if failed_count == 0:
                    messagebox.showinfo("完成", f"所有COW分区已成功擦除（{erased_count} 个）")
                else:
                    messagebox.showwarning("部分完成", f"COW分区擦除完成，成功: {erased_count} 个，失败: {failed_count} 个")
            else:
                self.window.add_log("未找到需要擦除的COW分区")
                self.flash_log_lines.append("未找到需要擦除的COW分区")
                messagebox.showinfo("完成", "未找到需要擦除的COW分区")
        except Exception as e:
            self.window.add_log(f"处理逻辑分区异常: {str(e)}")
            self.flash_log_lines.append(f"处理逻辑分区异常: {str(e)}")
            messagebox.showerror("错误", f"处理逻辑分区异常: {str(e)}")
        self.window.after(0, lambda: self.step_btn.configure(
            text="⑤ 刷写分区（点击执行）",
            state="normal",
            command=self.flash_all_partitions
        ))

    def flash_all_partitions(self):
        import threading
        messagebox.showinfo(
            "刷写提示",
            "刷机过程中请勿操作手机，也不要关闭或操作本程序。\n"
            "如无报错请耐心等待，刷写完成会有提示。\n"
            "my_stock,odm,vendor,system,system_ext需耐心等待"
        )
        self._show_flash_progress()
        threading.Thread(target=self._thread_flash_all_partitions, daemon=True).start()

    def _show_flash_progress(self):
        for widget in self.img_list_frame.winfo_children():
            widget.destroy()
        customtkinter.CTkLabel(
            self.img_list_frame,
            text="刷写进度",
            font=("微软雅黑", 14, "bold")
        ).pack(pady=5)
        self.progress_bar = customtkinter.CTkProgressBar(self.img_list_frame, width=400)
        self.progress_bar.pack(pady=10)
        self.progress_bar.set(0)
        self.flash_log_text = customtkinter.CTkTextbox(self.img_list_frame, height=180, font=("Consolas", 11))
        self.flash_log_text.pack(fill="both", expand=True, padx=10, pady=10)
        self.flash_log_text.insert("end", "刷写日志:\n")
        self.flash_log_text.see("end")
        # 添加重要提示
        customtkinter.CTkLabel(
            self.img_list_frame,
            text="重要提示：\n"
                 "1. 刷机过程中请勿乱动程序以及手机\n"
                 "2. my_stock, odm, vendor, system, system_ext 分区需耐心等待\n"
                 "3. 本工具为收费工具，一切后果由用户自行承担",
            font=("微软雅黑", 12),
            text_color="red",
            justify="left"
        ).pack(pady=8)

    def _thread_flash_all_partitions(self):
        try:
            # 日志收集
            flash_log_lines = self.flash_log_lines if hasattr(self, "flash_log_lines") else []
            def log_both(msg):
                self.window.add_log(msg)
                flash_log_lines.append(msg)
                self._append_flash_log(msg)

            self.show_realtime_log_window()

            import re
            logical_partitions = []
            try:
                result = subprocess.run(
                    ["platform-tools\\fastboot", "getvar", "all"],
                    capture_output=True, text=True
                )
                output = result.stdout + result.stderr
                logical_matches = re.findall(r"is-logical:([\w\-_]+):yes", output)
                log_both(f"检测到逻辑分区: {', '.join(logical_matches) if logical_matches else '无'}")
                for partition in logical_matches:
                    if partition.endswith('-cow'):
                        if partition.endswith('_a-cow') or partition.endswith('_b-cow'):
                            base_name = partition[:-6] 
                        else:
                            base_name = partition.replace('-cow', '')
                    elif partition.endswith('_a') or partition.endswith('_b'):
                        base_name = partition[:-2] 
                    else:
                        base_name = partition
                    if base_name not in logical_partitions:
                        logical_partitions.append(base_name)
                        log_both(f"添加逻辑分区: {base_name} (来自 {partition})")
                self.full_logical_partitions = logical_matches
            except Exception as e:
                log_both(f"获取逻辑分区信息失败: {str(e)}")
                logical_partitions = []

            with self._lock:
                img_files_to_flash = [f for f in self.img_files if "modem" not in os.path.splitext(f)[0].lower()]
            logical_tasks = []
            normal_tasks = []
            for f in img_files_to_flash:
                base = os.path.splitext(f)[0].lower()
                if base in logical_partitions:
                    logical_tasks.append((base, f))
                else:
                    normal_tasks.append((base, f))
            log_both(f"普通分区数量: {len(normal_tasks)}")
            log_both(f"逻辑分区数量: {len(logical_tasks)}")
            normal_success = 0
            normal_failed = []
            logical_success = 0
            logical_failed = []
            log_both("====== 第一阶段：刷写普通分区 ======")
            for idx, (part_name, img_file) in enumerate(normal_tasks, 1):
                self._wait_if_paused()
                img_path = os.path.join(self.img_dir, img_file)
                progress_msg = f"普通分区({idx}/{len(normal_tasks)}) "
                log_msg = f"{progress_msg}正在刷写分区: {part_name}"
                log_both(log_msg)
                ret = self.run_fastboot_cmd_realtime(["platform-tools\\fastboot", "flash", part_name, img_path])
                if ret == 0:
                    normal_success += 1
                    log_msg = f"{progress_msg}刷写成功: {part_name}"
                    log_both(log_msg)
                else:
                    log_msg = f"{progress_msg}刷写失败: {part_name}"
                    log_both(log_msg)
                    normal_failed.append(part_name)
                self.progress_bar.set(idx / len(normal_tasks))
            log_both(f"普通分区刷写完成，成功: {normal_success}，失败: {len(normal_failed)}")
            if logical_tasks:
                log_both("====== 第二阶段：刷写逻辑分区 ======")
                for idx, (part_name, img_file) in enumerate(logical_tasks, 1):
                    self._wait_if_paused()
                    img_path = os.path.join(self.img_dir, img_file)
                    progress_msg = f"逻辑分区({idx}/{len(logical_tasks)}) "
                    log_msg = f"{progress_msg}正在刷写分区: {part_name}"
                    log_both(log_msg)
                    ret = self.run_fastboot_cmd_realtime(["platform-tools\\fastboot", "flash", part_name, img_path])
                    if ret == 0:
                        logical_success += 1
                        log_msg = f"{progress_msg}刷写成功: {part_name}"
                        log_both(log_msg)
                    else:
                        log_msg = f"{progress_msg}刷写失败: {part_name}"
                        log_both(log_msg)
                        logical_failed.append(part_name)
                    self.progress_bar.set(idx / len(logical_tasks))
                log_both(f"逻辑分区刷写完成，成功: {logical_success}，失败: {len(logical_failed)}")
            failed_parts = normal_failed + logical_failed
            total_success = normal_success + logical_success
            log_both(f"总刷写成功分区数量: {total_success}")
            if failed_parts:
                import re
                try:
                    current_slot = "a" 
                    try:
                        slot_result = subprocess.run(
                            ["platform-tools\\fastboot", "getvar", "current-slot"],
                            capture_output=True, text=True
                        )
                        for line in (slot_result.stdout + slot_result.stderr).splitlines():
                            if "current-slot:" in line.lower():
                                slot_val = line.split(":")[-1].strip()
                                if slot_val in ["a", "b"]:
                                    current_slot = slot_val
                                    break
                    except Exception as e:
                        log_both(f"检测当前槽位失败: {str(e)}，默认使用A槽")
                    log_both(f"当前槽位: {current_slot.upper()}")
                    fixed_logical_partitions = [
                        "system", "system_ext", "vendor", "product", 
                        "odm", "vendor_dlkm", "system_dlkm"
                    ]
                    with self._lock:
                        img_files_copy = self.img_files.copy()
                    img_base_names = [os.path.splitext(f)[0].lower() for f in img_files_copy]
                    logical_partitions = []
                    for part_name in fixed_logical_partitions:
                        if part_name in img_base_names:
                            logical_partitions.append(part_name)
                    for img_file in img_files_copy:
                        base_name = os.path.splitext(img_file)[0].lower()
                        if base_name.startswith("my") and base_name not in logical_partitions:
                            logical_partitions.append(base_name)
                    log_both(f"修复阶段识别到的逻辑分区: {', '.join(logical_partitions)}")
                    self.full_logical_partitions = []
                    for part_name in logical_partitions:
                        full_name = f"{part_name}_{current_slot}"
                        self.full_logical_partitions.append(full_name)
                        log_both(f"生成完整逻辑分区名: {full_name}")
                    failed_logical_parts = [part for part in failed_parts if part in logical_partitions]
                    failed_normal_parts = [part for part in failed_parts if part not in logical_partitions]
                    if failed_logical_parts:
                        log_both(f"检测到刷写失败的逻辑分区: {', '.join(failed_logical_parts)}，开始擦除并重建...")
                        if failed_normal_parts:
                            log_both(f"检测到刷写失败的普通分区: {', '.join(failed_normal_parts)}，这些分区只会重试刷写，不会重构")
                    else:
                        log_both("检测到刷写失败分区，但无逻辑分区需要重构")
                        if failed_normal_parts:
                            log_both(f"失败的普通分区: {', '.join(failed_normal_parts)}，这些分区只会重试刷写，不会重构")
                except Exception as e:
                    log_both(f"重新获取逻辑分区列表失败: {str(e)}")
                    logical_partitions = []
                    failed_logical_parts = []
                    failed_normal_parts = failed_parts
                retry_success = 0
                retry_failed = []
                for part_name in failed_normal_parts:
                    self._wait_if_paused()
                    img_file = None
                    for f in img_files_copy:
                        if os.path.splitext(f)[0].lower() == part_name:
                            img_file = f
                            break
                    if not img_file:
                        log_both(f"未找到普通分区 {part_name} 的img文件，跳过重试")
                        retry_failed.append(part_name)
                        continue
                    img_path = os.path.join(self.img_dir, img_file)
                    log_both(f"重试刷写普通分区: {part_name}")
                    ret = self.run_fastboot_cmd_realtime(["platform-tools\\fastboot", "flash", part_name, img_path])
                    if ret == 0:
                        retry_success += 1
                        log_both(f"重试刷写成功: {part_name}")
                        failed_parts.remove(part_name)
                    else:
                        log_both(f"重试刷写失败: {part_name}")
                        retry_failed.append(part_name)
                for part_name in failed_logical_parts:
                    self._wait_if_paused()
                    img_file = None
                    for f in img_files_copy:
                        if os.path.splitext(f)[0].lower() == part_name:
                            img_file = f
                            break
                    if not img_file:
                        log_both(f"未找到逻辑分区 {part_name} 的img文件，跳过重试")
                        retry_failed.append(part_name)
                        continue
                    full_partition_name = None
                    for full_name in self.full_logical_partitions:
                        if full_name == f"{part_name}_{current_slot}":
                            full_partition_name = full_name
                            break
                    if full_partition_name:
                        log_both(f"正在擦除分区: {full_partition_name}")
                        ret = self.run_fastboot_cmd_realtime(["platform-tools\\fastboot", "delete-logical-partition", full_partition_name])
                        if ret != 0:
                            log_both(f"擦除分区失败: {full_partition_name}")
                            retry_failed.append(part_name)
                            continue
                        log_both(f"正在重建分区: {full_partition_name}")
                        ret = self.run_fastboot_cmd_realtime(["platform-tools\\fastboot", "create-logical-partition", full_partition_name, "1"])
                        if ret != 0:
                            log_both(f"重建分区失败: {full_partition_name}")
                            retry_failed.append(part_name)
                            continue
                    else:
                        log_both(f"未找到分区 {part_name} 对应的完整逻辑分区名")
                        retry_failed.append(part_name)
                        continue
                    img_path = os.path.join(self.img_dir, img_file)
                    log_both(f"重新刷写分区: {part_name}")
                    ret = self.run_fastboot_cmd_realtime(["platform-tools\\fastboot", "flash", part_name, img_path])
                    if ret == 0:
                        retry_success += 1
                        log_both(f"重新刷写成功: {part_name}")
                        failed_parts.remove(part_name)
                    else:
                        log_both(f"重新刷写失败: {part_name}")
                        retry_failed.append(part_name)
                log_both(f"分区重试完成，成功: {retry_success} 个，失败: {len(retry_failed)} 个")
                if retry_failed:
                    messagebox.showwarning("分区重试失败", f"以下分区重试后仍失败: {', '.join(retry_failed)}\n请检查img文件或设备状态。")
                else:
                    messagebox.showinfo("分区重试成功", "所有分区重试后已成功刷写！")
            log_both("正在擦除谷歌账号...")
            self.run_fastboot_cmd_realtime(["platform-tools\\fastboot", "erase", "frp"])
            messagebox.showinfo("完成", "基本刷写完成")
            log_both("基本刷写完成")
            log_both("重启到bootloader以刷写modem分区")
            self.run_fastboot_cmd_realtime(["platform-tools\\fastboot", "reboot-bootloader"])
            import time
            for i in range(30):
                check_proc = subprocess.run(
                    ["platform-tools\\fastboot", "devices"],
                    capture_output=True, text=True
                )
                if check_proc.stdout.strip():
                    break
                time.sleep(1)
            with self._lock:
                modem_files = [f for f in self.img_files if "modem" in os.path.splitext(f)[0].lower()]
            log_both(f"检测到modem分区文件: {', '.join(modem_files) if modem_files else '无'}")
            success_count = 0
            for idx, img_file in enumerate(modem_files, 1):
                part_name = os.path.splitext(img_file)[0].lower()
                img_path = os.path.join(self.img_dir, img_file)
                progress_msg = f"({idx}/{len(modem_files)}) "
                log_msg = f"{progress_msg}开始刷写modem分区: {part_name} ({img_file})"
                log_both(log_msg)
                ret = self.run_fastboot_cmd_realtime(["platform-tools\\fastboot", "flash", part_name, img_path])
                if ret == 0:
                    log_both(f"{progress_msg}modem分区刷写成功: {part_name}")
                    success_count += 1
                else:
                    log_both(f"{progress_msg}modem分区刷写失败: {part_name}")
                    failed_parts.append(part_name)
            total_success = total_success + success_count
            msg = f"刷写完成！成功分区数量: {total_success}"
            if failed_parts:
                msg += f"\n失败分区: {', '.join(failed_parts)}"
            messagebox.showinfo("完成", msg)
            log_both(msg)
            self._save_flash_log(flash_log_lines)
            format_choice = messagebox.askyesnocancel(
                "格式化data", 
                "刷写完成，请选择格式化方式：\n\n"
                "是 = 重启到recovery手动格式化\n"
                "否 = 在fastboot中直接擦除userdata和metadata\n"
                "取消 = 跳过格式化（不推荐）\n\n"
                "注意：降级不格式化可能无法开机！"
            )
            if format_choice is True:  
                log_both("正在重启到recovery以便手动格式化数据分区...")
                self.run_fastboot_cmd_realtime(["platform-tools\\fastboot", "reboot", "recovery"])
                messagebox.showinfo(
                    "请手动格式化",
                    "设备已重启到recovery，请在recovery菜单中手动格式化数据分区，然后重启系统。"
                )
                log_both("已重启到recovery，请手动格式化数据分区")
            elif format_choice is False:  
                log_both("开始在fastboot中擦除userdata和metadata分区...")
                log_both("正在擦除userdata分区...")
                ret = self.run_fastboot_cmd_realtime(["platform-tools\\fastboot", "erase", "userdata"])
                if ret == 0:
                    log_both("userdata分区擦除成功")
                else:
                    log_both("userdata分区擦除失败")
                log_both("正在擦除metadata分区...")
                ret = self.run_fastboot_cmd_realtime(["platform-tools\\fastboot", "erase", "metadata"])
                if ret == 0:
                    log_both("metadata分区擦除成功")
                else:
                    log_both("metadata分区擦除失败")
                log_both("数据分区擦除完成，准备重启系统...")
                messagebox.showinfo(
                    "擦除完成", 
                    "userdata和metadata分区已擦除完成。\n"
                    "设备将重启到系统，首次开机可能需要较长时间。"
                )
                log_both("正在重启到系统...")
                self.run_fastboot_cmd_realtime(["platform-tools\\fastboot", "reboot"])
                log_both("设备已重启到系统")
            else:  
                log_both("用户选择跳过格式化，请注意：不格式化可能无法正常开机！")
                messagebox.showwarning(
                    "跳过格式化", 
                    "您选择了跳过格式化。\n"
                    "请注意：如果不格式化数据分区，设备可能无法正常开机。\n"
                    "如果遇到开机问题，请手动进入recovery进行格式化。"
                )
            self.enable_log_close_btn()
            try:
                out_dir = "修复分区"
                if os.path.exists(out_dir):
                    shutil.rmtree(out_dir)
            except Exception:
                pass
        except Exception as e:
            self.window.add_log(f"刷写分区异常: {str(e)}")
            if hasattr(self, "flash_log_lines"):
                self.flash_log_lines.append(f"刷写分区异常: {str(e)}")
            self._append_flash_log(f"刷写分区异常: {str(e)}")
            messagebox.showerror("错误", f"刷写分区异常: {str(e)}")
            self.enable_log_close_btn()
        self.window.after(0, lambda: self.step_btn.configure(
            text="已完成全部步骤",
            state="disabled"
        ))

    def _save_flash_log(self, log_lines):
        """只保存刷机日志到本地文件，不做任何上传"""
        import datetime
        import os
        log_dir = "data"
        os.makedirs(log_dir, exist_ok=True)
        import platform
        device_name = platform.node()
        log_file = os.path.join(log_dir, f"{device_name}.log")
        now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        extra_log = ""
        if hasattr(self, "log_textbox") and self.log_textbox:
            try:
                extra_log = self.log_textbox.get("1.0", "end").strip()
            except Exception:
                extra_log = ""
        merged_log = list(log_lines)
        if extra_log:
            for line in extra_log.splitlines():
                if line.strip() and line.strip() not in merged_log:
                    merged_log.append(line.strip())
        try:
            with open(log_file, "w", encoding="utf-8") as f:
                f.write("\n".join(merged_log))
            self.window.add_log(f"刷机日志已保存: {log_file}")
        except Exception as e:
            self.window.add_log(f"刷机日志保存失败: {str(e)}")

    def unpack_payload(self):
        """选择刷机包并在新cmd窗口中执行解包"""
        file_path = filedialog.askopenfilename(
            title="选择刷机包(payload.bin或zip文件)",
            filetypes=[("刷机包文件", "*.bin *.zip"), ("payload.bin", "*.bin"), ("zip文件", "*.zip"), ("所有文件", "*.*")]
        )
        if not file_path:
            return
        
        self._show_unpack_progress()
        
        import threading
        threading.Thread(
            target=self._thread_unpack_payload,
            args=(file_path,),
            daemon=True
        ).start()
        self.window.add_log(f"开始处理刷机包: {os.path.basename(file_path)}")

    def _show_unpack_progress(self):
        """显示解压进度UI"""
        for widget in self.img_list_frame.winfo_children():
            widget.destroy()
            
        customtkinter.CTkLabel(
            self.img_list_frame,
            text="解包进度",
            font=("微软雅黑", 14, "bold")
        ).pack(pady=5)
        
        self.unpack_progress = customtkinter.CTkProgressBar(self.img_list_frame, width=400)
        self.unpack_progress.pack(pady=10)
        self.unpack_progress.set(0)
        
        self.unpack_status = customtkinter.CTkLabel(
            self.img_list_frame,
            text="准备解压...",
            font=("微软雅黑", 12)
        )
        self.unpack_status.pack()

    def _thread_unpack_payload(self, file_path):
        """解包线程"""
        import os
        try:
            unpack_tool = "platform-tools\\payload-dumper-go.exe"
            images_dir = "images"
            os.makedirs(images_dir, exist_ok=True)
            payload_path = file_path
            if file_path.lower().endswith('.zip'):
                import zipfile
                import os
                zip_base = os.path.splitext(os.path.basename(file_path))[0]
                extract_dir = os.path.abspath(zip_base)
                os.makedirs(extract_dir, exist_ok=True)
                try:
                    self.window.after(0, lambda: (
                        self.unpack_status.configure(text="正在解压zip文件..."),
                        self.window.add_log("正在解压zip文件...")
                    ))
                    with zipfile.ZipFile(file_path, 'r') as zip_ref:
                        file_list = zip_ref.namelist()
                        model = None
                        android = None
                        if 'payload_properties.txt' in file_list:
                            with zip_ref.open('payload_properties.txt') as f:
                                content = f.read().decode(errors='ignore')
                                for line in content.splitlines():
                                    if line.startswith('ota_target_version='):
                                        model = line.split('=',1)[1].strip()
                                    if line.startswith('oplus_rom_version='):
                                        android = line.split('=',1)[1].strip()
                            if model:
                                self.window.after(0, lambda: self.window.add_log(f"机型: {model}"))
                            if android:
                                self.window.after(0, lambda: self.window.add_log(f"安卓版本: {android}"))
                            def ask_continue():
                                msg = f"检测到刷机包信息：\n机型: {model or '未知'}\n安卓版本: {android or '未知'}\n\n是否继续解压？"
                                return messagebox.askyesno("刷机包信息确认", msg)
                            result = [None]  # type: list[object]
                            def ask():
                                result[0] = ask_continue()
                            self.window.after(0, ask)
                            import time
                            while result[0] is None:
                                time.sleep(0.05)
                            if not result[0]:
                                self.window.after(0, lambda: self.unpack_status.configure(text="用户取消解压"))
                                return
                        total = len(file_list)
                        payload_files = [f for f in file_list if f.lower().endswith('payload.bin')]
                        if not payload_files:
                            self.window.after(0, lambda: self._safe_messagebox_error("zip文件中未找到payload.bin文件"))
                            return
                        payload_in_zip = payload_files[0]
                        for idx, member in enumerate(file_list, 1):
                            zip_ref.extract(member, extract_dir)
                            progress = idx / total
                            self.window.after(0, lambda p=progress: self.unpack_progress.set(p))
                    payload_path = os.path.join(extract_dir, payload_in_zip)
                    self.window.after(0, lambda: (
                        self.unpack_progress.set(1),
                        self.unpack_status.configure(text="解压完成"),
                        self.window.add_log(f"系统解压完成: {payload_in_zip}")
                    ))
                    unpack_tool = "platform-tools\\payload-dumper-go.exe"
                    images_dir = "images"
                    os.makedirs(images_dir, exist_ok=True)
                    cmd = f'platform-tools\\payload-dumper-go.exe -c 128 -o images "{payload_path}"'
                    self.window.after(0, lambda: self.window.add_log(f"启动解包进程: {os.path.basename(payload_path)}"))
                    import subprocess
                    import threading
                    
                    def monitor_unpack():
                        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8')
                        stdout, stderr = proc.communicate()
                        if proc.returncode != 0 or stderr.strip():
                            self.window.after(0, lambda: self._safe_messagebox_error(f"解包过程出现错误:\n{stderr.strip()}"))
                    
                    threading.Thread(target=monitor_unpack, daemon=True).start()
                    
                    subprocess.Popen(
                        f'start cmd /k "{cmd} && echo 解包完成! && pause"',
                        shell=True,
                        creationflags=subprocess.CREATE_NEW_CONSOLE
                    )
                    self.window.after(0, lambda: self.window.add_log(f"解包进程已启动，输出目录: images"))
                    self.window.after(0, lambda: self._safe_messagebox_info(
                        f"已在独立窗口启动解包进程\n\n"
                        f"刷机包: {os.path.basename(payload_path)}\n"
                        f"输出目录: images\n\n"
                        "解包完成后请检查images目录中的img文件"
                    ))
                    return
                except Exception as e:
                    self.window.after(0, lambda: (
                        self.unpack_status.configure(text="解压失败"),
                        self.window.add_log(f"系统解压失败: {str(e)}"),
                        self._safe_messagebox_error("系统解压失败: " + str(e))
                    ))
                    return
            
            cmd = f'platform-tools\\payload-dumper-go.exe -c 128 -o images "{payload_path}"'
            self.window.after(0, lambda: self.window.add_log(f"启动解包进程: {os.path.basename(payload_path)}"))
            
            
            import subprocess
            import threading
            
            def monitor_unpack():
                proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8')
                stdout, stderr = proc.communicate()
                if proc.returncode != 0 or stderr.strip():
                    self.window.after(0, lambda: self._safe_messagebox_error(f"解包过程出现错误:\n{stderr.strip()}"))
            
            
            threading.Thread(target=monitor_unpack, daemon=True).start()
            
            
            subprocess.Popen(
                f'start cmd /k "{cmd} && echo 解包完成! && pause"',
                shell=True,
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
            self.window.after(0, lambda: self.window.add_log(f"解包进程已启动，输出目录: images"))
            self.window.after(0, lambda: self._safe_messagebox_info(
                f"已在独立窗口启动解包进程\n\n"
                f"刷机包: {os.path.basename(payload_path)}\n"
                f"输出目录: images\n\n"
                "解包完成后请检查images目录中的img文件"
            ))
        except Exception as e:
            self.window.after(0, lambda: self._safe_messagebox_error(f"解包过程异常: {str(e)}"))

    def _append_flash_log(self, msg):
        """在刷写日志文本框和实时日志弹窗中追加日志"""
        from datetime import datetime
        ts = datetime.now().strftime("%H:%M:%S")
        if hasattr(self, "flash_log_text") and self.flash_log_text:
            self.flash_log_text.insert("end", f"[{ts}] {msg}\n")
            self.flash_log_text.see("end")
        if hasattr(self, "log_textbox") and self.log_textbox:
            self.log_textbox.insert("end", f"[{ts}] {msg}\n")
            self.log_textbox.see("end")

    def fastbootd_repair(self, folder_path=None):
        """直接选择文件夹并执行修复，无需手动选"""
        import os
        from tkinter import messagebox
        if folder_path is None:
            folder_path = os.path.abspath("修复分区")
        if not os.path.exists(folder_path):
            messagebox.showerror("错误", f"未找到修复分区目录: {folder_path}")
            return
        self._process_img_folder_and_reboot(folder_path)

    def _process_img_folder_and_reboot(self, folder_path):
        """处理img文件夹并重启到Fastboot"""
        try:
            if not os.path.exists(folder_path):
                messagebox.showerror("错误", "选择的文件夹不存在")
                return
            
            img_files = [f for f in os.listdir(folder_path) if f.lower().endswith('.img')]
            if not img_files:
                messagebox.showerror("错误", "选择的文件夹中没有找到img文件")
                return
            
            original_count = len(img_files)
            img_files = [f for f in img_files if 'preloader_raw' not in f.lower()]
            if original_count > len(img_files):
                skipped_count = original_count - len(img_files)
                self.window.add_log(f'已跳过preloader_raw分区：{skipped_count}个文件')
            
            self.img_dir = folder_path
            with self._lock:
                self.img_files = img_files
            
            self.window.add_log(f"已选择img文件夹: {folder_path}")
            self.window.add_log(f"检测到img文件: {', '.join(img_files)}")
            
            self._show_repair_progress()
            
            import threading
            threading.Thread(target=self._thread_process_img_folder, daemon=True).start()
            
        except Exception as e:
            messagebox.showerror("错误", f"处理img文件夹失败: {str(e)}")



    def _thread_process_img_folder(self):
        """在后台线程中处理img文件夹"""
        try:
            self.window.add_log("开始处理img文件夹...")
            self.window.add_log("正在重启设备到Fastboot模式...")
            subprocess.run(
                ["platform-tools\\fastboot", "reboot-bootloader"],
                capture_output=True, text=True
            )
            import time
            for i in range(30):
                time.sleep(1)
                try:
                    result = subprocess.run(
                        ["platform-tools\\fastboot", "devices"],
                        capture_output=True, text=True
                    )
                    if result.stdout.strip():
                        break
                except:
                    pass
            self.window.add_log("设备已重启到Fastboot模式")
            time.sleep(5)
            state2 = self._detect_device_state()
            if state2 == "fastboot":
                self.window.add_log("复查：设备依然处于fastboot模式。")
            else:
                self.window.add_log(f"复查失败：设备未保持在fastboot模式，当前为{state2 or '未知'}。")
                self.window.after(0, lambda: self._safe_messagebox_error(f"设备未保持在fastboot模式，当前为{state2 or '未知'}。"))
                return
            self._execute_repair_flow()
            
        except Exception as e:
            self.window.add_log(f"处理img文件夹失败: {str(e)}")
            messagebox.showerror("错误", f"处理img文件夹失败: {str(e)}")
        finally:
            self.window.after(0, lambda: self.repair_progress.set(1))

    def _execute_repair_flow(self):
        """执行修复流程：识别平台、刷写关键分区、重启到fastbootd"""
        import time
        try:
            getvar = subprocess.run(
                ["platform-tools\\fastboot", "getvar", "hardware"],
                capture_output=True, text=True
            )
            hw_info = (getvar.stdout + getvar.stderr).lower()
        except Exception:
            hw_info = ""
        if "mt" in hw_info or "mediatek" in hw_info:
            key_parts = [
                "boot.img", "lk.img", "dtbo.img", "md1img.img", "vbmeta.img", "vendor_boot.img"
            ]
            platform_name = "联发科"
        else:
            key_parts = [
                "boot.img", "recovery.img", "dtbo.img", "modem.img", "vbmeta.img", "vendor_boot.img"
            ]
            platform_name = "高通"
        state = self._detect_device_state()
        if state != "fastboot":
            self._safe_messagebox_error("请将设备重启到Bootloader模式后再执行修复")
            return
        img_map = {}
        with self._lock:
            img_files_copy = self.img_files.copy()
        for name in key_parts:
            for f in img_files_copy:
                if f.lower() == name:
                    img_map[name] = os.path.join(self.img_dir, f)
                    break
        total = len([k for k in key_parts if k in img_map])
        if total == 0:
            self._safe_messagebox_info("未找到任何关键分区文件，跳过刷写步骤")
            return
        idx = 0
        for part in key_parts:
            if part not in img_map:
                continue
            part_name = part.replace(".img", "")
            img_path = img_map[part]
            idx += 1
            self.window.after(0, lambda p=idx, t=total: self.repair_progress.set(p / t))
            try:
                result = subprocess.run(
                    ["platform-tools\\fastboot", "flash", part_name, img_path],
                    capture_output=True, text=True
                )
            except Exception as e:
                pass
            time.sleep(0.5)
        self.repair_progress.set(1)
        time.sleep(0.5)
        try:
            subprocess.run(
                ["platform-tools\\fastboot", "reboot", "fastboot"],
                capture_output=True, text=True
            )
            self._safe_messagebox_info("关键分区修复已完成，设备已重启到fastbootd模式")
        except Exception as e:
            self._safe_messagebox_error(f"重启到fastbootd失败: {str(e)}")

    def _show_repair_progress(self):
        for widget in self.img_list_frame.winfo_children():
            widget.destroy()
        customtkinter.CTkLabel(
            self.img_list_frame,
            text="正在修复中，请勿操作手机和程序...",
            font=("微软雅黑", 16, "bold"),
            text_color="orange"
        ).pack(pady=40)
        self.repair_progress = customtkinter.CTkProgressBar(self.img_list_frame, width=400)
        self.repair_progress.pack(pady=20)
        self.repair_progress.set(0)



    def show_realtime_log_window(self):
        import customtkinter
        prev_log = ""
        if hasattr(self, "log_textbox") and self.log_textbox:
            try:
                prev_log = self.log_textbox.get("1.0", "end")
            except Exception:
                prev_log = ""
        if hasattr(self, "log_win") and self.log_win and self.log_win.winfo_exists():
            self.log_win.destroy()
        self.log_win = customtkinter.CTkToplevel(self.window)
        self.log_win.title("Fastboot 实时日志")
        self.log_win.geometry("800x600")
        self.log_win.protocol("WM_DELETE_WINDOW", lambda: None)  # 禁止直接关闭
        self.log_win.attributes('-topmost', True)  # 置顶
        self.log_textbox = customtkinter.CTkTextbox(self.log_win, font=("Consolas", 11))
        self.log_textbox.pack(fill="both", expand=True, padx=10, pady=10)
        if prev_log.strip():
            self.log_textbox.insert("end", prev_log)
        else:
            self.log_textbox.insert("end", "刷写日志:\n")
        self.log_textbox.see("end")
        btn_frame = customtkinter.CTkFrame(self.log_win)
        btn_frame.pack(pady=10)
        if not hasattr(self, "_flash_paused"):
            self._flash_paused = False
        def do_pause():
            self._flash_paused = True
            pause_btn.configure(state="disabled")
            resume_btn.configure(state="normal")
            self._append_flash_log("[操作] 已暂停刷写流程")
        def do_resume():
            self._flash_paused = False
            pause_btn.configure(state="normal")
            resume_btn.configure(state="disabled")
            self._append_flash_log("[操作] 已继续刷写流程")
        pause_btn = customtkinter.CTkButton(
            btn_frame,
            text="暂停",
            width=120,
            font=("微软雅黑", 12),
            command=do_pause,
            state="normal"
        )
        pause_btn.pack(side="left", padx=10)
        resume_btn = customtkinter.CTkButton(
            btn_frame,
            text="继续",
            width=120,
            font=("微软雅黑", 12),
            command=do_resume,
            state="disabled"
        )
        resume_btn.pack(side="left", padx=10)
        self.close_btn = customtkinter.CTkButton(
            btn_frame,
            text="安全关闭",
            command=self.log_win.destroy,
            width=120,
            font=("微软雅黑", 12),
            state="disabled"
        )
        self.close_btn.pack(side="left", padx=10)

    def _check_fastboot_error_and_hint(self, output):
        """检测fastboot输出中的常见错误并弹窗提示"""
        for key, hint in FASTBOOT_ERROR_HINTS:
            if key.lower() in output.lower():
                from tkinter import messagebox
                self.window.add_log(f"检测到Fastboot错误：{key} => {hint}")
                messagebox.showerror("Fastboot错误提示", f"检测到错误：{key}\n\n{hint}")
                break

    def run_fastboot_cmd_realtime(self, cmd):
        import subprocess
        self.log_textbox.insert("end", f"正在执行刷写操作...\n")
        self.log_textbox.see("end")
        self.log_textbox.update()
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        output_lines = []
        if proc.stdout is not None:
            for line in iter(proc.stdout.readline, ''):
                self.log_textbox.insert("end", line)
                self.log_textbox.see("end")
                self.log_textbox.update()
                output_lines.append(line)
            proc.stdout.close()
        proc.wait()
        self._check_fastboot_error_and_hint(''.join(output_lines))
        return proc.returncode

    def enable_log_close_btn(self):
        if hasattr(self, 'close_btn'):
            self.close_btn.configure(state="normal")

    def _open_url(self, url):
        import webbrowser
        webbrowser.open(url)

    def _wait_if_paused(self):
        while getattr(self, "_flash_paused", False):
            import time
            time.sleep(0.2)
            if hasattr(self, "window"):
                try:
                    self.window.update()
                except Exception:
                    pass