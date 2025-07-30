import customtkinter
import subprocess
import threading
from tkinter import messagebox

class AppManager:
    def __init__(self, window):
        self.window = window
        self.app_list = []
        
    def show_menu(self):
        self.window.clear_main_frame()
        
        customtkinter.CTkLabel(
            self.window.main_frame,
            text="应用管理",
            font=("微软雅黑", 24, "bold")
        ).pack(pady=20)

        search_frame = customtkinter.CTkFrame(self.window.main_frame)
        search_frame.pack(fill="x", padx=20, pady=10)
        
        customtkinter.CTkLabel(
            search_frame,
            text="输入应用包名:",
            font=("微软雅黑", 12)
        ).pack(side="left", padx=10)
        
        self.search_var = customtkinter.StringVar()
        self.search_var.trace_add("write", self._on_search_change)
        search_entry = customtkinter.CTkEntry(
            search_frame,
            textvariable=self.search_var,
            width=400,
            placeholder_text="输入完整或部分包名, 例如: com.android.settings"
        )
        search_entry.pack(side="left", padx=10)

        self.result_frame = customtkinter.CTkScrollableFrame(
            self.window.main_frame,
            height=400
        )
        self.result_frame.pack(fill="both", expand=True, padx=20, pady=10)

        customtkinter.CTkLabel(
            self.result_frame,
            text="请输入要操作的应用包名",
            font=("微软雅黑", 12)
        ).pack(pady=10)

    def _on_search_change(self, *args):
        search_text = self.search_var.get().strip()
        if len(search_text) < 3:
            return
            
        for widget in self.result_frame.winfo_children():
            widget.destroy()

        try:
            result = subprocess.run(
                ["platform-tools\\adb.exe", "shell", "pm", "list", "packages", "-f", search_text],
                capture_output=True, text=True
            )
            
            if result.returncode != 0:
                raise Exception(result.stderr)

            packages = []
            for line in result.stdout.splitlines():
                if line.strip() and line.startswith("package:"):
                    line = line.replace("package:", "")
                    pkg = line.split("=")[-1]  
                    packages.append(pkg)
                    
            if packages:
                for pkg in packages:
                    self._show_package_item(pkg)
            else:
                customtkinter.CTkLabel(
                    self.result_frame,
                    text="未找到匹配的应用",
                    font=("微软雅黑", 12)
                ).pack(pady=10)
                
        except Exception as e:
            self.window.add_log(f"搜索应用失败: {str(e)}")
            customtkinter.CTkLabel(
                self.result_frame,
                text=f"搜索失败: {str(e)}",
                font=("微软雅黑", 12),
                text_color="red"
            ).pack(pady=10)

    def _show_package_item(self, pkg):
        item_frame = customtkinter.CTkFrame(self.result_frame)
        item_frame.pack(fill="x", padx=5, pady=2)
        
        type_result = subprocess.run(
            ["platform-tools\\adb.exe", "shell", "pm", "path", pkg],
            capture_output=True, text=True
        )
        is_system = "/system/" in type_result.stdout
        
        tag = "[系统应用]" if is_system else "[用户应用]"
        customtkinter.CTkLabel(
            item_frame,
            text=f"{pkg} {tag}",
            font=("微软雅黑", 12),
            anchor="w"
        ).pack(side="left", padx=10, pady=5)

        btn_frame = customtkinter.CTkFrame(item_frame, fg_color="transparent")
        btn_frame.pack(side="right", padx=10)
        
        customtkinter.CTkButton(
            btn_frame,
            text="停止",
            command=lambda: self.force_stop(pkg),
            width=80,
            height=30
        ).pack(side="left", padx=5)
        
        customtkinter.CTkButton(
            btn_frame,
            text="清除数据",
            command=lambda: self.clear_data(pkg),
            width=80,
            height=30
        ).pack(side="left", padx=5)
        
        customtkinter.CTkButton(
            btn_frame,
            text="卸载",
            command=lambda: self.uninstall(pkg),
            width=80,
            height=30,
            fg_color="red"
        ).pack(side="left", padx=5)

    def force_stop(self, package):
        try:
            if not messagebox.askyesno("确认", f"确定要强制停止应用 {package} 吗?"):
                return
                
            result = subprocess.run(
                ["platform-tools\\adb.exe", "shell", "am", "force-stop", package],
                capture_output=True, text=True
            )
            
            if result.returncode == 0:
                self.window.add_log(f"已强制停止应用: {package}")
                messagebox.showinfo("成功", "应用已停止")
            else:
                raise Exception(result.stderr)
                
        except Exception as e:
            error_msg = f"停止应用失败: {str(e)}"
            self.window.add_log(error_msg)
            messagebox.showerror("错误", error_msg)

    def clear_data(self, package):
        try:
            if not messagebox.askyesno("警告", 
                f"确定要清除应用 {package} 的全部数据吗?\n"
                "此操作将删除应用所有数据且不可恢复"):
                return
                
            result = subprocess.run(
                ["platform-tools\\adb.exe", "shell", "pm", "clear", package],
                capture_output=True, text=True
            )
            
            if result.returncode == 0:
                self.window.add_log(f"已清除应用数据: {package}")
                messagebox.showinfo("成功", "应用数据已清除")
            else:
                raise Exception(result.stderr)
                
        except Exception as e:
            error_msg = f"清除数据失败: {str(e)}"
            self.window.add_log(error_msg)
            messagebox.showerror("错误", error_msg)

    def uninstall(self, package):                   
        try:
            if not messagebox.askyesno("警告",
                f"确定要卸载应用 {package} 吗?\n"
                "此操作将删除应用且不可恢复"):
                return
                
            cmd = ["platform-tools\\adb.exe", "uninstall"]
            if package.startswith("com.android") or package.startswith("android"):
                if not messagebox.askyesno("警告",
                    "警告:你正在尝试卸载系统应用\n"
                    "这可能导致设备无法正常工作\n\n"
                    "是否继续?"):
                    return
                cmd.append("--user 0")
                
            cmd.append(package)
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if "Success" in result.stdout:
                self.window.add_log(f"已卸载应用: {package}")
                messagebox.showinfo("成功", "应用已卸载")
            else:
                raise Exception(result.stderr)
                
        except Exception as e:
            error_msg = f"卸载失败: {str(e)}"
            self.window.add_log(error_msg)
            messagebox.showerror("错误", error_msg)
