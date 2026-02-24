"""
通用 GitHub 项目上传工具
Universal GitHub Project Uploader

使用方法 / Usage:
    python github_uploader.py

功能 / Features:
    - 交互式配置项目信息
    - 自动初始化 Git 仓库
    - 支持创建新仓库或推送到现有仓库
    - 自动生成 README 和 .gitignore
"""

import subprocess
import os
import sys
from pathlib import Path


def clean_input(text):
    """清理用户输入，去除反引号和多余空格"""
    if not text:
        return text
    # 去除反引号
    text = text.replace('`', '')
    # 去除多余空格
    text = ' '.join(text.split())
    return text.strip()


def run_command(cmd, check=True):
    """运行命令"""
    print(f">>> {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr and check:
        print(result.stderr, file=sys.stderr)
    return result.returncode == 0


def check_git():
    """检查 Git 是否安装"""
    result = subprocess.run("git --version", shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print("❌ Git 未安装！请访问 https://git-scm.com/download/win 下载安装")
        return False
    print(f"✅ Git 已安装: {result.stdout.strip()}")
    return True


def get_user_input():
    """获取用户输入"""
    print("\n" + "=" * 60)
    print("🚀 GitHub 项目上传工具")
    print("=" * 60)
    print("\n⚠️  重要提示 / Important:")
    print("   本脚本只负责推送代码，不会自动创建 GitHub 仓库！")
    print("   This script only pushes code, does NOT create GitHub repository!")
    print("\n   请确保已在 GitHub 网页创建同名仓库：")
    print("   Please create the repository on GitHub first:")
    print("   👉 https://github.com/new")
    
    # 获取 GitHub 用户名
    github_username = clean_input(input("\n📋 GitHub 用户名 (默认: youkengizero): "))
    if not github_username:
        github_username = "youkengizero"
    
    # 获取仓库名称
    print("\n📦 仓库名称 / Repository name:")
    print("   请输入 GitHub 上已创建的仓库名称")
    print("   Enter the repository name you created on GitHub")
    repo_name = clean_input(input("   如: my-project: "))
    while not repo_name:
        print("❌ 仓库名称不能为空！")
        repo_name = clean_input(input("📦 仓库名称: "))
    
    # 获取项目描述
    description = clean_input(input("📝 项目描述: "))
    if not description:
        description = f"{repo_name} - A GitHub project"
    
    # 选择是否私有（默认公开）
    is_private_input = clean_input(input("🔒 是否私有仓库? (y/N, 默认: n): ")).lower()
    is_private = is_private_input == 'y'
    
    # 选择编程语言（默认 Python）
    print("\n🌐 选择项目类型:")
    print("  1. Python (默认)")
    print("  2. JavaScript/Node.js")
    print("  3. Java")
    print("  4. C/C++")
    print("  5. 其他/通用")
    
    lang_choice = clean_input(input("选择 (1-5, 直接回车默认: 1): "))
    lang_map = {
        '1': 'Python',
        '2': 'Node',
        '3': 'Java',
        '4': 'C++',
        '5': ''
    }
    gitignore_template = lang_map.get(lang_choice, 'Python')
    
    # 是否生成 README（默认不生成）
    gen_readme_input = clean_input(input("\n📄 生成 README.md? (Y/n, 默认: n): ")).lower()
    gen_readme = gen_readme_input == 'y'
    
    return {
        'username': github_username,
        'repo_name': repo_name,
        'description': description,
        'is_private': is_private,
        'gitignore_template': gitignore_template,
        'gen_readme': gen_readme
    }


def create_readme(repo_name, description):
    """创建 README.md"""
    readme_content = f"""# {repo_name}

{description}

## 简介 / Introduction

这是一个 GitHub 开源项目。

This is a GitHub open source project.

## 安装 / Installation

```bash
# 克隆仓库 / Clone the repository
git clone https://github.com/youkengizero/{repo_name}.git

# 进入项目目录 / Enter project directory
cd {repo_name}
```

## 使用 / Usage

请查看项目文档了解如何使用。

Please refer to the project documentation for usage instructions.

## 贡献 / Contributing

欢迎提交 Issue 和 Pull Request！

Issues and Pull Requests are welcome!

## 许可证 / License

MIT License
"""
    
    with open('README.md', 'w', encoding='utf-8') as f:
        f.write(readme_content)
    print("✅ 已生成 README.md")


def create_gitignore(template):
    """创建 .gitignore"""
    # 基础忽略规则（所有项目通用）
    base_ignore = """# Upload scripts
github_uploader.py
update_repo.py

# Reference folders
参考文件/
nicegui_components/
主程序备份/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
"""
    
    gitignore_content = base_ignore
    
    if template == 'Python':
        gitignore_content += """
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
env/
ENV/
"""
    elif template == 'Node':
        gitignore_content += """
# Node.js
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
package-lock.json
yarn.lock

# Build
dist/
build/
"""
    
    with open('.gitignore', 'w', encoding='utf-8') as f:
        f.write(gitignore_content)
    print(f"✅ 已生成 .gitignore ({template if template else '基础规则'})")


def check_and_fix_repo(config):
    """检查并修复仓库状态"""
    if not os.path.exists('.git'):
        return True  # 没有仓库，正常初始化
    
    print("\n🔍 检查 Git 仓库状态...")
    
    # 检查是否有提交
    result = subprocess.run("git log --oneline -1", shell=True, capture_output=True, text=True)
    has_commit = result.returncode == 0 and result.stdout.strip()
    
    # 检查远程仓库配置
    result = subprocess.run("git remote -v", shell=True, capture_output=True, text=True)
    has_remote = result.returncode == 0 and 'origin' in result.stdout
    
    # 检查是否有未推送的提交
    if has_remote and has_commit:
        result = subprocess.run("git log origin/main..main --oneline", shell=True, capture_output=True, text=True)
        unpushed = result.stdout.strip()
        if unpushed:
            print(f"   发现 {len(unpunushed.split(chr(10)))} 个未推送的提交")
            return 'push_only'  # 只需要推送
    
    if not has_commit:
        print("   ⚠️  仓库已初始化但没有提交记录")
        print("   可能原因：之前选择了'重新初始化'但推送失败")
        choice = clean_input(input("\n是否修复并重新推送? (Y/n): ")).lower()
        if choice != 'n':
            print("   🗑️  删除旧的 Git 仓库...")
            # 尝试删除 .git 目录，处理权限错误
            try:
                import shutil
                shutil.rmtree('.git')
                print("   ✅ 已删除旧仓库，将重新初始化")
                return True  # 重新初始化
            except PermissionError:
                print("   ⚠️  权限错误，无法删除 .git 目录")
                print("   正在使用 Git 命令重置仓库...")
                # 使用 Git 命令重置仓库状态
                run_command("git reset --hard HEAD")
                run_command("git clean -fdx")
                run_command("git add .")
                return True  # 继续使用现有仓库
            except Exception as e:
                print(f"   ⚠️  删除失败: {e}")
                print("   继续使用现有仓库...")
                return True
        return False
    
    return True  # 仓库正常


def init_and_push(config):
    """初始化并推送"""
    print("\n" + "=" * 60)
    print("📦 开始上传项目...")
    print("=" * 60)
    
    # 检查并修复仓库状态
    fix_result = check_and_fix_repo(config)
    if not fix_result:
        print("❌ 已取消")
        return False
    
    # 如果只需要推送
    if fix_result == 'push_only':
        print("\n🚀 直接推送到 GitHub...")
        remote_url = f"https://github.com/{config['username']}/{config['repo_name']}.git"
        if run_command("git push -u origin main"):
            print("\n" + "=" * 60)
            print("✅ 推送成功！")
            print("=" * 60)
            print(f"\n🌐 仓库地址: {remote_url}")
            return True
        else:
            print("\n❌ 推送失败")
            return False
    
    # 检查是否有现有 git 仓库（用户手动选择）
    if os.path.exists('.git'):
        print("\n⚠️ 检测到已存在的 Git 仓库")
        print("   提示：如果之前推送失败，建议重新初始化")
        choice = clean_input(input("   是否重新初始化? (y/N): ")).lower()
        if choice == 'y':
            print("   🗑️  删除旧的 Git 仓库...")
            # 尝试删除 .git 目录，处理权限错误
            try:
                import shutil
                shutil.rmtree('.git')
                print("   ✅ 已删除旧仓库")
            except PermissionError:
                print("   ⚠️  权限错误，无法删除 .git 目录")
                print("   正在使用 Git 命令重置仓库...")
                # 使用 Git 命令重置仓库状态
                run_command("git reset --hard HEAD")
                run_command("git clean -fdx")
                run_command("git add .")
            except Exception as e:
                print(f"   ⚠️  删除失败: {e}")
                print("   继续使用现有仓库...")
    
    # 生成文件
    if config['gen_readme'] and not os.path.exists('README.md'):
        create_readme(config['repo_name'], config['description'])
    
    if config['gitignore_template'] and not os.path.exists('.gitignore'):
        create_gitignore(config['gitignore_template'])
    
    # 初始化 Git
    print("\n🌿 初始化 Git 仓库...")
    if not run_command("git init"):
        return False
    
    # 配置用户信息（如果未配置）
    run_command('git config user.name "youkengizero"', check=False)
    run_command('git config user.email "646937580@qq.com"', check=False)
    
    # 添加文件
    print("\n📥 添加文件...")
    run_command("git add .")
    
    # 提交
    print("\n💾 提交更改...")
    commit_msg = clean_input(input("提交信息 (默认: Initial commit): "))
    if not commit_msg:
        commit_msg = "Initial commit"
    
    if not run_command(f'git commit -m "{commit_msg}"'):
        print("⚠️ 没有需要提交的更改或提交失败")
    
    # 设置分支
    run_command("git branch -M main", check=False)
    
    # 添加远程仓库
    print("\n🔗 添加远程仓库...")
    remote_url = f"https://github.com/{config['username']}/{config['repo_name']}.git"
    
    # 检查是否已有远程仓库
    result = subprocess.run("git remote -v", shell=True, capture_output=True, text=True)
    if "origin" in result.stdout:
        run_command("git remote remove origin", check=False)
    
    if not run_command(f"git remote add origin {remote_url}"):
        return False
    
    # 推送
    print("\n🚀 推送到 GitHub...")
    # 尝试推送，失败时使用 --force 强制推送
    if run_command("git push -u origin main"):
        print("\n" + "=" * 60)
        print("✅ 上传成功！")
        print("=" * 60)
        print(f"\n🌐 仓库地址: {remote_url}")
        print(f"\n💡 后续更新:")
        print("   git add .")
        print('   git commit -m "更新说明"')
        print("   git push")
        return True
    else:
        print("\n⚠️  推送失败，尝试强制推送...")
        print("   (使用 --force 覆盖远程仓库)")
        if run_command("git push -u origin main --force"):
            print("\n" + "=" * 60)
            print("✅ 强制推送成功！")
            print("=" * 60)
            print(f"\n🌐 仓库地址: {remote_url}")
            return True
        else:
            print("\n❌ 推送失败")
            print("\n可能原因:")
            print("  1. 仓库不存在 - 请先在 GitHub 创建仓库")
            print("  2. 认证失败 - 需要输入 GitHub 用户名和密码/Token")
            print(f"\n快速创建仓库: https://github.com/new")
            return False


def main():
    """主函数"""
    # 检查 Git
    if not check_git():
        return 1
    
    # 获取脚本所在目录（而不是当前工作目录）
    script_dir = Path(__file__).parent.absolute()
    print(f"\n📁 脚本所在目录: {script_dir}")
    
    # 切换到脚本所在目录
    os.chdir(script_dir)
    print(f"📂 工作目录已切换至: {Path.cwd()}")
    
    # 确认目录
    confirm = clean_input(input("\n是否在此目录上传项目? (Y/n, 默认: Y): ")).lower()
    if confirm == 'n':
        print("❌ 已取消")
        return 0
    
    # 获取配置
    config = get_user_input()
    
    # 执行上传
    if init_and_push(config):
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())
