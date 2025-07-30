import subprocess

class DeviceDetector:
    @staticmethod
    def check_fastboot():
        try:
            result = subprocess.run(
                ["platform-tools\\fastboot", "devices"],
                capture_output=True, text=True
            )
            return bool(result.stdout.strip())
        except:
            return False
    
    @staticmethod
    def check_adb():
        try:
            result = subprocess.run(
                ["platform-tools\\adb.exe", "devices"],
                capture_output=True, text=True
            )
            return len(result.stdout.strip().splitlines()) > 1
        except:
            return False
            
    @staticmethod
    def get_device_info():
        info = {}
        try:
            if DeviceDetector.check_adb():
                root_result = subprocess.run(
                    ["platform-tools\\adb.exe", "shell", "su", "-c", "id"],
                    capture_output=True, text=True,
                    timeout=1
                )
                info["root"] = "已获取Root" if "uid=0" in root_result.stdout else "未Root"

                if "uid=0" in root_result.stdout:
                    slot_result = subprocess.run(
                        ["platform-tools\\adb.exe", "shell", "getprop", "ro.boot.slot_suffix"],
                        capture_output=True, text=True
                    )
                    slot = slot_result.stdout.strip()
                    if slot in ["_a", "_b"]:
                        info["root"] = f"已获取Root ({slot.upper()[1:]}槽)"
                    
                props = subprocess.run(
                    ["platform-tools\\adb.exe", "shell", "getprop"],
                    capture_output=True, text=True
                ).stdout
                
                for line in props.splitlines():
                    if "[ro.product.model]" in line:
                        info["model"] = line.split("[")[2].strip("[]")
                    elif "[ro.build.version.release]" in line:
                        info["android"] = line.split("[")[2].strip("[]")
                    elif "[ro.build.version.sdk]" in line:
                        info["api"] = line.split("[")[2].strip("[]")
                        
            elif DeviceDetector.check_fastboot():
                fb_info = subprocess.run(
                    ["platform-tools\\fastboot", "getvar", "all"],
                    capture_output=True, text=True
                ).stdout
                
                info["mode"] = "Fastboot"
                if "product:" in fb_info:
                    info["model"] = fb_info.split("product:")[1].splitlines()[0].strip()
                    
        except Exception as e:
            info["error"] = str(e)
            
        return info
    
    @staticmethod
    def get_detailed_info():
        info = {
            "基本信息": {},
            "系统信息": {},
            "硬件信息": {},
            "安全信息": {}
        }
        
        try:
            if DeviceDetector.check_adb():
                try:
                    root_result = subprocess.run(
                        ["platform-tools\\adb.exe", "shell", "su", "-c", "id"],
                        capture_output=True, text=True,
                        timeout=1
                    )
                    root_status = "已获取Root权限" if "uid=0" in root_result.stdout else "未获取Root权限"
                    
                    if "uid=0" in root_result.stdout:
                        slot_result = subprocess.run(
                            ["platform-tools\\adb.exe", "shell", "getprop", "ro.boot.slot_suffix"],
                            capture_output=True, text=True
                        )
                        slot = slot_result.stdout.strip()
                        if slot in ["_a", "_b"]:
                            root_status = f"已获取Root权限 (当前{slot.upper()[1:]}槽)"
                    
                    info["安全信息"]["ROOT状态"] = root_status
                except:
                    info["安全信息"]["ROOT状态"] = "检测失败"
                
                props = subprocess.run(
                    ["platform-tools\\adb.exe", "shell", "getprop"],
                    capture_output=True, text=True,
                        encoding='gbk',
                    errors='ignore'
                ).stdout or ""
                
                for line in props.splitlines():
                    if "[ro.product.model]" in line:
                        info["基本信息"]["设备型号"] = line.split("[")[2].strip("[]")
                    elif "[ro.product.brand]" in line:
                        info["基本信息"]["品牌"] = line.split("[")[2].strip("[]")
                    elif "[ro.build.version.release]" in line:
                        info["系统信息"]["Android版本"] = line.split("[")[2].strip("[]")
                    elif "[ro.build.version.sdk]" in line:
                        info["系统信息"]["API级别"] = line.split("[")[2].strip("[]")
                    elif "[ro.build.version.security_patch]" in line:
                        info["安全信息"]["安全补丁级别"] = line.split("[")[2].strip("[]")
                    elif "[ro.crypto.state]" in line:
                        info["安全信息"]["加密状态"] = line.split("[")[2].strip("[]")
                
                cpu_info = subprocess.run(
                    ["platform-tools\\adb.exe", "shell", "cat", "/proc/cpuinfo"],
                    capture_output=True, text=True,
                    encoding='gbk',
                    errors='ignore'
                ).stdout or ""
                
                if cpu_info:
                    for line in cpu_info.splitlines():
                        if "Hardware" in line:
                            info["硬件信息"]["CPU型号"] = line.split(":")[-1].strip()
                            break
                
                mem_info = subprocess.run(
                    ["platform-tools\\adb.exe", "shell", "cat", "/proc/meminfo"],
                    capture_output=True, text=True,
                    encoding='gbk',
                    errors='ignore'
                ).stdout or ""
                
                if mem_info:
                    for line in mem_info.splitlines():
                        if "MemTotal" in line:
                            try:
                                mem_kb = int(line.split()[1])
                                info["硬件信息"]["总内存"] = f"{mem_kb // 1024} MB"
                            except (ValueError, IndexError):
                                info["硬件信息"]["总内存"] = "未知"
                            break
                
                battery = subprocess.run(
                    ["platform-tools\\adb.exe", "shell", "dumpsys", "battery"],
                    capture_output=True, text=True,
                    encoding='gbk',
                    errors='ignore'
                ).stdout or ""
                
                if battery:
                    for line in battery.splitlines():
                        if "level:" in line:
                            info["硬件信息"]["电池电量"] = f"{line.split(':')[1].strip()}%"
                        elif "status:" in line:
                            status = line.split(':')[1].strip()
                            info["硬件信息"]["充电状态"] = "充电中" if status == "2" else "未充电"

            elif DeviceDetector.check_fastboot():
                info["基本信息"]["模式"] = "Fastboot"
                fb_info = subprocess.run(
                    ["platform-tools\\fastboot", "getvar", "all"],
                    capture_output=True, text=True,
                    encoding='gbk',
                    errors='ignore'
                ).stdout or ""
                
                if "unlocked:" in fb_info.lower():
                    unlock_status = "已解锁" if "true" in fb_info.lower() else "未解锁"
                    info["安全信息"]["Bootloader状态"] = unlock_status
                
            else:
                info["基本信息"]["状态"] = "未连接设备"
                
        except Exception as e:
            info["错误信息"] = {"错误详情": str(e)}
            
        return info
