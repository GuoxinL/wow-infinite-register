---
name: wow-infinite-register
slug: wow-infinite-register
displayName: 某某世界无限注册助手
description: |
  在真实 Windows 桌面上自动创建《某某世界》角色，
  并在遇到"阵营人口不平衡"等拒绝弹窗时无限后退重试，
  直到真正建号成功。
  当用户要求"无限注册/创建某某世界角色/自动重试建号/模拟鼠标键盘创建角色"，
  或需要按指定规则集(PVP/普通)、性别、种族、职业、名字批量重试建号时使用。
  AI 全自动定位坐标（图像识别+逐屏截图验证，无需用户点击采集），
  内置真实桌面控制、截图取证、角色三项校验、安全闸门与客户端3D死锁自恢复；
  开跑前须向用户完整交代流程步骤，经用户明确确认后才启动注册循环。
summary: 自动创建某某世界角色，遇阵营拒绝弹窗自动后退重试，直到建号成功
version: 1.0.0
license: MIT
agent_created: true
---

# 某某世界无限自动挂机创建角色

## 概述

在**真实 Windows 桌面**（非虚拟桌面）上模拟鼠标键盘，按用户指定的规则集、名字、性别、种族、职业创建《某某世界》角色。服务器在阵营不平衡时会拒绝创建，脚本自动后退重来。**坐标定位由 AI 自主驱动**：通过图像识别 + 逐屏截图验证自动定位，无需用户参与点击采集。**但启动注册循环前必须先向用户完整交代流程步骤，等用户明确确认后才开跑。**

## 关键约束（务必遵守）

1. **绝不手动点右上角关闭窗口**来跳过弹窗；一律走界面内"确定/后退"按钮。
2. **安全闸门**：规则集或角色三项（性别/种族/职业）任一校验不过，绝不进入命名页、绝不点"完成"。宁可停机也不误建角色。
3. **坐标由 AI 自动定位，不依赖用户点击，也不使用 `presets/` 的写死坐标**。所有坐标必须来自**当前这台显示器**的实时截图 + 图像识别（见第 2 步），显示器/分辨率/UI 缩放变化后必须重新定位。`presets/` 仅作字段结构参考。
4. **DPI 口径必须一致**：`desktop_ctl.py`、`calibrate.py`、`vision.py` 都在进程启动时调用 `SetProcessDpiAwareness(2)`，坐标统一为物理像素。否则 150% 缩放下会差 1.5 倍，点击全部错位。
5. **焦点必须锁定游戏**：`desktop_ctl.focus()` 已用 `AttachThreadInput` + ALT 键技巧绕过 Windows 前台锁定。每次点击前先 `focus('某某世界')` 并确认 `GetForegroundWindow()` 是游戏窗口——**这是最常见的失败根因**：焦点在 WorkBuddy 时点击会落在浏览器上，导致坐标重复、界面不前进。
6. **真实桌面**：运行期间不要移动鼠标/键盘做其它操作，否则坐标错位。
7. **开跑闸门（必须）**：坐标定位、validate/probe 校验等准备工作可自主完成；但**启动试跑（trial）或无限模式（infinite）前，必须先向用户完整交代流程步骤，并等用户明确确认后才执行**。用户未确认前，绝不启动任何注册循环。这两处开跑是唯一需要用户点头的环节，其余全程自主。
8. **停机必须切回 AI Agent（必须）**：游戏是全屏的，脚本停下后若不切回窗口，用户盯着游戏画面根本察觉不到已停。`register.py` 的 `main()` 已用 `try/finally` 包住试跑/无限分支，任何退出（正常跑完、`safety_stop` 中止、异常崩溃）都会调用 `focus_agent()` 自动切回 `WorkBuddy`。**例外**：用户主动喊"停"导致的后台任务 kill 不会走 finally——此时 AI 必须**在终止任务后手动执行一次** `python -c "import desktop_ctl as d; d.focus('WorkBuddy')"`，确认前台回到 Agent 再向用户报告。每次向用户汇报"已停止/试跑结束"前，都要先确认前台是 WorkBuddy。

## 工作流

### 第 1 步：确定变量

从用户指令中收集 6 项（缺哪项问哪项，不要臆测；用户说"沿用上次/示例"则用 preset 默认组合）：

| 变量  | 说明            | 示例        |
| --- | ------------- | --------- |
| 规则集 | PVP / 普通 / 其它 | PVP       |
| 主名  | 角色主名字         | 刘一波誓死     |
| 副名  | 副名字           | 守护龙傲天     |
| 性别  | 男 / 女         | 男         |
| 种族  | 含阵营（部落/联盟）    | 塑风者天裔（部落） |
| 职业  | 职业名           | 德鲁伊       |

收集齐后直接进入第 2 步定位，定位过程本身会截图验证选择结果。**但开跑前（第 4 步试跑、第 5 步无限）必须先向用户交代完整流程并拿到明确确认，见第 4 步「开跑交代」。**

### 第 2 步：AI 自动定位坐标（必经，取代人工点击采集）

坐标**全部由 AI 通过实时截图 + 图像识别自动确定**，不要求用户点击。两种手段配合：

- **截图取证**：`python -u desktop_ctl.py shot <name>.png` 抓全屏，用 ViewImage 看图判断界面状态和元素位置；`cropfile` 裁剪放大局部精确读坐标。
- **像素识别**：`python -u vision.py` 用连通域检测红色按钮（`red_buttons`）、金色边框（`gold_regions`）、绿勾（`green_checks`），返回每个区域的 `box / cx,cy / area`。

逐屏推进流程（**每步都先 `focus` 再点击，点完 screenshot 验证界面确实前进**）：

1. 登录页：识别中央红色「重新连接」→ 点击 → 截图确认进入规则集页。
2. 规则集页：识别目标规则集卡片的金色边框（`gold_regions` 最大框）取中心；识别右下「选择」红按钮 → 点击 → 截图确认进入创建页。
3. 创建页（关键，务必逐项截图验证选中态）：
   - 性别：顶部中间两个图标，点目标（男=左/女=右），裁剪放大确认目标图标出现金色高亮框（**默认可能是反的，必须先验证**）。
   - 种族：左侧两列头像（蓝=联盟/红=部落），点目标阵营的目标头像，裁剪放大确认高亮框落在正确头像上。**种族必须先选对**，否则某些职业（如德鲁伊对库尔提拉斯人）是灰色锁定、点不动。
   - 职业：底部图标栏，点目标图标，用 `vision` 检测该图标区域出现金框、原选中图标金框消失。
   - 自定外观：右下红按钮 → 点击 → 截图确认进入命名页。
4. 命名页：定位主名/副名输入框 → `type_text` 填入 → `vision.green_checks` 在副名框右侧找到绿勾（这是 `green_box`）；定位红色「完成」按钮（`finish_box` 框住它）→ 点击。
5. 阵营弹窗：点完成约 1-3 秒后弹出，`vision.red_buttons` 在画面中央找到红色「确定」（这是 `dialog_box` + `dialog_confirm` 点击点）→ 点确定回到命名页。
6. 后退链：命名页「后退」→ 创建页「后退」（同一个 `back_1`）→ 角色选择页「后退」（`back_3`，位置更靠左下）→ 回到登录页（截图确认「重新连接」出现）。

把以上实测坐标和检测框写入 `config_run.json`：
- `ui` 用短 key（`reconnect`/`ruleset_confirm`/`custom_appearance`/`name_main`/`name_sub`/`finish`/`dialog_confirm`/`back_1`/`back_3`），**不要带 `ui.` 前缀**。
- 检测框阈值参考基线：`gender` gold>0.20 且 ratio>1.8；`race` halo bright>0.10/gold>0.02；`class` bright>0.12；`ruleset` gold>0.10；`dialog` red>0.45；绿勾>15 像素。用 probe 数值微调，`min` 取选中值的 60-70% 留噪声余量。

### 第 3 步：validate + probe 校验

```bash
python register.py --config config_run.json --mode validate   # 配置合法
python -u register.py --config config_run.json --mode probe    # 打印各检测项 True/False 与数值
```

- 在**登录页** probe：绿勾=0、弹窗红≈0、登录页=True 即就绪。
- 在**创建页三项选中时** probe：`性别/种族/职业` 三项应全 True（这是安全闸门的关键验证）。若某项 False，回第 2 步重测该检测框，不要强行试跑。
- 参考基线（3840×2160）：男 `L≈0.23/R≈0.08`，塑风者天裔 `halo bright≈0.27/gold≈0.05`，德鲁伊 `bright≈0.20`，阵营弹窗 `dialog_red≈0.877/finish_red≈0.000/green=57`。

### 第 4 步：开跑交代 + 用户确认 + 试跑 3 轮

**开跑交代（必经闸门）**：启动任何注册循环前，先用下面这份清单**逐条向用户交代**，然后停下等用户明确回复"确认/开跑/可以"之类的话——**没拿到确认绝不执行**：

> 1. 目标：规则集 / 性别 / 种族（含阵营）/ 职业 / 主名 / 副名，逐项列出。
> 2. 会做什么：AI 已自动定位好坐标，接下来会驱动真实游戏窗口，循环执行「重新连接 → 选规则集 → 选性别/种族/职业 → 填名 → 完成 → 遇阵营弹窗点确定 → 后退重来」。
> 3. 安全边界：任一项校验不过立即停机，绝不误建角色；绝不点右上角关窗。
> 4. 试跑规模：先跑 3 轮验证信号稳定，每轮约 50 秒（约 2-3 分钟）。
> 5. 运行期间：请不要操作鼠标键盘，否则坐标错位。
> 6. 如何停止：随时说"停"，我立即终止后台任务；试跑结束后还会再次向你确认是否进入无限模式。

用户确认后再执行试跑：

```bash
python -u register.py --config config_run.json --mode trial --rounds 3 --tag trial
```

- 每轮输出 `R<n> <kind> 信号=(dialog_red,finish_red,green) 耗时`，写入 `register_trial.jsonl`。
- 正常拒绝应稳定为阵营弹窗信号（dialog_red 高、finish_red≈0、green>0）。
- 关注两类异常：`safety_stop`（规则集未选中，绝不提交）、`drift_*`（角色校验失败）。
- 若出现 `safety_stop` 或持续 drift，**停在此处排障**，不要进入无限。

向用户汇报：成功/失败轮数、信号是否一致、是否有误建或 drift、耗时统计。

### 第 5 步：二次确认 + 进入无限注册

试跑信号稳定并汇报后，**再次向用户交代**无限模式要点并等明确确认——**没有这次确认绝不启动**：

> - 无限模式会持续重试，直到真正建号成功（写 `loop_success.png`）才自动停止。
> - 期间会长时间占用真实桌面（可能数小时），请勿操作鼠标键盘。
> - 内置 3D 死锁自恢复、校验失败安全闸门；随时可说"停"终止。

用户明确同意后，启动无人值守无限模式（后台）：

```bash
python -u register.py --config config_run.json --mode infinite --tag inf
```

该模式：无限重试、遇阵营弹窗自动后退、3D 死锁自动恢复、校验失败按安全闸门停机后自动复位、真正建号成功写 `loop_success.png` 并停止。记下后台 task_id 并向用户报告，用户可随时要求查看进度或叫停。

### 第 6 步：进度与停机处理

- 查进度：看 `register_inf.jsonl` 尾部、`loop_latest_*.png`；成功看 `loop_success.png`。
- 客户端每连续运行数小时可能 3D 死锁；无限模式已内置恢复。
- 若后台任务因会话重启被杀：先用 `focus('WorkBuddy')` 切回 Agent，确认桌面状态后，用同一条 `infinite` 命令重新拉起（换 `--tag`）。
- 若用户要求停止：终止后台任务后，**手动执行一次** `python -c "import desktop_ctl as d; d.focus('WorkBuddy')"` 把前台切回 Agent（kill 不走 finally），确认后再回复用户。脚本自己结束（试跑跑完/成功停机/异常）则由 `main()` 的 `finally → focus_agent()` 自动切回。

## 脚本与文件

- `scripts/vision.py` — 图像识别定位：`red_buttons`/`gold_regions`/`green_checks`/`find_color_regions`；`python vision.py` 分析当前屏幕全部彩色区域。
- `scripts/desktop_ctl.py` — 零依赖 Win32 真实桌面控制（截图/点击/中文输入/像素采样/`focus` 强制置前/信号）。
- `scripts/calibrate.py` — 保留 `capture`/`boxes`/`probe` 兼容命令；DPI 已修正。`capture` 为旧的人工点击模式，全自动流程优先用 vision 定位。
- `scripts/register.py` — 配置驱动主程序：`validate` / `probe` / `trial` / `infinite` 四模式。
- `scripts/config_run.json` — 当前实测配置（AI 自动定位生成，屏幕绑定）。
- `scripts/presets/*.json` — 字段结构样例（**仅供格式参考**）。
- `references/calibration.md` — 校准指南与信号基线（含历史参考坐标，勿直接用）。

## 排障速查

| 现象 | 可能原因 | 处理 |
| --- | --- | --- |
| 点击没反应、坐标重复、界面不前进 | 焦点在 WorkBuddy 不在游戏 | 每次点击前 `focus('某某世界')` 并确认 `GetForegroundWindow()`；已修复的 `focus` 会用 AttachThreadInput+ALT 强制置前 |
| 点击全部错位 1.5 倍 | DPI 口径不一致 | 确认所有脚本顶部有 `SetProcessDpiAwareness(2)`；`desktop_ctl info` 与 `calibrate` 屏幕尺寸应一致 |
| 职业图标灰色点不动 | 种族不支持该职业 | 先选对种族（如德鲁伊需部落塑风者/巨魔/牛头人），再选职业 |
| probe 三项全 0、3D 黑屏 | 客户端渲染死锁 | 点"创建新角色"重建渲染并退回登录页；无限模式自恢复 |
| `safety_stop` | 规则集未被选中 | 检查规则集 detect 框/阈值；勿强行提交 |
| 持续 `drift_creation` | 种族/职业检测框偏移 | 用 vision 重测该选项 detect 框，或重新走第 2 步定位 |
| 绿勾一直不出 | 名字框残留拼接 | 脚本已 Ctrl+A+Delete 清空；检查名字合法性 |
| `login_state` 误判 | finish_box 红色比例漂移 | 调整 `signals.login_red_min/max`（当前默认 0.15/0.65）；登录页约 0.23、命名页约 0.78、弹窗约 0 |
| 信号与基线不符 | 分辨率/显示器/客户端版本变了 | 重走第 2 步 AI 自动定位整套坐标 |
