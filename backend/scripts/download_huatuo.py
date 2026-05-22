"""下载 Huatuo26M-Lite 数据集到本地目录（纯 datasets 库，不加载 torch）"""
import sys
import traceback
from pathlib import Path

LOCAL_DIR = Path(r"C:\System_IT\Evibotchat\Huatuo-26M")


def main():
    LOCAL_DIR.mkdir(parents=True, exist_ok=True)
    print(f"本地缓存目录: {LOCAL_DIR}")

    data_dir = LOCAL_DIR / "data"
    if (data_dir / "dataset_info.json").exists():
        print("数据集已存在于本地，跳过下载。")
        return

    print("正在从 Hugging Face 下载 Huatuo26M-Lite 数据集（约 180k 条 QA 对）...")
    sys.stdout.flush()

    try:
        from datasets import load_dataset

        print("开始 load_dataset...")
        sys.stdout.flush()

        dataset = load_dataset(
            "FreedomIntelligence/Huatuo26M-Lite",
            split="train",
            cache_dir=str(LOCAL_DIR),
            streaming=False,
        )
        print(f"数据集加载完成，共 {len(dataset)} 条")
        sys.stdout.flush()

        dataset.save_to_disk(str(data_dir))
        print(f"数据集已保存到: {data_dir}")
        sys.stdout.flush()

        count_qa = sum(1 for _ in dataset if _.get("question") and _.get("answer"))
        print(f"有效 QA 对: {count_qa}/{len(dataset)}")
        print("下载完成！")

    except Exception as e:
        print(f"下载失败: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()