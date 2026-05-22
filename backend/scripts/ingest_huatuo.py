import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))
# Huatuo-26M 问答对数据集
# 引用：https://arxiv.org/abs/2305.01526
# @misc{li2023huatuo26m,
#   title={Huatuo-26M, a Large-scale Chinese Medical QA Dataset},
#   author={Jianquan Li and Xidong Wang and Xiangbo Wu and Zhiyi Zhang
#           and Xiaolong Xu and Jie Fu and Prayag Tiwari and Xiang Wan
#           and Benyou Wang},
#   year={2023}, eprint={2305.01526}, archivePrefix={arXiv},
#   primaryClass={cs.CL}}
from app.vectorstore import build_qa_knowledge_base, ITER_HUATUO_LOCAL_PATH


if __name__ == "__main__":
    local_path = ITER_HUATUO_LOCAL_PATH
    if (local_path / "dataset_info.json").exists():
        print(f"使用本地数据集: {local_path}")
    else:
        print("本地数据集不存在，请先运行 scripts/download_huatuo.py")

    count = build_qa_knowledge_base(batch_size=64, rate_per_minute=4000)
    print(f"已写入问答对向量片段: {count}")