# 硬件、技术栈与安装顺序

核对日期2026-10-26。单机实测与容量建议分开；不是采购性能保证。

| 项目 | 本次实际 |
|---|---|
| 系统/CPU/内存 | Windows11，i7-12700KF，64GB DDR4 |
| 显卡 | RTX5080，16GB显存 |
| 电源 | 用户报告额定1000W金牌全模组；历史黑屏原因未证明 |
| 数字人 | H3 FL2VA pruned INT8 convrot；8实际步；Turbo v4 step600 EMA LoRA1.0；Euler/simple |
| 画幅 | 原生1024×576，24fps，124帧约5.167秒；1920×1080排版合成 |
| 声音 | Ming-3.0-tts-0.5b，GPU官方BFloat16路径，同一真实参考 |
| 字幕/检查 | Qwen3-ASR-0.6B＋Qwen3-ForcedAligner-0.6B，CPU |
| 程序画面 | Python＋Pillow＋NumPy＋OpenCV＋FFmpeg，CPU渲染 |
| 本地推理环境 | ComfyUI0.32.0，PyTorch2.12.1+cu130，SageAttention；历史组合，不是最新版要求 |
| T8节点快照 | git提交7a99dba76f6b0d8ed44e33375fe83ac84ebbcfa1，当时工作树干净 |
| Ming权重修订 | 8d66b70a00f05ad183fa8a863b4ce609fc83cbc0 |

满意成片192.792秒，以程序动画为主体，穿插4段已认可人物；修订只重做4段配音、复用12段声音。一个新人物候选因眨眼问题弃用，开头用已确认照片/大字。不能宣传全片一次H3生成或8步已经解决眼神。

## 分享对象的配置建议

| 路线 | 起点建议 | 验证状态 |
|---|---|---|
| 复刻本地路线 | NVIDIA16GB显存、64GB内存、现代桌面多核CPU、NVMe SSD | 上述5080组合已实测；同显存其他卡未逐一验证 |
| 更宽裕 | NVIDIA24GB或以上、64–128GB内存 | 容量建议，未测耗时/性价比，不保证更快 |
| 已有8–12GB显存 | 先写稿、配音评估与程序动画；H3单独做低负载可行性测试 | 本项目未验证，不列最低配置 |
| 无合适显卡 | 先用真人录音或许可TTS做程序动画，人物另评估设备/服务 | 替代路线，不是完整本地复刻 |

新项目建议至少150GB空闲空间，保存多模型/候选宜200GB以上；这是工程容量建议。五个H3相关文件实际合计约40.28GiB：基模19.53、文本编码器14.61、视频VAE4.85、音频VAE0.564、LoRA0.726，尚不含Ming、ASR、环境、缓存与素材。SSD总容量可考虑1–2TB，关键是实际空闲。

电源按显卡厂商及整机匹配，不能凭金牌/1000W保证稳定。[NVIDIA规格](https://www.nvidia.com/en-us/geforce/graphics-cards/50-series/rtx-5080/)列5080为16GB、整机建议850W；非公版查具体型号。不固定报价，也不要求所有人买5080。

## 必需软件与来源

1. 能读写本地文件、执行Python/FFmpeg并维护任务的编程智能体。写稿模型可在线，在线写稿与智能体推理消耗其服务Token；本地媒体推理不向在线视频API计Token，仍有电费、时间和硬件成本。
2. [ComfyUI H3指南](https://docs.comfy.org/tutorials/video/minimax/minimax-h3)、[H3官方模型](https://huggingface.co/MiniMaxAI/MiniMax-H3)。本次使用社区量化/裁剪权重，不是官方全量权重直接进16GB。下载时核对量化发布者、兼容性与哈希。
3. [T8音频节点](https://github.com/T8mars/comfyui-minimax-h3-audio-T8)、[Turbo节点](https://github.com/Larryvrh/ComfyUI-MiniMax-H3-Turbo)。版本须与ComfyUI、权重一起记档，生产中不盲目全部升级。
4. [Ming-3.0-tts](https://github.com/inclusionAI/Ming-3.0-tts)，用0.5b，不与tiny混淆。本例设置TTS/Chinese、use_spk_emb=true、cfg2.0、sigma0.25、temperature0、raw_text=true、trim_silence=true、max_decode_steps1000；编码/生成seed记档。0.95倍速仅是本例音色选择，一次无变调处理，不是通用必须值。
5. [Qwen3-ASR及ForcedAligner](https://github.com/QwenLM/Qwen3-ASR)、FFmpeg/ffprobe。本例CPU Ming路径失败已停，不宣传CPU语音已验证。
6. 动画环境安装Pillow、NumPy、OpenCV及合法中文字体；不打包Windows商业字体分发。

Turbo作者说明4–8步、simple调度、强度1.0；本项目选8步。20步原生路线另行验证，不能在同一个加速LoRA上把steps改20当升级。[来源](https://github.com/Larryvrh/ComfyUI-MiniMax-H3-Turbo)

lock_source不保证逐音素口型，仍需画面检查；T8作者明确此限制。[说明](https://github.com/T8mars/comfyui-minimax-h3-audio-T8/blob/main/examples/workflows/02-audio-control/README.md)

## 安装顺序

1. 安装智能体客户端，解压技能；把项目位置设到非系统盘。
2. 安装FFmpeg和CPU动画环境，运行doctor检查缺项。ComfyUI、Ming、ASR分别用兼容环境，避免混装冲突的transformers/torch依赖。
3. 按上游说明安装ComfyUI、两类节点和五类匹配权重；复制runtime.example.json为项目runtime.json，填本机路径。示例相对路径以配置文件所在目录为基准；模型名按本机下拉框/API候选原文填写，Windows子目录分隔符可能是反斜线，不能仅按磁盘文件存在就认为API枚举也匹配。
4. TEMP/TMP、HF_HOME、TORCH_HOME等逐项指向工作盘；只改当前目录不足以搬走缓存。模型完整后再离线推理，不把缺失权重当已安装。
5. 本机ComfyUI启动后运行doctor --check-comfy；只检查节点，不证明推理通过。共享服务有别人的任务时不夺取、不全局清队列。
6. 用自己的图/声做短试听、CPU动画预览和H3短样片，满意后完整生产。

本包没有模型、环境安装器或GPU自动排队器。API图需绑定输入、适配版本；构图通过不等于在他人机器实测通过。

## 许可

新编规程/辅助代码可按包内许可再编辑。Ming代码标注MIT，H3是其社区模型许可，整个栈不能笼统称MIT。模型、节点、字体和素材各按自身许可，本包不重打包。[Ming许可](https://github.com/inclusionAI/Ming-3.0-tts/blob/main/LICENSE)、[H3许可](https://huggingface.co/MiniMaxAI/MiniMax-H3/blob/main/LICENSE)。这里识别来源，不替具体场景作许可结论。
