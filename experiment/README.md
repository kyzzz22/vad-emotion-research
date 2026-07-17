# A2 实验实现

## 随机化

生成 48 个匿名参与者的预分配随机表：

```powershell
python experiment/generate_schedules.py --participants 48 --seed 20260714
```

脚本使用 8 个正交序列，平衡 semantic/induced 场次顺序、lexical/prototype 区块顺序和诱发首个视频效价，每序列预分配 6 人。每个语义区块包含 6 个目标概念和 12 个 filler，分别独立随机；诱发视频正负效价交替，同一概念不连续，并在第 6 个视频后安排休息。Filler 只降低重复目标的显著性，不进入处理后的主分析表。

生成后的 `materials/schedules.csv` 是任务实现的输入，不应在正式招募后重新生成。冻结时记录脚本版本、种子和文件 SHA-256。

每次修改材料后运行跨文件校验：

```powershell
python experiment/validate_materials.py
```

## 尚待接入

正式呈现程序取决于实验室已有平台和生理设备事件接口。冻结前必须补充：视频文件相对路径、精确剪辑时间、事件码格式、设备确认时间戳和原始导出解析器。不要在不知道设备接口时伪造同步实现。

## 浏览器参考任务

先生成配置，再从 `experiment/web` 启动静态服务器：

```powershell
python experiment/build_web_config.py
python -m http.server 8765 --directory experiment/web
```

打开 `http://127.0.0.1:8765`。正式媒体文件按 `media/VID_...mp4` 放置，但受版权保护的影片不进入仓库。页面显示“事件接口未配置”时只能用于主观任务或流程演练，不能声称已完成生理同步。

设备适配器必须在 `app.js` 之前加载，并实现 `window.a2MarkerHook(record)`。`web/marker-adapter.example.js` 只展示接口契约，默认会报错，不能直接用于采集。完成适配后以光电或等效方法测量显示端到记录端延迟。

测试模式为 `http://127.0.0.1:8765/?test=1`，会缩短计时并模拟视频，所有导出均带 `test_mode=1`。自动验收脚本会完成 36 个 semantic 项目、一个 induced 试次、缺失媒体路径、桌面/手机布局和 CSV 导出：

```powershell
node experiment/test_web_task.cjs
```
