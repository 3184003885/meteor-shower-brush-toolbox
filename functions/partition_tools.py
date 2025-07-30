import customtkinter
import subprocess
import os
from tkinter import messagebox, filedialog

class PartitionTools:
    def __init__(self, window):
        self.window = window
        self.backup_dir = os.path.join("downloads", "partitions")
        os.makedirs(self.backup_dir, exist_ok=True)
        
    def show_menu(self):
        self.window.clear_main_frame()
        
        customtkinter.CTkLabel(
            self.window.main_frame,
            text="ADB ROOT分区工具",
            font=("微软雅黑", 24, "bold")
        ).pack(pady=20)

        dump_frame = customtkinter.CTkFrame(self.window.main_frame)
        dump_frame.pack(fill="x", padx=30, pady=10)
        
        customtkinter.CTkLabel(
            dump_frame,
            text="分区提取",
            font=("微软雅黑", 16, "bold")
        ).pack(pady=10)

        partition_frame = customtkinter.CTkFrame(dump_frame)
        partition_frame.pack(fill="x", padx=20, pady=10)

        partition_var = customtkinter.StringVar()
        customtkinter.CTkEntry(
            partition_frame,
            textvariable=partition_var,
            placeholder_text="输入分区名称 (例如: boot_a, boot_b)",
            width=300
        ).pack(side="left", padx=10)
        
        operation_frame = customtkinter.CTkFrame(partition_frame)
        operation_frame.pack(side="right", padx=10)

        customtkinter.CTkButton(
            operation_frame,
            text="提取分区",
            command=lambda: self.dump_partition(partition_var.get().strip()),
            width=120
        ).pack(side="left", padx=5)

        customtkinter.CTkButton(
            operation_frame,
            text="刷入分区",
            command=lambda: self.flash_partition(partition_var.get().strip()),
            width=120
        ).pack(side="left", padx=5)

        info_frame = customtkinter.CTkFrame(self.window.main_frame)
        info_frame.pack(fill="x", padx=30, pady=20)
        
        customtkinter.CTkLabel(
            info_frame,
            text="使用说明",
            font=("微软雅黑", 16, "bold")
        ).pack(pady=10)
        
        notes = [
            "• 请手动输入需要操作的分区名称",
            "• AB分区设备请在分区名后添加 _a 或 _b",
            "• 常见分区: boot, recovery, init_boot 等",
            "• 提取的分区文件将保存在 downloads/partitions 目录"
        ]
        
        for note in notes:
            customtkinter.CTkLabel(
                info_frame,
                text=note,
                font=("微软雅黑", 12)
            ).pack(anchor="w", padx=20, pady=2)

        self.window.add_log("已打开分区工具")

    def _check_root(self):
        try:
            result = subprocess.run(
                ["platform-tools\\adb.exe", "shell", "id"],
                capture_output=True, text=True
            )
            return "uid=0" in result.stdout
        except Exception as e:
            self.window.add_log(f"检查ROOT权限异常: {str(e)}")
            return False

    def _get_partition_suffix(self, partition_name):
        """检测分区是否需要添加后缀"""
        try:
            if partition_name.endswith('_a') or partition_name.endswith('_b'):
                return partition_name

            result = subprocess.run(
                ["platform-tools\\adb.exe", "shell", "getprop", "ro.boot.slot_suffix"],
                capture_output=True, text=True
            )
            current_slot = result.stdout.strip()
            
            if current_slot in ['_a', '_b']:
                check_result = subprocess.run(
                    ["platform-tools\\adb.exe", "shell", "ls", "-l", f"/dev/block/by-name/{partition_name}_{current_slot[1]}"],
                    capture_output=True, text=True
                )
                if check_result.returncode == 0:
                    return f"{partition_name}{current_slot}"
                    
            return partition_name
            
        except Exception as e:
            self.window.add_log(f"分区检测异常: {str(e)}")
            return partition_name

    def dump_partition(self, partition):
        if not partition:
            messagebox.showerror("错误", "请输入分区名称")
            return
            
        partition = self._get_partition_suffix(partition)
        
        try:
            save_path = filedialog.asksaveasfilename(
                title=f"保存{partition}分区",
                initialdir=self.backup_dir,
                initialfile=f"{partition}.img",
                filetypes=[("镜像文件", "*.img")]
            )
            if not save_path:
                return

            self.window.add_log(f"开始提取{partition}分区...")
            
            result = subprocess.run(
                ["platform-tools\\adb.exe", "shell", "su", "-c", 
                 f"dd if=/dev/block/by-name/{partition} of=/data/local/tmp/{partition}.img"],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                raise Exception(result.stderr)
            
            pull_result = subprocess.run(
                ["platform-tools\\adb.exe", "pull", 
                 f"/data/local/tmp/{partition}.img", save_path],
                capture_output=True,
                text=True
            )
            
            if pull_result.returncode != 0:
                raise Exception(pull_result.stderr)
                
            subprocess.run(
                ["platform-tools\\adb.exe", "shell", "rm", 
                 f"/data/local/tmp/{partition}.img"]
            )
            
            self.window.add_log(f"{partition}分区提取成功")
            messagebox.showinfo("成功", f"{partition}分区已保存到:\n{save_path}")
            
        except Exception as e:
            error_msg = f"提取分区失败: {str(e)}"
            self.window.add_log(error_msg)
            messagebox.showerror("错误", error_msg)

    def flash_partition(self, partition):
        if not partition:
            messagebox.showerror("错误", "请输入分区名称") 
            return

        partition = self._get_partition_suffix(partition)
            
        try:
            image_path = filedialog.askopenfilename(
                title=f"选择要刷入{partition}分区的镜像文件",
                initialdir=self.backup_dir,
                filetypes=[("镜像文件", "*.img")]
            )
            if not image_path:
                return

            self.window.add_log(f"开始刷入{partition}分区...")
            
            result = subprocess.run(
                ["platform-tools\\adb.exe", "push", 
                 image_path, "/sdcard/flash.img"],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                raise Exception(result.stderr)

            result = subprocess.run(
                ["platform-tools\\adb.exe", "shell", "su", "-c",
                 "cp /sdcard/flash.img /data/local/tmp/flash.img"],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                raise Exception(result.stderr)

            result = subprocess.run(
                ["platform-tools\\adb.exe", "shell", "su", "-c",
                 f"dd if=/data/local/tmp/flash.img of=/dev/block/by-name/{partition}"],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                raise Exception(result.stderr)

            subprocess.run(
                ["platform-tools\\adb.exe", "shell", "rm",
                 "/data/local/tmp/flash.img"]
            )

            self.window.add_log(f"{partition}分区刷入成功")
            messagebox.showinfo("成功", f"{partition}分区刷入完成")

        except Exception as e:
            error_msg = f"刷入分区失败: {str(e)}"
            self.window.add_log(error_msg)
            messagebox.showerror("错误", error_msg)

def flash_partition_command(image_path, target_partition):
    """
    使用ADB工具刷写分区：
    1. 将镜像文件推送到/sdcard/flash.img
    2. 使用su命令将/sdcard/flash.img复制到/data/local/tmp/flash.img
    3. 使用dd命令刷写目标分区（target_partition）
    """
    import subprocess
    push_cmd = ["platform-tools\\adb.exe", "push", image_path, "/sdcard/flash.img"]
    push_result = subprocess.run(push_cmd, capture_output=True, text=True)
    if push_result.returncode != 0:
        print("推送到 /sdcard 失败:", push_result.stderr)
        return False

    copy_cmd = ["platform-tools\\adb.exe", "shell", "su", "-c", "cp /sdcard/flash.img /data/local/tmp/flash.img"]
    copy_result = subprocess.run(copy_cmd, capture_output=True, text=True)
    if copy_result.returncode != 0:
        print("复制到 /data/local/tmp 失败:", copy_result.stderr)
        return False

    dd_cmd = ["platform-tools\\adb.exe", "shell", "su", "-c", f"dd if=/data/local/tmp/flash.img of={target_partition}"]
    dd_result = subprocess.run(dd_cmd, capture_output=True, text=True)
    if dd_result.returncode == 0:
        print("刷写成功")
        return True
    else:
        print("刷写失败:", dd_result.stderr)
        return False


if __name__ == "__main__":
    image = input("请输入分区镜像文件路径: ").strip()
    target = input("请输入目标分区的设备节点: ").strip()
    flash_partition_command(image, target)
