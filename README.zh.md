# VisionCleanse

![VisionCleanse 主视觉图 — 杂乱照片经重复检测后整理入文件夹，重复照片进入隔离区](docs/assets/illustrations/hero_banner.png)

[![CI](https://github.com/MinhTriTM/vision-cleanse/actions/workflows/ci.yml/badge.svg)](https://github.com/MinhTriTM/vision-cleanse/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

当前版本：**0.2.0**。([Tiếng Việt](README.md) · [English](README.en.md))

清理计算机视觉数据集：检测近似重复图片，防止训练集 / 验证集 / 测试集之间的数据泄漏。

## 功能

- **第一环——精确匹配：** 用 MD5（或 SHA-256）找出字节完全相同的复制文件。
- **第二环——感知哈希：** 用 Pillow + numpy 自行实现的 pHash 和 dHash（不依赖 `imagehash`）。可检测尺寸缩放、格式转换和 JPEG 重新压缩。深度裁剪和旋转暂不支持，需要后续环。
- **划分优先级：** 保留优先级为 `test > val > train`。同一划分内保留分辨率最高者，其次文件最大者，再按文件名排序（结果确定，可复现）。
- **标签冲突：** 同一张（或极相似）图片出现在两个类别下时，**绝不自动删除**，而是写入 `conflict_report.csv` 供人工复核。
- **删除安全：** 默认**演练模式**（只出报告，不动文件）。使用 `--apply` 时，被剔除的文件会被**移至隔离目录**（保持原目录结构）并附 `manifest.json`，永不直接删除。
- **标注同步：** 图片旁的 YOLO `.txt` 标签会随图片一起移入隔离区。传入 `--coco` 时，COCO JSON 会导出一份清理后的副本，原文件永不被覆盖。
- **数据集健康检查（0.2.0）：** 除重复检测外，还检查 0 字节文件、损坏文件、空白/纯色图片、过小图片、划分目录中的异常文件、缺失 YOLO 标签、孤立/格式错误/空 YOLO 标签、同名不同内容文件，以及测试集内部重复。发现 `.txt` 标签时自动启用 YOLO 检查（或用 `--yolo` 强制启用）。
- **三种语言（0.2.0）：** 命令行提示和检查名称支持越南语、英语和中文，通过 `--lang vi|en|zh` 切换（默认 `vi`）。`report.json` 中的键始终为英文，便于程序读取。

## “数据集干净”是什么意思

当报告中 `"clean": true` 时，表示**所有已启用的检查均已通过**（无错误、无警告）。这不是绝对保证：近似重复检测本身是模糊问题，任何工具都无法发现语义层面的标签错误。报告会列出全部已运行的检查，因此结论可审计。

## 安装

```bash
pip install -e .
```

仅需 Pillow 和 numpy。测试使用 Python 自带的 `unittest`，无需 pytest：

```bash
python -m unittest discover -s tests -v
```

（未安装时可用 `PYTHONPATH=src` 运行。）

## 命令行

```bash
# 预览（演练模式，默认）：不移动任何文件
vision-cleanse /path/to/dataset

# 真正隔离重复文件
vision-cleanse /path/to/dataset --apply

# 中文提示，强制启用 YOLO 检查
vision-cleanse /path/to/dataset --apply --lang zh --yolo

# 附带 COCO 同步
vision-cleanse /path/to/dataset --apply --coco /path/to/annotations.json
```

期望的数据集结构：

```
dataset/
  train/<class>/a.jpg   # 或 train/a.jpg（无类别子目录）
  val/<class>/b.jpg
  test/<class>/c.jpg
```

YOLO 布局（Ultralytics 标准）——期望结构：

```
dataset_root/
  images/train/img1.jpg
  images/train/img2.jpg
  images/val/img3.jpg
  labels/train/img1.txt
  labels/train/img2.txt
  labels/val/img3.txt
  data.yaml   # train: images/train, val: images/val, names: [cat, dog]
```

`test` 划分是可选的：只有 train/val 的数据集同样可以完整运行，
没有 test 时的保留优先级为 `val > train`。

不存在的划分会被跳过并给出警告。报告写入
`vision_cleanse_report/report.json`，出现标签冲突时还会写入
`vision_cleanse_report/conflict_report.csv`。

## Python API

```python
from vision_cleanse import clean

report = clean("/path/to/dataset", dry_run=True)
print(report["duplicate_groups"], report["to_quarantine"])

# 真正执行
report = clean("/path/to/dataset", dry_run=False,
               quarantine_dir="/path/to/quarantine")
```

## 支持的数据集结构

自动识别两种结构：

- **Classic：**`train/<class>/a.jpg`（或 `train/a.jpg`），YOLO `.txt`
  标签与图片同目录。
- **YOLO：**`images/train/a.jpg` + `labels/train/a.txt` + `data.yaml`
  （类别名来自 `data.yaml` 的 `names`）。此模式下标签文件按
  `labels/` 树结构进入隔离区。

## 图表

```bash
pip install vision-cleanse[charts]
vision-cleanse /path/to/dataset --charts
```

导出 25 张 PNG 图表到 `<report-dir>/charts`（见 `docs/charts.md`）：
划分/类别概览，文件大小、宽、高、长宽比、面积分布；有 YOLO 标签时：
每图框数、每类框数、框宽/高/面积分布、框中心散点与热力图、类别 ×
划分热力图；以及清洗结果：按方法分组的重复组、按划分/原因的移除数、
按检查/严重程度的健康问题、保留与隔离对比。无数据的图表会被跳过并
在 `report.json` 中注明原因（不画空图）。

演示数据集的完整示例图库（23 张图表、流水线图与插图——每张图表的说明见 `docs/charts.md`）：

![每划分图片数](docs/assets/charts/split_sizes.png)

![各划分占比](docs/assets/charts/split_share.png)

![每类别图片数](docs/assets/charts/class_images.png)

![按划分堆叠的每类别图片数](docs/assets/charts/class_split_stacked.png)

![文件大小分布](docs/assets/charts/file_size_hist.png)

![图片宽度分布](docs/assets/charts/width_hist.png)

![图片高度分布](docs/assets/charts/height_hist.png)

![宽高比分布](docs/assets/charts/aspect_hist.png)

![图片面积分布](docs/assets/charts/area_hist.png)

![每图框数](docs/assets/charts/instances_per_image.png)

![每类别框数](docs/assets/charts/boxes_per_class.png)

![框宽度分布](docs/assets/charts/box_width_hist.png)

![框高度分布](docs/assets/charts/box_height_hist.png)

![框面积分布](docs/assets/charts/box_area_hist.png)

![框中心散点图](docs/assets/charts/box_centers_scatter.png)

![框中心热力图](docs/assets/charts/box_centers_heatmap.png)

![框宽高散点图](docs/assets/charts/box_wh_scatter.png)

![类别×划分框热力图](docs/assets/charts/class_split_heatmap.png)

![按方法分组的重复组](docs/assets/charts/dup_by_method.png)

![按划分重叠的重复组 Venn 图](docs/assets/charts/duplicate_groups_venn.png)

![按划分的移除文件](docs/assets/charts/removals_by_split.png)

![按原因的移除文件](docs/assets/charts/removals_by_reason.png)

![每划分保留与隔离对比](docs/assets/charts/kept_vs_quarantined.png)

![流水线流程图](docs/assets/pipeline.png)

![两张近似图片：一张保留，一张隔离](docs/assets/illustrations/duplicates_concept.png)

![TRAIN、VAL、TEST 文件夹与保护 TEST 集免于泄漏的护盾](docs/assets/illustrations/splits_protection.png)

## 阈值

当 pHash **或** dHash 的汉明距离在阈值内（默认 64 位哈希取 10）时，一对图片即被视为近似重复。两种哈希互补：dHash 读取水平梯度符号，在 JPEG 噪声下非常稳定（实测即使 JPEG 质量为 30 时距离仍为 0，包括 pHash 会漂移至 16 的平滑图片）；pHash 读取全局低频结构，能发现 dHash 看不见的变化（dHash 只比较左右相邻像素）。OR 规则偏向召回；由于文件只是被隔离并附报告，永不静默删除，用户仍可复核。请在自己的数据上实测后再用
`--phash-threshold` / `--dhash-threshold` 调整。

## 局限（直言）

- 深度裁剪、旋转、翻转和大幅颜色变化暂不支持，需要深度特征环和几何验证环。
- 近似重复分组目前为 pairwise O(n²)。数据集非常大时，请先按划分扫描，或等待 FAISS 环。
- 不承诺“100% 干净”：近似重复是模糊问题。请先在自生成的变体上测量准确率/召回率，再信任默认阈值。
- 无法读取的文件会被跳过并列入 `images_unreadable`，不会导致程序崩溃。
