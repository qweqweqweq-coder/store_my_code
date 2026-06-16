import os
import shutil
import re

def natural_sort_key(s):
    """用于实现数字自然排序 (1, 2, 10 而不是 1, 10, 2)"""
    return [int(text) if text.isdigit() else text.lower() for text in re.split('([0-9]+)', s)]

def move_files_to_previous_folder(parent_dir, limit=96):
    # 1. 获取所有子文件夹并进行自然排序
    subfolders = [f.name for f in os.scandir(parent_dir) if f.is_dir()]
    subfolders.sort(key=natural_sort_key)

    if len(subfolders) < 2:
        print("文件夹数量不足，无法执行‘移至上一个’的操作。")
        return

    print(f"检测到序列: {' -> '.join(subfolders)}")
    print("-" * 30)

    # 2. 从第二个文件夹开始遍历 (索引从 1 开始)
    for i in range(1, len(subfolders)):
        current_folder_name = subfolders[i]
        prev_folder_name = subfolders[i-1]
        
        current_folder_path = os.path.join(parent_dir, current_folder_name)
        prev_folder_path = os.path.join(parent_dir, prev_folder_name)

        # 获取当前文件夹中的文件
        files = [f for f in os.scandir(current_folder_path) if f.is_file()]
        files.sort(key=lambda x: x.name) # 文件也按名称排个序

        # 取前 96 个
        files_to_move = files[:limit]
        
        if not files_to_move:
            print(f"跳过 [{current_folder_name}]: 文件夹内无文件。")
            continue

        print(f"正在移动: [{current_folder_name}] -> [{prev_folder_name}] (共 {len(files_to_move)} 个)")

        for file in files_to_move:
            src_path = file.path
            dest_path = os.path.join(prev_folder_path, file.name)

            # 冲突检查：如果上一个文件夹里已有同名文件，重命名
            count = 1
            name, ext = os.path.splitext(file.name)
            while os.path.exists(dest_path):
                dest_path = os.path.join(prev_folder_path, f"{name}_{count}{ext}")
                count += 1

            shutil.move(src_path, dest_path)

    print("-" * 30)
    print("操作完成！")

if __name__ == "__main__":
    # 你的大文件夹路径
    target_path = r'D:\gnss_work\refl_code\2026\rinex\97531'
    move_files_to_previous_folder(target_path)