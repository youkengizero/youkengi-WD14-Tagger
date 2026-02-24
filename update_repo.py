"""
GitHub 仓库更新工具
GitHub Repository Updater

使用方法 / Usage:
    python update_repo.py

功能 / Features:
    - 自动检测文件变更
    - 交互式提交信息输入
    - 一键推送到 GitHub
"""

import subprocess
import sys
import os


def run_command(cmd, check=False):
    """运行命令"""
    print(f">>> {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    return result.returncode == 0, result.stdout, result.stderr


def check_git_status():
    """检查 Git 状态"""
    success, stdout, _ = run_command("git status --short")
    if not success:
        return None
    
    # 定义需要忽略的文件和文件夹
    IGNORED_ITEMS = [
        'github_uploader.py',
        'update_repo.py',
        '参考文件',
        'nicegui_components',
        '主程序备份',
    ]
    
    # 解析变更文件
    changes = []
    for line in stdout.strip().split('\n'):
        if line:
            status = line[:2].strip()
            filename = line[3:].strip()
            
            # 检查是否需要忽略
            should_ignore = False
            for ignored in IGNORED_ITEMS:
                if filename == ignored or filename.startswith(ignored + '/'):
                    should_ignore = True
                    break
            
            if not should_ignore:
                changes.append({'status': status, 'file': filename})
    
    return changes


def get_status_emoji(status):
    """获取状态对应的 emoji"""
    status_map = {
        'M': '📝',  # 修改
        'A': '✨',  # 新增
        'D': '🗑️',  # 删除
        '??': '🆕', # 未跟踪
        'R': '🔀',  # 重命名
    }
    return status_map.get(status, '📄')


def get_status_text(status):
    """获取状态文字说明"""
    status_map = {
        'M': '修改',
        'A': '新增',
        'D': '删除',
        '??': '未跟踪',
        'R': '重命名',
    }
    return status_map.get(status, status)


def main():
    """主函数"""
    print("=" * 60)
    print("🚀 GitHub 仓库更新工具")
    print("=" * 60)
    
    # 检查是否在 git 仓库中
    if not os.path.exists('.git'):
        print("\n❌ 当前目录不是 Git 仓库！")
        print("   请先运行: git init")
        return 1
    
    # 检查远程仓库
    success, stdout, _ = run_command("git remote -v")
    if not success or 'origin' not in stdout:
        print("\n❌ 未配置远程仓库！")
        remote_url = input("请输入远程仓库地址 (如: https://github.com/youkengizero/repo.git): ").strip()
        if remote_url:
            run_command(f"git remote add origin {remote_url}")
        else:
            return 1
    
    # 检查文件状态
    print("\n📋 检查文件变更...")
    changes = check_git_status()
    
    if changes is None:
        print("❌ 无法获取 Git 状态")
        return 1
    
    if not changes:
        print("✅ 没有需要提交的变更")
        
        # 询问是否强制推送
        choice = input("\n是否强制推送到远程? (y/N): ").strip().lower()
        if choice == 'y':
            print("\n🚀 推送到 GitHub...")
            run_command("git push")
        return 0
    
    # 显示变更文件
    print(f"\n发现 {len(changes)} 个文件变更:\n")
    print("-" * 60)
    for i, change in enumerate(changes, 1):
        emoji = get_status_emoji(change['status'])
        status_text = get_status_text(change['status'])
        print(f"{i:2}. {emoji} [{status_text:4}] {change['file']}")
    print("-" * 60)
    
    # 确认添加
    print("\n选项:")
    print("  1. 添加所有变更 (git add .)")
    print("  2. 选择特定文件添加")
    print("  3. 取消")
    
    choice = input("\n请选择 (1-3, 默认: 1): ").strip() or '1'
    
    if choice == '3':
        print("❌ 已取消")
        return 0
    
    if choice == '2':
        # 选择特定文件
        selected = input("请输入要添加的文件编号 (多个用逗号分隔, 如: 1,3,5): ").strip()
        try:
            indices = [int(x.strip()) - 1 for x in selected.split(',')]
            files_to_add = [changes[i]['file'] for i in indices if 0 <= i < len(changes)]
            
            for file in files_to_add:
                run_command(f'git add "{file}"')
        except (ValueError, IndexError):
            print("❌ 输入无效")
            return 1
    else:
        # 添加所有
        print("\n📥 添加所有变更...")
        run_command("git add .")
    
    # 输入提交信息
    print("\n💾 提交更改...")
    default_msg = "更新项目"
    
    # 提供常用提交信息模板
    print("\n常用提交信息:")
    print("  1. 更新项目")
    print("  2. 修复问题")
    print("  3. 添加功能")
    print("  4. 更新文档")
    print("  5. 自定义")
    
    msg_choice = input("\n请选择 (1-5, 默认: 1): ").strip() or '1'
    
    msg_templates = {
        '1': '更新项目',
        '2': '修复问题',
        '3': '添加功能',
        '4': '更新文档',
    }
    
    if msg_choice in msg_templates:
        commit_msg = msg_templates[msg_choice]
    else:
        commit_msg = input("请输入提交信息: ").strip()
    
    if not commit_msg:
        commit_msg = default_msg
    
    # 提交
    success, _, _ = run_command(f'git commit -m "{commit_msg}"')
    if not success:
        print("⚠️ 提交失败或没有变更需要提交")
        return 1
    
    print(f"✅ 已提交: {commit_msg}")
    
    # 推送
    print("\n🚀 推送到 GitHub...")
    success, _, stderr = run_command("git push")
    
    if success:
        print("\n" + "=" * 60)
        print("✅ 更新成功！")
        print("=" * 60)
        
        # 获取仓库地址
        _, remote_out, _ = run_command("git remote get-url origin")
        if remote_out:
            repo_url = remote_out.strip().replace('.git', '')
            print(f"\n🌐 仓库地址: {repo_url}")
    else:
        print("\n❌ 推送失败")
        if 'rejected' in stderr:
            print("\n提示: 远程仓库有更新，尝试先拉取:")
            print("  git pull origin main")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
