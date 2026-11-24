# 安全政策 | Security Policy

本项目定位为本地离线维保工作流，仍处于测试与打包验证阶段。未确认正式生产支持版本或安全 SLA。

- 聊天记录、姓名、员工映射、客户台账、OCR 截图及日报均可能包含敏感信息，不得上传未经授权的原始资料。
- 使用合成或脱敏测试数据，保留人工确认与审计记录；不得将未经确认的解析结果视为正式日报。
- 检查日志、输出、运行数据库、临时文件、凭据和导出文件是否被 Git 追踪；历史扫描及真实数据核查需要独立证据。
- 发现问题通过已建立的授权维护人员私密渠道报告，提供脱敏复现、影响及版本；不在公开 Issue 发布敏感内容。

This is a local maintenance workflow project in a test and packaging-validation stage. No production support or security SLA is asserted. Protect chat records, employee identity mappings, customer records, OCR images and reports. Use synthetic or sanitized fixtures and retain human confirmation. Report issues privately through an established authorized maintainer channel. A dedicated reporting endpoint, historical secret scan and security test results require separate verification.

本政策不等同于安全审计通过。
