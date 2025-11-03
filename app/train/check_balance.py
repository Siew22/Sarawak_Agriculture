# app/train/check_balance.py
import os
from collections import defaultdict
import json
import pandas as pd

# --- 从你的训练脚本中复制这两个关键列表 ---
DATA_DIRS = [
    '../../PlantVillage-Dataset/raw/color', 
    '../../Mydataset/kaggle_black_pepper_dataset',
    '../../Mydataset/Pepper Diseases and Pests Detection/Pepper Diseases and Pests Detection/PepperDiseaseTest/PepperDiseaseTest',
    #'../../PlantVillage-Dataset/raw/grayscale',
    #'../../PlantVillage-Dataset/raw/segmented',
    #'../../training_workspace/confirmed_data', # 确保包含了你的新数据源
]

LABELS_PATH = '../../models_store/pepper_only_labels.json'
# --- 配置结束 ---

def check_data_balance():
    print("--- 开始进行数据集平衡性检查 ---")
    
    # 1. 扫描并获取所有“胡椒专属”类别
    pepper_class_names = set()
    for data_dir in DATA_DIRS:
        if os.path.isdir(data_dir):
            for class_name in os.listdir(data_dir):
                if os.path.isdir(os.path.join(data_dir, class_name)) and 'pepper' in class_name.lower():
                    pepper_class_names.add(class_name)
    
    sorted_class_names = sorted(list(pepper_class_names))
    if not sorted_class_names:
        print("❌ 错误：在所有数据源中，没有找到任何包含'pepper'字眼的类别文件夹！")
        return

    print(f"✅ 共找到 {len(sorted_class_names)} 个与'Pepper'相关的唯一类别。")
    
    # 2. 统计每个类别的图片数量
    class_counts = defaultdict(int)
    for data_dir in DATA_DIRS:
        if not os.path.isdir(data_dir):
            print(f"⚠️ 警告: 找不到数据路径 '{data_dir}'，已跳过。")
            continue
        
        print(f"  - 正在扫描: {data_dir}")
        for class_name in os.listdir(data_dir):
            if class_name in pepper_class_names:
                class_path = os.path.join(data_dir, class_name)
                if os.path.isdir(class_path):
                    count = len([f for f in os.listdir(class_path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))])
                    class_counts[class_name] += count
    
    if not class_counts:
        print("❌ 错误: 在所有数据源中，没有找到任何有效的'Pepper'图片！")
        return
        
    # 3. 使用Pandas进行可视化和分析
    df = pd.DataFrame(list(class_counts.items()), columns=['ClassName', 'ImageCount'])
    df = df.sort_values(by='ImageCount', ascending=False).reset_index(drop=True)
    
    total_images = df['ImageCount'].sum()
    df['Percentage'] = (df['ImageCount'] / total_images * 100).round(2).astype(str) + '%'
    
    print("\n--- 数据集平衡性分析报告 ---")
    print(df.to_string())
    print("---------------------------------")
    print(f"总图片数: {total_images}")
    
    # 4. 生成标签文件 (可选，与训练脚本同步)
    os.makedirs(os.path.dirname(LABELS_PATH), exist_ok=True)
    idx_to_class = {str(i): name for i, name in enumerate(df['ClassName'].tolist())}
    with open(LABELS_PATH, 'w') as f:
        json.dump(idx_to_class, f, indent=4)
    print(f"\n✅ 标签文件已根据数量排序更新于: {LABELS_PATH}")

if __name__ == "__main__":
    check_data_balance()