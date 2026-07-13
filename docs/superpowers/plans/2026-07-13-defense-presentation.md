# Defense Presentation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 生成一套与项目代码事实一致、由曾铁昭和龙梦婷共同讲解的 14 页答辩 PPT 及逐页答辩稿。

**Architecture:** 使用项目交付文档、路由注册、模块代码、测试结果和前端截图建立证据清单；以同一份页序内容模型驱动 PPT 和答辩稿，保证两份产物完全对齐。PPT 使用 `@oai/artifact-tool` 生成，采用项目现有羊皮纸白、学院酒红、深墨和古铜视觉体系。

**Tech Stack:** JavaScript ES modules、`@oai/artifact-tool`、PowerPoint、Markdown、项目现有 React 前端截图、思源黑体。

## Global Constraints

- PPT 共 14 页，五个业务模块分别独立占一页并作为同等重点。
- 客服 Agent 使用 Dify + Python；客户研判、企业助手、学生助手、智能报告使用纯 Python。
- 曾铁昭与龙梦婷共同覆盖所有模块，第 10—11 页接力讲解模块关系和完整请求流。
- 全部文字使用思源黑体，通过字号、字重、颜色和留白区分层级。
- 总讲解时间控制在约 13 分钟，预留 2 分钟用于切换和现场停顿。
- 不把规划能力、Mock 或未完成现场验收的外部链路写成已上线。
- PPT 视觉继承前端，不使用通用蓝色科技风、彩虹渐变、玻璃拟态或密集卡片墙。

---

### Task 1: 建立内容证据和页序模型

**Files:**
- Create: 外部临时工作区 `source-notes.txt`
- Create: 外部临时工作区 `slide-content.json`

**Interfaces:**
- Consumes: `main.py`、`routers/`、`services/`、`models/`、`tests/`、`docs/integration/最终集成交接报告_20260712.md`、前端设计说明与截图。
- Produces: 14 页标题、主讲人、用时、可见文案、讲稿要点和图片路径组成的结构化内容。

- [ ] **Step 1: 核对五模块 Router、Service、Model、前端入口和技术边界**

  运行 `rg` 检查路由注册、模块文件和前端页面；输出必须覆盖客户研判、客服 Agent、企业助手、学生助手和智能报告。

- [ ] **Step 2: 重新执行与答辩数据相关的验证命令**

  运行 `pytest -q`、前端测试和生产构建；只采用本轮实际结果。

- [ ] **Step 3: 编写 14 页内容模型**

  每页明确标题、受众可见文案、主讲人、建议用时、上下页关系和素材路径；五个模块页统一包含业务问题、核心能力、输入/处理/输出、代码位置、上下游和实现边界。

### Task 2: 编写逐页答辩稿

**Files:**
- Create: `答辩材料/海外留学教育服务平台_答辩稿.md`

**Interfaces:**
- Consumes: Task 1 的 14 页内容模型。
- Produces: 与 PPT 一一对应的中文逐页讲稿。

- [ ] **Step 1: 生成逐页口语稿**

  每页包含主讲人、建议用时、可直接朗读的正文、切页/交接提示和必要演示提示。

- [ ] **Step 2: 检查双主讲覆盖和总时长**

  核对曾铁昭、龙梦婷均讲到模块关系；全部建议用时合计不超过 13 分钟。

- [ ] **Step 3: 检查真实性和必问题**

  搜索技术边界、未完成功能和 Vibe Coding 回答，确保无过度承诺。

### Task 3: 生成 14 页 PowerPoint

**Files:**
- Create: 外部临时工作区 `build-defense-deck.mjs`
- Create: `答辩材料/海外留学教育服务平台_答辩PPT.pptx`

**Interfaces:**
- Consumes: Task 1 的内容模型、前端截图和统一视觉 Token。
- Produces: 16:9、14 页、思源黑体的 PowerPoint 文件。

- [ ] **Step 1: 初始化 artifact-tool 工作区**

  使用 presentations skill 的 `setup_artifact_tool_workspace.mjs` 初始化外部临时目录。

- [ ] **Step 2: 实现统一母版与 14 页页面**

  使用羊皮纸白、学院酒红、深墨、古铜；页面采用编辑式网格和细线分隔；模块关系和请求流使用简洁原生形状，其他页面优先使用真实前端截图。

- [ ] **Step 3: 导出 PPTX**

  执行生成脚本并确认文件存在、页数为 14。

### Task 4: 渲染、检查与修订

**Files:**
- Create: 外部临时工作区 `preview/`
- Create: 外部临时工作区 `qa/`
- Modify: `答辩材料/海外留学教育服务平台_答辩PPT.pptx`
- Modify: `答辩材料/海外留学教育服务平台_答辩稿.md`

**Interfaces:**
- Consumes: Task 2 和 Task 3 的产物。
- Produces: 通过版式、内容和一致性检查的最终交付文件。

- [ ] **Step 1: 渲染全部 14 页并生成总览图**

  使用 `render_slides.py` 和 `create_montage.py`，确认 14 张页面图均成功生成。

- [ ] **Step 2: 逐页检查完整尺寸图片**

  检查文字溢出、遮挡、标题换行、截图裁切、颜色和字体层级；发现问题后修改并重新渲染。

- [ ] **Step 3: 执行结构检查**

  使用 `slides_test.py` 检查画布溢出；搜索 PPT/讲稿中的模块名称、主讲人、技术边界和 Vibe Coding，确认页序一致。

- [ ] **Step 4: 最终交付检查**

  确认 PPTX 和 Markdown 可读取、文件名清晰、无临时占位符、无敏感配置、无未核实完成声明。
