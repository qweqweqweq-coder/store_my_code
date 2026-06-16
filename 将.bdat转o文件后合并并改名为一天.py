import subprocess
import os
import datetime
from pathlib import Path

def process_gnss_pipeline(src_root, dst_root, convbin_path, gfzrnx_path, station_id="9755"):
    """
    一键完成：扫描日期文件夹 -> 转换所有.bdat为.obs -> 用gfzrnx合并为标准一日.rnx文件 -> 清理临时文件
    """
    src_root_path = Path(src_root)
    dst_root_path = Path(dst_root)
    
    # 创建最终的输出大文件夹
    dst_root_path.mkdir(parents=True, exist_ok=True)
    
    # 1. 遍历 9577 文件夹下的所有子文件夹
    subfolders = [f for f in src_root_path.iterdir() if f.is_dir()]
    print(f"共发现 {len(subfolders)} 个日期文件夹准备处理。\n")

    for folder in subfolders:
        folder_name = folder.name  # 例如 "20250502"
        
        # 2. 检查文件夹名是否为8位数字日期
        if not (len(folder_name) == 8 and folder_name.isdigit()):
            print(f"跳过非日期文件夹: {folder_name}")
            continue
            
        print(f"==================================================")
        print(f"正在处理日期文件夹: {folder_name}")
        print(f"==================================================")
        
        # 3. 解析日期并计算年积日 (DOY)
        try:
            date_obj = datetime.datetime.strptime(folder_name, "%Y%m%d")
            year = date_obj.strftime("%Y")
            doy = date_obj.strftime("%j")  # 获取3位数的年积日，例如 122
            formatted_date = date_obj.strftime("%Y/%m/%d") # convbin 要求的格式
        except Exception as e:
            print(f"日期解析失败 {folder_name}: {e}")
            continue

        # 4. 寻找该文件夹下的所有 .bdat 文件
        bdat_files = list(folder.glob("*.bdat"))
        if not bdat_files:
            print(f"文件夹 {folder_name} 内没有找到 .bdat 文件，跳过。")
            continue
            
        print(f"-> 步骤1: 发现 {len(bdat_files)} 个 .bdat 文件，开始转换为临时 .obs...")
        
        # 5. 循环调用 convbin，将所有 .bdat 转换为临时的 .obs
        temp_obs_files = []
        for bdat_file in bdat_files:
            stem = bdat_file.stem
            # 临时 obs 文件直接生成在原文件夹中
            obs_out = folder / f"{stem}.obs"
            temp_obs_files.append(obs_out)
            
            # 构造 convbin 命令
            conv_cmd = [
                str(convbin_path),
                str(bdat_file),
                "-o", str(obs_out),
                "-tr", formatted_date, "00:00:00",
                "-v", "3.04",
                "-r", "rtcm3",
                "-f", "6",
                "-od", "-os", "-oi", "-ol"
            ]
            # 执行转换 (静默模式)
            subprocess.run(conv_cmd, capture_output=True, text=True, encoding='utf-8')

        print(f"-> 步骤2: 临时转换完成。开始调用 gfzrnx 合并为一天的数据...")

        # 6. 构建你要求的 RINEX 3 标准长文件名
        # 示例: 975500CHN_R_20251220000_01D_05S_MO.rnx
        output_filename = f"{station_id}00CHN_R_{year}{doy}0000_01D_05S_MO.rnx"
        final_output_path = dst_root_path / output_filename

        # 7. 调用 gfzrnx 进行合并
        # 因为 gfzrnx 支持通配符，我们把当前文件夹作为它的工作目录(cwd)
        gfz_cmd = [
            str(gfzrnx_path),
            "-finp", "*.obs",
            "-fout", str(final_output_path),
            "-vo", "3"
        ]
        
        try:
            # shell=True 在 Windows 下支持 *.obs 通配符
            result = subprocess.run(gfz_cmd, cwd=str(folder), capture_output=True, text=True, shell=True)
            
            if final_output_path.exists():
                print(f"【成功】成功生成全天大文件: {output_filename}")
            else:
                print(f"【失败】gfzrnx 未能生成文件。错误信息: {result.stderr}")
        except Exception as e:
            print(f"【错误】合并时发生异常: {e}")

        # 8. 步骤3: 清理原文件夹里的临时 .obs 和其他导航文件，保持电脑干净
        print(f"-> 步骤3: 正在清理临时生成的 obs/nav 文件...")
        for extra_file in folder.iterdir():
            if extra_file.suffix.lower() in ['.obs', '.nav'] or 'glonass' in extra_file.name or 'galileo' in extra_file.name or 'bds' in extra_file.name:
                try:
                    extra_file.unlink()
                except:
                    pass
        print(f"日期 {folder_name} 处理完毕。\n")

    print(f"所有任务已全部完成！最终的一天一个的 .rnx 文件已保存在: {dst_root}")

# --- ⚙️ 路径配置区 ⚙️ ---
if __name__ == "__main__":
    # 1. 你的 convbin.exe 路径
    CONVBIN_EXE = r"G:\chaobaihe\RTKLIB_bin-rtklib_2.4.3\RTKLIB_bin-rtklib_2.4.3\bin\convbin.exe"
    
    # 2. 你的 gfzrnx.exe 路径 (请确保下载了 Windows 版的 gfzrnx)
    GFZRNX_EXE = r"G:\chaobaihe\RTKLIB_bin-rtklib_2.4.3\RTKLIB_bin-rtklib_2.4.3\bin\gfzrnx.exe"
    
    # 3. 你的原始数据根目录 (即包含 20250502 等文件夹的 9577 文件夹)
    DATA_SRC_ROOT = r"D:\gnss_work\refl_code\2026\rinex\9753"
    
    # 4. 你希望把最终合并好的 .rnx 成果文件放在哪个新文件夹里
    DATA_DST_ROOT = r"D:\gnss_work\refl_code\2026\rinex\9753"
    
    # 5. 你的测站名（文件名开头那四位，代码里会自动补全成 975500CHN）
    STATION_NAME = "9753"

    # 启动全自动流水线
    process_gnss_pipeline(DATA_SRC_ROOT, DATA_DST_ROOT, CONVBIN_EXE, GFZRNX_EXE, STATION_NAME)