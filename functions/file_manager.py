import os
import subprocess
import customtkinter
from tkinter import messagebox, filedialog

class FileManager:
    def __init__(self, window):
        self.window = window
        self.current_dir = "/storage/emulated/0"  
        self.path_var = customtkinter.StringVar()
        self.path_var.set(f"当前路径: {self.current_dir}")

    def manage_files(self):
        self.window.clear_main_frame()
        
        title_frame = customtkinter.CTkFrame(self.window.main_frame)
        title_frame.pack(fill="x", padx=20, pady=(0,10))
        
        customtkinter.CTkLabel(
            title_frame,
            text="文件管理",
            font=("微软雅黑", 24, "bold")
        ).pack(side="left", padx=20)
        
        path_frame = customtkinter.CTkFrame(self.window.main_frame)
        path_frame.pack(fill="x", padx=20, pady=5)
        
        customtkinter.CTkLabel(
            path_frame,
            textvariable=self.path_var,
            font=("微软雅黑", 12)
        ).pack(fill="x", padx=10)
        
        list_frame = customtkinter.CTkFrame(self.window.main_frame)
        list_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.file_list = customtkinter.CTkScrollableFrame(list_frame)
        self.file_list.pack(fill="both", expand=True)
        
        button_frame = customtkinter.CTkFrame(self.window.main_frame)
        button_frame.pack(fill="x", padx=20, pady=10)
        
        buttons = [
            ("⬆️ 返回上级", self.go_up),
            ("🔄 刷新", self.refresh_files),
            ("📥 提取文件", self.pull_file),
            ("📤 推送文件", self.push_file)
        ]
        
        for text, cmd in buttons:
            customtkinter.CTkButton(
                button_frame,
                text=text,
                command=cmd,
                width=120,
                height=32,
                font=("微软雅黑", 12)
            ).pack(side="left", padx=5)

        self.refresh_files()
        self.window.add_log(f"打开目录: {self.current_dir}")

    def refresh_files(self):
        self.path_var.set(f"当前路径: {self.current_dir}")
        for widget in self.file_list.winfo_children():
            widget.destroy()
            
        try:
            result = subprocess.run(
                ["platform-tools\\adb.exe", "shell", "ls", "-la", self.current_dir],
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            
            if result.returncode == 0 and result.stdout:
                files = result.stdout.splitlines()
                
                if self.current_dir != "/storage/emulated/0":
                    back_frame = customtkinter.CTkFrame(self.file_list)
                    back_frame.pack(fill="x", padx=5, pady=2)
                    back_label = customtkinter.CTkLabel(
                        back_frame,
                        text="📁 ..",
                        font=("微软雅黑", 12),
                        anchor="w"
                    )
                    back_label.pack(fill="x", padx=10, pady=5)
                    back_label.bind("<Button-1>", lambda e: self.go_up())

                for line in files:
                    if line.strip() and not line.startswith("total"):
                        try:
                            parts = line.split(None, 8)  
                            if len(parts) >= 8:
                                perms = parts[0]
                                name = parts[-1]
                                if name in [".", ".."]:
                                    continue
                                    
                                item_frame = customtkinter.CTkFrame(self.file_list)
                                item_frame.pack(fill="x", padx=5, pady=2)
                                
                                icon = "📁 " if perms.startswith("d") else "📄 "
                                
                                label = customtkinter.CTkLabel(
                                    item_frame,
                                    text=f"{icon}{name}",
                                    font=("微软雅黑", 12),
                                    anchor="w"
                                )
                                label.pack(fill="x", padx=10, pady=5)
                                
                                if perms.startswith("d"):
                                    label.bind("<Button-1>", lambda e, n=name: self.enter_directory(n))
                                else:
                                    label.bind("<Button-1>", lambda e, n=name: self._show_file_dialog(n))
                        except:
                            continue
                            
            else:
                self.window.add_log(f"获取文件列表失败: {result.stderr}")
                customtkinter.CTkLabel(
                    self.file_list,
                    text="无法读取此目录，请检查权限",
                    font=("微软雅黑", 12)
                ).pack(pady=10)
                
        except Exception as e:
            self.window.add_log(f"刷新文件列表失败: {str(e)}")
            messagebox.showerror("错误", str(e))

    def enter_directory(self, name):
        if name in [".", ".."]:
            return
            
        self.current_dir = os.path.normpath(os.path.join(self.current_dir, name)).replace("\\", "/")
        self.path_var.set(f"当前路径: {self.current_dir}")
        self.refresh_files()
        self.window.add_log(f"进入目录: {self.current_dir}")

    def go_up(self):
        if self.current_dir != "/storage/emulated/0":
            self.current_dir = os.path.normpath(os.path.dirname(self.current_dir)).replace("\\", "/")
            self.path_var.set(f"当前路径: {self.current_dir}")
            self.refresh_files()
            self.window.add_log(f"返回上级: {self.current_dir}")

    def pull_file(self):
        pass

    def _show_file_dialog(self, filename):
        full_path = os.path.join(self.current_dir, filename).replace("\\", "/")
        action = messagebox.askquestion("文件操作", f"请选择要对文件 {filename} 执行的操作：\n是=提取，否=删除，取消=不操作", icon='question', type='yesnocancel')
        if action == 'yes':
            save_path = filedialog.asksaveasfilename(
                title="保存文件",
                initialfile=filename,
                filetypes=[('所有文件', '*.*')]
            )
            if save_path:
                try:
                    result = subprocess.run(
                        ["platform-tools\\adb.exe", "pull", full_path, save_path],
                        capture_output=True,
                        text=True
                    )
                    if result.returncode == 0:
                        self.window.add_log(f"文件已保存到: {save_path}")
                        messagebox.showinfo("成功", "文件提取成功！")
                    else:
                        raise Exception(result.stderr)
                except Exception as e:
                    self.window.add_log(f"文件提取失败: {str(e)}")
                    messagebox.showerror("错误", f"提取失败: {str(e)}")
        elif action == 'no':    
            if messagebox.askyesno("确认删除", f"确定要删除文件: {filename} 吗？此操作不可恢复！"):
                try:
                    result = subprocess.run(
                        ["platform-tools\\adb.exe", "shell", "rm", f'\"{full_path}\"'],
                        capture_output=True,
                        text=True
                    )
                    if result.returncode == 0:
                        self.window.add_log(f"已删除文件: {full_path}")
                        messagebox.showinfo("成功", "文件删除成功！")
                        self.refresh_files()
                    else:
                        raise Exception(result.stderr)
                except Exception as e:
                    self.window.add_log(f"文件删除失败: {str(e)}")
                    messagebox.showerror("错误", f"删除失败: {str(e)}")

    def push_file(self):
        file_path = filedialog.askopenfilename(title="选择要推送的文件", filetypes=[('所有文件', '*.*')])
        if file_path:
            if messagebox.askyesno("确认", f"是否要推送文件到当前目录: {self.current_dir}?"):
                try:
                    filename = os.path.basename(file_path)
                    dest_path = f"{self.current_dir}/{filename}"
                    
                    result = subprocess.run(
                        ["platform-tools\\adb.exe", "push", file_path, dest_path],
                        capture_output=True,
                        text=True
                    )
                    
                    if result.returncode == 0:
                        self.window.add_log(f"文件已推送到: {dest_path}")
                        messagebox.showinfo("成功", "文件推送成功！")
                        self.refresh_files()  
                    else:
                        raise Exception(result.stderr)
                except Exception as e:
                    self.window.add_log(f"文件推送失败: {str(e)}")
                    messagebox.showerror("错误", f"推送失败: {str(e)}")
