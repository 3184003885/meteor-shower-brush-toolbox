import os
import subprocess
import customtkinter
from tkinter import messagebox, filedialog

class AppInstaller:
    def __init__(self, window):
        self.window = window
        self.selected_apks = []
        
    def show_installer(self):
        self.window.clear_main_frame()
        
        customtkinter.CTkLabel(
            self.window.main_frame,
            text="批量安装应用",
            font=("微软雅黑", 24, "bold")
        ).pack(pady=20)

        customtkinter.CTkLabel(
            self.window.main_frame,
            text="支持选择多个APK文件或整个文件夹进行批量安装",
            font=("微软雅黑", 12)
        ).pack(pady=(0, 10))
        
        btn_frame = customtkinter.CTkFrame(self.window.main_frame)
        btn_frame.pack(pady=10)
        
        customtkinter.CTkButton(
            btn_frame,
            text="选择APK文件",
            command=self.select_apks,
            width=150,
            height=32,
            font=("微软雅黑", 12)
        ).pack(side="left", padx=5)

        customtkinter.CTkButton(
            btn_frame,
            text="选择文件夹",
            command=self.select_folder,
            width=150,
            height=32,
            font=("微软雅黑", 12)
        ).pack(side="left", padx=5)
        
        list_frame = customtkinter.CTkFrame(self.window.main_frame)
        list_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.apk_list = customtkinter.CTkTextbox(
            list_frame,
            font=("微软雅黑", 12),
            height=300
        )
        self.apk_list.pack(fill="both", expand=True, padx=10, pady=10)
        
        control_frame = customtkinter.CTkFrame(self.window.main_frame)
        control_frame.pack(pady=10)
        
        buttons = [
            ("开始安装", self.install_selected, "green"),
            ("清空列表", self.clear_list, None)
        ]
        
        for text, cmd, color in buttons:
            btn = customtkinter.CTkButton(
                control_frame,
                text=text,
                command=cmd,
                width=120,
                height=32,
                font=("微软雅黑", 12),
                fg_color=color if color else None
            )
            btn.pack(side="left", padx=5)

    def select_apks(self):
        files = filedialog.askopenfilenames(
            title="选择APK文件",
            filetypes=[("APK文件", "*.apk"), ("所有文件", "*.*")]
        )
        if files:
            self.add_apks(files)

    def select_folder(self):
        folder = filedialog.askdirectory(title="选择APK文件夹")
        if folder:
            apks = [os.path.join(folder, f) for f in os.listdir(folder) if f.lower().endswith('.apk')]
            if apks:
                self.add_apks(apks)
            else:
                messagebox.showinfo("提示", "所选文件夹中没有APK文件")

    def add_apks(self, apk_paths):
        for path in apk_paths:
            if path not in self.selected_apks:
                self.selected_apks.append(path)
                self.apk_list.insert("end", f"{os.path.basename(path)}\n")
        self.window.add_log(f"已添加 {len(apk_paths)} 个APK文件")

    def select_all(self):
        self.apk_list.select_set(0, tk.END)

    def deselect_all(self):     
        self.apk_list.selection_clear(0, tk.END)

    def clear_list(self):
        self.selected_apks.clear()
        self.apk_list.delete("0.0", "end")
        self.window.add_log("已清空安装列表")

    def install_selected(self):
        if not self.selected_apks:
            messagebox.showinfo("提示", "请选择要安装的APK")
            return
            
        total = len(self.selected_apks)
        if not messagebox.askyesno("确认", f"确定要安装选中的 {total} 个应用吗？"):
            return
            
        success = 0
        failed = 0
        self.window.add_log(f"开始安装 {total} 个应用...")
        
        for apk_path in self.selected_apks:
            apk_name = os.path.basename(apk_path)
            self.window.add_log(f"正在安装: {apk_name}")
            
            try:
                result = subprocess.run(
                    ["platform-tools\\adb.exe", "install", "-r", apk_path],
                    capture_output=True,
                    text=True,
                    encoding='utf-8'
                )
                if "Success" in result.stdout:
                    success += 1
                    self.window.add_log(f"{apk_name} 安装成功")
                else:
                    failed += 1
                    self.window.add_log(f"{apk_name} 安装失败: {result.stderr}")
            except Exception as e:
                failed += 1
                self.window.add_log(f"{apk_name} 安装异常: {str(e)}")
                
        self.window.add_log(f"安装完成: {success} 成功, {failed} 失败")
        messagebox.showinfo("完成", f"安装完成\n成功: {success}\n失败: {failed}")
