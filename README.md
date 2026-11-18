> 开服这么久了，还没能建出一个部落 PVP 的号——每次都被「阵营人口不平衡」挡在门外。于是有了这个工具。

# 某某世界无限注册助手

> 一个在**真实 Windows 桌面**上自动创建《某某世界》角色的 AI Skill。当服务器因「阵营人口不平衡」拒绝创建时，自动后退重试，直到真正建号成功。坐标由 AI 通过图像识别 + 逐屏截图验证**全自动定位**，无需人工点击采集。

已上架 SkillHub：[某某世界无限自动挂机创建角色](https://skillhub.cn/skills/user_dc0b813f/wow-infinite-register)

## 真实运行数据（实测，非演示）

5 个批次累计运行 **597 轮 / 约 8.8 小时**，511 次提交创建中 510 次被阵营弹窗拒绝，最终在无限 #3 第 38 轮成功建号。

| 批次 | 日期 | 轮次 |
|---|---|---:|
| 试跑 10 轮 | 2026-11-17 | 10 |
| 试跑 3 轮 | 2026-11-17 | 3 |
| 无限 #1 | 2026-11-17 | 8 |
| 无限 #2 | 2026-11-18 | 538 |
| 无限 #3 | 2026-11-18 | 38（第 38 轮成功）|

建号成功凭证（PVP / 等级 1 / 德鲁伊）：

![角色名特写](evidence/success_detail.png)

全屏截图与原始日志见 [`evidence/`](evidence/)。

## 功能特性

- **全自动坐标定位**：图像识别（连通域检测红按钮 / 金色高亮框 / 绿色对勾）+ 逐屏截图验证，AI 自行确定全部 UI 坐标与检测框，无需用户点击采集。分辨率 / DPI / UI 缩放变化后自动重新定位。
- **真实桌面控制**：零第三方依赖的 Win32 桌面控制（截图、点击、中文输入、像素采样），`AttachThreadInput` + ALT 技巧绕过 Windows 前台锁定，确保焦点锁在游戏窗口。
- **安全闸门**：规则集或角色三项（性别 / 种族 / 职业）任一校验不过，立即停机，绝不进入命名页、绝不误建角色。
- **3D 死锁自恢复**：客户端长时间挂机会出现 3D 黑屏死锁（信号全归零），自动检测并点击「创建新角色」重建渲染、退回登录页。（该恢复逻辑正是从无限 #2 的 86 次 drift 空转中总结修复的。）
- **停机自动回到 Agent**：脚本用 `try/finally` 包住运行分支，任何退出（正常跑完 / 安全停机 / 异常）都会把前台切回 AI Agent 窗口，避免用户对着全屏游戏毫无察觉。
- **双开跑闸门**：启动试跑、启动无限模式前各需一次人工确认；定位、校验等准备工作全程自主。

## 目录结构

```
wow-infinite-register/
├── SKILL.md                          # Skill 定义（frontmatter 含 SkillHub 发布字段）
├── README.md                         # 本文件
├── references/
│   └── calibration.md                # 坐标校准指南与信号基线
├── scripts/
│   ├── register.py                   # 主程序：validate / probe / trial / infinite 四模式
│   ├── desktop_ctl.py                # Win32 真实桌面控制（零依赖）
│   ├── vision.py                     # 图像识别定位（红按钮/金框/绿勾）
│   ├── calibrate.py                  # 坐标采集与检测框校准（兼容旧命令）
│   └── presets/
│       └── pvp-male-skydancer-druid.json   # 字段结构样例（非写死坐标）
└── evidence/                         # 真实运行凭证
    ├── run-statistics.json           # 汇总统计
    ├── register_inf3.jsonl           # 成功批次原始日志（第 38 轮建号）
    ├── register_inf2.jsonl           # 538 轮长跑批次原始日志
    ├── loop_success.png              # 建号成功全屏截图
    └── success_detail.png            # 角色名特写
```

## 使用方法

本仓库是一个 **WorkBuddy / CodeBuddy 兼容的 Skill**（共享 `SKILL.md` + `scripts/` 格式）。安装后通过对话触发：

```
@skill:wow-infinite-register
```

向 AI 说明目标即可（规则集、性别、种族、职业、主名、副名），AI 会：

1. 确认 6 项变量
2. 自动定位坐标（截图 + 图像识别）
3. `validate` / `probe` 校验检测框
4. 向你交代流程并确认后，试跑 3 轮
5. 再次确认后，进入无人值守无限模式，直到建号成功

也可直接运行脚本（需先由 AI 生成 `config_run.json`）：

```bash
cd scripts
python register.py --config config_run.json --mode validate   # 配置校验
python register.py --config config_run.json --mode probe      # 信号探测
python register.py --config config_run.json --mode trial --rounds 3 --tag trial
python register.py --config config_run.json --mode infinite --tag inf
```

> `config_run.json` 是屏幕绑定 + 含个人名字的实测配置，**刻意不随仓库发布**——安装方需按 SKILL 流程在自己机器上自动定位生成。

## 打包发布

仓库内置 Makefile，一条命令生成可安装的 Skill zip：

```bash
make            # 生成 dist/wow-infinite-register-<version>.zip
make list       # 预览将打包的文件
make verify     # 校验 zip 内容
make clean      # 清理 dist/
```

默认只打包 `SKILL.md`、`README.md`、`scripts/`、`references/`，并自动排除 `config_run*.json`、Python 缓存和系统文件；`evidence/`（约 13 MB 实测凭证）默认不打包，需要时执行 `make INCLUDE_EVIDENCE=1`。

zip 内默认套一层 `wow-infinite-register/` 目录；若安装器要求 `SKILL.md` 直接位于根目录，使用 `make NO_PREFIX=1`。Windows 上没有 `python3` 时，追加 `PYTHON=python` 即可。

## 环境要求

- Windows 10/11，真实桌面会话（非虚拟桌面 / 非纯 RDP 无头会话）
- Python 3.x（脚本仅用标准库，无需 pip 安装依赖）
- 3840×2160 实测环境；其他分辨率需重新自动定位坐标
- 目标某某世界客户端已安装并可正常登录

## 信号基线（供排障）

以下为 3840×2160 实测值，`probe` 模式可现场打印对照：

| 状态 | dialog_red | finish_red | green | 含义 |
|---|---:|---:|---:|---|
| 阵营拒绝弹窗 | ≈ 0.871 | ≈ 0.000 | 62 | 创建被拒，后退重试 |
| 建号成功 | ≈ 0.009 | ≈ 0.000 | 0 | 命名页消失，进入角色选择页 |
| 登录页 | ≈ 0 | ≈ 0.234 | 0 | 干净登录页，可开始 |

角色三项选中态：男性 `L≈0.23/R≈0.08`；塑风者天裔 `halo bright≈0.27/gold≈0.05`；德鲁伊 `bright≈0.20`。

## 免责声明

本项目仅用于**个人在自己拥有账号的环境中做自动化技术验证**。请自行评估目标服务器的服务条款——绕过阵营人口平衡限制可能违反部分服务器规则。作者不对因使用本工具产生的账号处罚或数据损失负责。项目不含任何游戏客户端破解、外挂或网络封包篡改，仅通过模拟鼠标键盘操作真实 UI。

## License

MIT
