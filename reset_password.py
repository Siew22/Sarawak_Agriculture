# 文件路径: reset_password.py

import sys
# 我们需要能够访问 app 目录下的模块，所以先把它加到系统路径中
sys.path.append('./app')

from auth.security import get_password_hash

def main():
    # 检查命令行参数是否正确
    if len(sys.argv) != 3:
        print("\nUsage: python reset_password.py <user_email> <new_password>")
        print("Example: python reset_password.py bcs24020043@gmail.com mynewpassword123\n")
        return

    user_email = sys.argv[1]
    new_password = sys.argv[2]
    
    # 使用我们后端代码中完全相同的哈希函数
    hashed_password = get_password_hash(new_password)
    
    print("\n" + "="*40)
    print("--- Password Reset Script ---")
    print("="*40)
    print(f"Target Email:    {user_email}")
    print(f"New Password:    {new_password}")
    print(f"Generated Hash:  {hashed_password}")
    print("\n--- SQL Command to run in your database ---")
    # 生成可以直接复制粘贴的 SQL 更新语句
    print(f"UPDATE users SET hashed_password = '{hashed_password}' WHERE email = '{user_email}';")
    print("="*40 + "\n")

if __name__ == "__main__":
    main()