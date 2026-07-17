# 数据与版本管理政策

## 基本原则

本仓库用于保存研究设计、分析代码、派生汇总结果、图表和写作记录，不作为受限数据库或参与者原始数据的分发渠道。仓库即使设置为私有，也不改变原数据库的许可条件。

## 可以提交

- 自行编写的分析和实验代码。
- 研究方案、预注册、伦理草案、文献综述和论文草稿。
- 不包含可识别个人信息的聚合统计结果。
- 为当前论文生成的类别级汇总 CSV 和图表。
- 交互式 VAD 3D 模型源代码及本地化开源依赖。
- 数据获取说明、校验值和复现步骤。

## 不得提交

- `DREAMER.mat` 及 DREAMER 原始 EEG/ECG 信号。
- CASE 原始或完整生理信号副本。
- NRC-VAD v2.1 完整词典、压缩包及其重新打包版本。
- 新招募参与者的原始评分、生理信号或可识别信息。
- API 密钥、访问令牌、邮箱密码或设备凭据。
- 虚拟环境、缓存和可重新生成的大型中间文件。

## 本地数据位置

推荐在每台电脑分别建立以下本地文件，不通过 Git 同步：

```text
DREAMER.mat
public_data/case_pilot/case_dataset/
public_data/case_pilot/nrc_vad/
data/raw/
data/interim/
data/processed/
```

这些路径已经写入 `.gitignore`。

## 提交前检查

```bash
git status --short
git diff --cached --stat
git ls-files | grep -E "DREAMER\.mat|NRC-VAD|case_dataset/data|data/raw"
```

最后一条命令应没有输出。若出现受限文件，应先从暂存区移除：

```bash
git restore --staged <path>
```

## 大型派生文件

确有必要同步且许可允许的大型派生文件，应优先使用 GitHub Release 或 Git LFS，并在上传前再次确认其不包含可逆推出参与者身份的信息。当前阶段不需要使用 Git LFS。

