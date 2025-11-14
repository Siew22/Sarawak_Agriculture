# train/train_model.py (为你定制的、6GB最终纯净版)
import os
from pathlib import Path
# --- 关键修复：在所有其他导入之前，为PyTorch指定一个安全的缓存目录 ---
# 这会告诉PyTorch/Torchvision将所有下载的模型权重都存放在项目内部，
# 从而彻底避免在用户主目录下的权限问题。
torch_cache_dir = Path(__file__).resolve().parent.parent.parent / "temp" / "torch_cache"
os.makedirs(torch_cache_dir, exist_ok=True)
os.environ['TORCH_HOME'] = str(torch_cache_dir)
import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import datasets, models, transforms
from torch.utils.data import DataLoader, Dataset, ConcatDataset, random_split
import json
from tqdm import tqdm
import time
from PIL import Image

# --- 6GB VRAM 自研配置 (使用你指定的路径) ---
# --- ↓↓↓ 你指定的、最终的数据源路径！↓↓↓ ---
DATA_DIRS = [
    '../../Mydataset/kaggle_black_pepper_dataset',
    '../../Mydataset/BLACK_PEPPER_DATASET',
]
# --- ↑↑↑ 路径配置结束 ↑↑↑ ---

MODEL_SAVE_PATH = '../../models_store/FINAL_PEPPER_MODEL_b0.pth'
LABELS_PATH = '../../models_store/final_pepper_labels.json'
BATCH_SIZE = 16 # 6GB VRAM 的安全批量大小
NUM_WORKERS = 2 # 6GB VRAM 的安全CPU工作线程数
NUM_EPOCHS = 80 # 保持足够的训练轮次
LEARNING_RATE = 0.001
MODEL_ARCHITECTURE = 'efficientnet_b2' # 明确使用轻量级模型


# --- CustomDatasetWrapper 保持不变，确保多进程安全 ---
class CustomDatasetWrapper(Dataset):
    def __init__(self, dataset, transform=None):
        self.dataset = dataset
        self.transform = transform
    def __len__(self): return len(self.dataset)
    def __getitem__(self, idx):
        try:
            image, label = self.dataset[idx]
            if self.transform: image = self.transform(image)
            return image, label
        except Exception as e:
            print(f"\n警告: 加载索引 {idx} 时出错: {e}. 将尝试加载下一个样本。")
            if len(self) == 0: return None, None
            return self.__getitem__((idx + 1) % len(self))

def train():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if device.type == 'cpu': 
        print("⚠️  警告: 未检测到CUDA, 训练会非常慢。")
    else: 
        print(f"✅ 检测到CUDA设备: {torch.cuda.get_device_name(0)}")

    # 1. 自动从你的两个文件夹中整合所有类别
    print("正在扫描指定的数据源并整合类别...")
    all_class_names = set()
    for data_dir in DATA_DIRS:
        if os.path.isdir(data_dir):
            for class_name in os.listdir(data_dir):
                if os.path.isdir(os.path.join(data_dir, class_name)):
                    all_class_names.add(class_name)
        else:
            print(f"⚠️  警告: 数据源路径 '{data_dir}' 不存在，已跳过。")
    
    sorted_class_names = sorted(list(all_class_names))
    if not sorted_class_names:
        print("❌ 错误：在指定的数据源中没有找到任何类别文件夹！")
        return
        
    NUM_CLASSES = len(sorted_class_names)
    idx_to_class = {str(i): name for i, name in enumerate(sorted_class_names)}
    
    os.makedirs(os.path.dirname(LABELS_PATH), exist_ok=True)
    with open(LABELS_PATH, 'w') as f: json.dump(idx_to_class, f, indent=4)
    print(f"✅ 标签文件已更新，共找到 {NUM_CLASSES} 个唯一的胡椒相关类别。")
    print("将要训练的类别:", sorted_class_names)

    # 2. 数据增强 (适配 B0 模型的 224x224 尺寸)
    data_transforms = {
        'train': transforms.Compose([
            transforms.RandomResizedCrop(size=224, scale=(0.8, 1.0)),
            transforms.RandomHorizontalFlip(p=0.5),
            transforms.ColorJitter(brightness=0.2, contrast=0.2),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ]),
        'val': transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ]),
    }

    # 3. 简单可靠的数据加载逻辑
    print("\n正在从你指定的文件夹加载并合并数据集...")
    all_datasets = []
    for data_dir in DATA_DIRS:
        if os.path.isdir(data_dir):
            try:
                dataset = datasets.ImageFolder(root=data_dir)
                all_datasets.append(dataset)
                print(f"  - ✅ 已加载数据源: '{data_dir}' (包含 {len(dataset)} 张图片)")
            except Exception as e:
                print(f"  - ❌ 加载 '{data_dir}' 时出错: {e}")

    if not all_datasets:
        print("❌ 错误: 没有加载到任何有效的训练数据！")
        return
        
    full_dataset = ConcatDataset(all_datasets)
    print(f"\n✅ 数据整合完成: 共 {len(full_dataset)} 张图片。")

    # 4. 自动划分与加载
    print("正在将总数据集划分为训练集和验证集 (80/20)...")
    train_size = int(0.8 * len(full_dataset))
    val_size = len(full_dataset) - train_size
    generator = torch.Generator().manual_seed(42)
    train_split, val_split = torch.utils.data.random_split(full_dataset, [train_size, val_size], generator=generator)
    
    train_dataset = CustomDatasetWrapper(train_split, data_transforms['train'])
    val_dataset = CustomDatasetWrapper(val_split, data_transforms['val'])
    
    dataloaders = {
        'train': DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True, num_workers=NUM_WORKERS, pin_memory=True),
        'val': DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False, num_workers=NUM_WORKERS, pin_memory=True),
    }
    print(f"✅ 数据加载器准备就绪: 训练集 {len(train_dataset)} 张, 验证集 {len(val_dataset)} 张。")

    # 5. 模型定义 (100% 自研, 使用 B0)
    print(f"正在构建一个全新的 '{MODEL_ARCHITECTURE}' 模型 (100% 完全自研)...")
    model = models.efficientnet_b2(weights='IMAGENET1K_V1') #num_classes=NUM_CLASSES)
    # 2. 替换掉最后一层（分类器），以匹配我们自己的类别数量
    #    这样可以保留所有预训练好的特征提取能力
    num_ftrs = model.classifier[1].in_features
    model.classifier[1] = nn.Linear(num_ftrs, NUM_CLASSES)

    model = model.to(device)

    # 6. 优化器与训练循环
    criterion = nn.CrossEntropyLoss(label_smoothing=0.1)
    optimizer = optim.AdamW(model.parameters(), lr=LEARNING_RATE, weight_decay=1e-2)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=NUM_EPOCHS)
    scaler = torch.cuda.amp.GradScaler(enabled=(device.type == 'cuda'))
    
    start_time = time.time()
    best_acc = 0.0

    print("\n--- 开始“胡椒专家”优化训练 (6GB版) ---")
    for epoch in range(NUM_EPOCHS):
        print(f'\nEpoch {epoch+1}/{NUM_EPOCHS} | 当前学习率: {optimizer.param_groups[0]["lr"]:.6f}')
        print('-' * 25)
        for phase in ['train', 'val']:
            model.train() if phase == 'train' else model.eval()
            running_loss, running_corrects = 0.0, 0
            
            progress_bar = tqdm(dataloaders[phase], desc=f"{phase.capitalize()} Epoch {epoch+1}")
            for inputs, labels in progress_bar:
                if inputs is None: continue
                inputs, labels = inputs.to(device, non_blocking=True), labels.to(device, non_blocking=True)
                optimizer.zero_grad(set_to_none=True)
                with torch.set_grad_enabled(phase == 'train'):
                    with torch.cuda.amp.autocast(enabled=(device.type == 'cuda')):
                        outputs = model(inputs)
                        _, preds = torch.max(outputs, 1)
                        loss = criterion(outputs, labels)
                    if phase == 'train':
                        scaler.scale(loss).backward()
                        scaler.step(optimizer)
                        scaler.update()
                running_loss += loss.item() * inputs.size(0)
                running_corrects += torch.sum(preds == labels.data)
                progress_bar.set_postfix(loss=f'{loss.item():.4f}')

            if len(dataloaders[phase].dataset) > 0:
                epoch_loss = running_loss / len(dataloaders[phase].dataset)
                epoch_acc = running_corrects.double() / len(dataloaders[phase].dataset)
                print(f'{phase} Loss: {epoch_loss:.4f} Acc: {epoch_acc:.4f}')

                if phase == 'val' and epoch_acc > best_acc:
                    best_acc = epoch_acc
                    torch.save(model.state_dict(), MODEL_SAVE_PATH)
                    print(f"🎉 新的最佳自研经济版模型已保存 (Accuracy: {best_acc:.4f}) 🎉")
        
        scheduler.step()

    time_elapsed = time.time() - start_time
    print(f'\n--- 训练完成 ---')
    print(f'总耗时: {time_elapsed // 60:.0f}分 {time_elapsed % 60:.0f}秒')
    print(f'🏆 最佳验证集准确率: {best_acc:4f}')

if __name__ == "__main__":
    train()