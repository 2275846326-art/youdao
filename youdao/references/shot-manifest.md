# 可检查的分镜清单

多镜头交接、批量制作或需自动核对素材时使用；单镜建议可继续用表格。已有清单则映射字段，不维护两套时间线。本脚本只核对结构、连续主时间线和本地文件，不代替语义、空间或视听验收。

将清单存为 UTF-8 JSON：顶层 `schema_version: 1`、可选 `duration_sec`，以及非空 `shots` 数组。每镜必填：
- `id`：不重复的字符串。
- `start_sec`、`end_sec`：有限非负秒数，结束晚于开始；按成片时间排列。
- `purpose`：画面承担的信息任务。
- `status`：`planned` / `ready` / `rendered` / `accepted`。
- `assets`：数组，每项 `path`（相对清单或绝对本地路径）和 `role`（控制或呈现什么）；无素材可为空。

可选 `spoken_text`、`visual`、`camera`、`light`、`end_state` 与其他项目字段由制作人保留，检查器不改写或删除。多轨叠加记录在镜头内部；此数组代表连续的主时间线。刻意留白也写成一个有目的的镜头，不以重叠主镜表达叠加。

`rendered` / `accepted` 另需 `output_path`。`accepted` 需非空 `review` 数组，每项为 `aspect`、`result`、`evidence`，结果取 `passed` / `not_checked` / `not_applicable` / `failed`；至少一项通过，不能仍有 failed 或 not_checked。只记录实际检查结果，不为通过校验编造证据。图片交付可将声音列不适用。用户批准和技术通过仍分开记录。

运行：`python <skill目录>/scripts/check_shots.py <清单.json>`。

默认检查现有文件（非零普通文件），计划中的缺图警告；ready 及以后缺图报错。`--structure-only` 只检查结构，输出会标明文件未检。退出码 0 表示此检查范围内无错误，1 为数据问题，2 为读取/格式错误；输出 JSON 便于留档。时长容差默认 0.04 秒，可用 `--tolerance` 显式设置。

远程链接应先记录平台任务与下载状态，供其他工具核实；此脚本不联网，也不把 URL 当本地文件。扩展名和文件存在不能证明媒体可解码：交付前还需媒体探测、必要时解码、画面查看和试听，具体范围记录在 review。
