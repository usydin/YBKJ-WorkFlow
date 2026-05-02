#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os
import sys
from pathlib import Path

# 将项目根目录加入 sys.path 以便导入 app 模块
root_dir = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(root_dir))

from app.database import SQLiteDataPool
from app.backup import JSONLBackupService
from app.intake_service import IntakeService
from app.ocr_staging_service import OCRStagingService

def main():
    parser = argparse.ArgumentParser(description="OCR 技术验证探针 (OCR Lab Probe)")
    parser.add_argument("--image", type=str, help="待识别的图片路径")
    parser.add_argument("--text", type=str, help="模拟 OCR 输出的文本文件路径")
    parser.add_argument("--output", type=str, help="识别结果输出到的 txt 路径")
    parser.add_argument("--to-staging", action="store_true", help="是否写入 OCR 暂存区")
    parser.add_argument("--source-name", type=str, default="OCR Lab Probe", help="来源名称")
    
    args = parser.parse_args()

    if not args.image and not args.text:
        print("错误：必须指定 --image 或 --text 参数。")
        parser.print_help()
        sys.exit(1)

    ocr_result = ""

    # 1. 获取识别内容
    if args.text:
        text_path = Path(args.text)
        if not text_path.exists():
            print(f"错误：文本文件不存在: {args.text}")
            sys.exit(1)
        print(f"正在从模拟文本读取识别结果: {args.text}")
        with open(text_path, "r", encoding="utf-8") as f:
            ocr_result = f.read().strip()
    elif args.image:
        print(f"检测到图片路径: {args.image}")
        print("提示：当前版本尚未集成 OCR 引擎，请先使用 --text 模拟识别结果，或将外部 OCR 文本粘贴到 OCR 暂存区。")
        sys.exit(0)

    if not ocr_result:
        print("错误：识别结果为空。")
        sys.exit(1)

    # 2. 输出到文件
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(ocr_result)
        print(f"识别结果已保存到: {args.output}")

    # 3. 写入 OCR 暂存区
    if args.to_staging:
        try:
            data_pool = SQLiteDataPool()
            data_pool.initialize()
            backup_service = JSONLBackupService()
            intake_service = IntakeService(data_pool, backup_service)
            ocr_service = OCRStagingService(data_pool, intake_service)
            
            record_id = ocr_service.create_staging_record(
                raw_text=ocr_result,
                source_type="future_ocr",
                source_name=args.source_name,
                note="由 tools/ocr_lab/ocr_probe.py 模拟写入"
            )
            print(f"成功写入 OCR 暂存区，记录 ID: {record_id}")
            print("请进入主程序“OCR暂存”页面查看、修正并导入。")
        except Exception as e:
            print(f"写入 OCR 暂存区失败: {e}")
            sys.exit(1)

if __name__ == "__main__":
    main()
