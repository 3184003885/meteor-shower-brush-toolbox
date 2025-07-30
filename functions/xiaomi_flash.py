import os
import customtkinter
from tkinter import filedialog, messagebox
import subprocess
import threading

class XiaomiFlash:
    def __init__(self, main_window):
        self.main_window = main_window
        self.content_frame = main_window.main_frame

    def clear_content(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def show_menu(self):
        self.clear_content()
        
        customtkinter.CTkLabel(
            self.content_frame,
            text="小米线刷工具",
            font=("微软雅黑", 24, "bold")
        ).pack(pady=20)

        script_frame = customtkinter.CTkFrame(self.content_frame)
        script_frame.pack(fill="x", padx=30, pady=10)

        customtkinter.CTkLabel(
            script_frame,
            text="请选择要执行的刷机脚本文件 (.bat)",
            font=("微软雅黑", 14)
        ).pack(pady=10)

        select_btn = customtkinter.CTkButton(
            script_frame,
            text="选择刷机脚本",
            command=self.select_flash_script,
            width=200,
            height=40,
            font=("微软雅黑", 13)
        )
        select_btn.pack(pady=10)

        note_frame = customtkinter.CTkFrame(self.content_frame)
        note_frame.pack(fill="x", padx=30, pady=20)

        customtkinter.CTkLabel(
            note_frame,
            text="注意事项",
            font=("微软雅黑", 16, "bold")
        ).pack(pady=10)

        notes = """
• 请确保设备已进入fastboot模式
• 建议使用小米官方刷机包
• 请选择正确的批处理(.bat)脚本
• 刷机过程中请勿断开设备连接
• 刷机前请先备份重要数据
        """
        
        customtkinter.CTkLabel(
            note_frame,
            text=notes,
            font=("微软雅黑", 13),
            justify="left"
        ).pack(padx=20, pady=10)

    def select_flash_script(self):
        script_path = filedialog.askopenfilename(
            title="选择刷机脚本",
            filetypes=[("批处理文件", "*.bat"), ("所有文件", "*.*")]
        )
        if not script_path:
            return

        self.clear_content()

        output_frame = customtkinter.CTkFrame(self.content_frame)
        output_frame.pack(fill="both", expand=True, padx=30, pady=20)

        customtkinter.CTkLabel(
            output_frame,
            text="刷机过程",
            font=("微软雅黑", 16, "bold")
        ).pack(pady=10)

        self.output_text = customtkinter.CTkTextbox(
            output_frame,
            font=("Consolas", 12),
            wrap="word"
        )
        self.output_text.pack(fill="both", expand=True, padx=10, pady=10)
    
        button_frame = customtkinter.CTkFrame(output_frame)
        button_frame.pack(fill="x", padx=10, pady=10)

        start_button = customtkinter.CTkButton(
            button_frame,
            text="开始刷机",
            command=lambda: threading.Thread(
                target=self.execute_script,
                args=(script_path,),
                daemon=True
            ).start(),
            width=150,
            height=35,
            font=("微软雅黑", 13)
        )
        start_button.pack(side="left", padx=10)

        back_button = customtkinter.CTkButton(
            button_frame,
            text="返回主菜单",
            command=self.show_menu,
            width=150,
            height=35,
            font=("微软雅黑", 13)
        )
        back_button.pack(side="left", padx=10)

    def execute_script(self, script_path):
        try:
            script_dir = os.path.dirname(script_path)
            script_name = os.path.basename(script_path)
            original_dir = os.getcwd()
            
            os.chdir(script_dir)
            process = subprocess.Popen(
                script_name,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='gbk',
                creationflags=subprocess.CREATE_NO_WINDOW
            )

            for line in iter(process.stdout.readline, ''):
                if not line:
                    break
                self.output_text.insert('end', line)
                self.output_text.see('end')
                self.content_frame.update()

            os.chdir(original_dir)
            process.wait()
            
            self.output_text.insert('end', "\n执行完成!\n")
            self.output_text.see('end')
            
        except Exception as e:
            error_msg = f"\n执行过程中出错: {str(e)}\n"
            self.output_text.insert('end', error_msg)
            self.output_text.see('end')
            messagebox.showerror("错误", error_msg)