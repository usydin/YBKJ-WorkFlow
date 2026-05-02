# OCR Lab (OCR 技术验证实验室)

本目录用于存放 OCR 技术的独立验证脚本与测试样例。

## 目录说明

- `ocr_probe.py`: 核心验证脚本框架，支持模拟识别与写入暂存区。
- `README.md`: 本说明文档。

## 使用方式

### 1. 模拟文本识别并输出到文件
使用现有文本文件模拟 OCR 识别结果：
```bash
.venv/bin/python tools/ocr_lab/ocr_probe.py --text dataset/samples/text_samples/realistic_wechat_records_sample.txt --output outputs/ocr_text/sample_ocr_result.txt
```

### 2. 模拟识别并写入 OCR 暂存区
```bash
.venv/bin/python tools/ocr_lab/ocr_probe.py --text dataset/samples/text_samples/realistic_wechat_records_sample.txt --to-staging
```

### 3. 测试图片识别 (当前阶段仅作占位提示)
```bash
.venv/bin/python tools/ocr_lab/ocr_probe.py --image dataset/samples/screenshots_raw/manual_test/test.png
```

## 注意事项

1. **不要提交真实截图**：严禁将包含敏感信息的图片提交到 Git。
2. **独立运行**：本目录下的脚本不作为主程序的启动依赖。
3. **输出产物**：`outputs/ocr_text/` 下的 `.txt` 文件已被 Git 忽略，不会提交。
