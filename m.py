# 文件名: m.py
import sys
from memori import Memori

# 这里是存记忆的地方，默认在当前文件夹生成 memory.db
DB_PATH = "memory.db"

def main():
    # 初始化
    mem = Memori(db_path=DB_PATH)
    mem.attribution(entity_id="User", process_id="My_Project")

    if len(sys.argv) < 3:
        print("❌ 用法不对，别直接运行脚本，要去指挥 AI 运行！")
        return

    command = sys.argv[1]          # add (存) 或 search (查)
    content = " ".join(sys.argv[2:]) # 内容

    if command == "add":
        mem.add(content)
        display_content = content[:100] + "..." if len(content) > 100 else content
        print(f"✅ [已记住]: {display_content}")
        
    elif command == "search":
        print(f"🔍 [正在回忆]: {content}")
        results = mem.search(content)
        print("--- 回忆内容 ---")
        print(results)

if __name__ == "__main__":
    main()