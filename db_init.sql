-- 智能报告模块 V2 数据库初始化脚本
-- ------------------------------------------------------------
-- 设计说明：
-- 1. 数据库目标版本：MySQL 8。
-- 2. 项目统一采用“无物理外键”策略，因此这里不写 FOREIGN KEY。
-- 3. 所有逻辑关联字段（如 report_id、owner_id、schedule_id）都通过索引提升查询性能。
-- 4. 报告快照只保存聚合指标，不保存心理咨询原文、投诉原文等敏感长文本。

CREATE DATABASE IF NOT EXISTS education_service
  DEFAULT CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE education_service;

CREATE TABLE IF NOT EXISTS report_generation (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键',
  report_type VARCHAR(64) NOT NULL COMMENT '报告类型编码，V2 使用 VARCHAR 方便扩展',
  report_title VARCHAR(255) NOT NULL COMMENT '报告标题',
  report_content JSON NULL COMMENT '按报告类型区分的结构化内容',
  report_html MEDIUMTEXT NULL COMMENT '后端模板渲染 HTML，禁止模型直接输出任意 HTML',
  period_start DATE NULL COMMENT '统计周期开始',
  period_end DATE NULL COMMENT '统计周期结束',
  status ENUM('pending','generating','completed','failed') NOT NULL DEFAULT 'pending' COMMENT '任务状态',
  schema_version INT NOT NULL DEFAULT 2 COMMENT '内容结构版本：历史为1，新报告为2',
  generated_by BIGINT UNSIGNED NULL COMMENT '生成用户ID，逻辑关联 sys_user.id',
  schedule_id BIGINT UNSIGNED NULL COMMENT '定时计划ID，逻辑关联 report_schedule.id',
  retry_of_report_id BIGINT UNSIGNED NULL COMMENT '重试来源报告ID',
  trigger_source ENUM('manual','schedule','retry','system') NOT NULL DEFAULT 'manual' COMMENT '触发来源',
  retry_count INT NOT NULL DEFAULT 0 COMMENT '第几次尝试',
  idempotency_key VARCHAR(128) NULL COMMENT '幂等键：手动请求头或 计划ID+统计周期',
  request_filters JSON NULL COMMENT '生成时筛选条件',
  aggregated_data_snapshot JSON NULL COMMENT '聚合指标快照，不保存敏感原文',
  data_quality JSON NULL COMMENT '数据质量说明',
  error_code VARCHAR(64) NULL COMMENT '机器可读错误码',
  error_message TEXT NULL COMMENT '失败原因',
  started_time DATETIME NULL COMMENT '开始时间',
  completed_time DATETIME NULL COMMENT '完成或失败时间',
  create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  update_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (id),
  UNIQUE KEY uk_report_generation_idempotency (idempotency_key),
  KEY idx_report_generation_type (report_type),
  KEY idx_report_generation_status (status),
  KEY idx_report_generation_period (period_start, period_end),
  KEY idx_report_generation_generated_by (generated_by),
  KEY idx_report_generation_schedule (schedule_id),
  KEY idx_report_generation_retry_of (retry_of_report_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='智能报告生成记录表';

CREATE TABLE IF NOT EXISTS report_schedule (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键',
  report_type VARCHAR(64) NOT NULL COMMENT '报告类型编码',
  cron_expression VARCHAR(64) NOT NULL COMMENT '五段 cron 表达式',
  enabled INT NOT NULL DEFAULT 1 COMMENT '1=启用，0=停用',
  timezone VARCHAR(64) NOT NULL DEFAULT 'Asia/Shanghai' COMMENT '时区',
  period_rule VARCHAR(32) NOT NULL DEFAULT 'previous_week' COMMENT 'previous_day/previous_week/previous_month',
  title_template VARCHAR(255) NULL COMMENT '标题模板，可使用 {start}/{end}/{report_type}',
  filters JSON NULL COMMENT '筛选条件',
  recipients JSON NULL COMMENT '通知接收人',
  created_by BIGINT UNSIGNED NULL COMMENT '创建人ID',
  last_run_time DATETIME NULL COMMENT '最近运行时间',
  last_status VARCHAR(32) NULL COMMENT '最近运行状态',
  last_error TEXT NULL COMMENT '最近运行错误',
  next_run_time DATETIME NULL COMMENT '下次运行时间',
  create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  update_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (id),
  KEY idx_report_schedule_type (report_type),
  KEY idx_report_schedule_enabled (enabled),
  KEY idx_report_schedule_next_run (next_run_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='智能报告定时计划表';

CREATE TABLE IF NOT EXISTS application_material_item (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键',
  application_id BIGINT UNSIGNED NOT NULL COMMENT '申请记录ID',
  student_id BIGINT UNSIGNED NULL COMMENT '学生ID',
  owner_id BIGINT UNSIGNED NULL COMMENT '负责人ID',
  material_name VARCHAR(128) NOT NULL COMMENT '材料名称',
  required INT NOT NULL DEFAULT 1 COMMENT '是否必填',
  deadline DATE NULL COMMENT '截止日期',
  submitted_time DATETIME NULL COMMENT '提交时间',
  status VARCHAR(32) NOT NULL DEFAULT 'pending' COMMENT 'pending/submitted/waived',
  update_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (id),
  KEY idx_material_application (application_id),
  KEY idx_material_student (student_id),
  KEY idx_material_owner (owner_id),
  KEY idx_material_deadline (deadline)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='申请材料明细表';

CREATE TABLE IF NOT EXISTS crm_lead_status_history (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键',
  lead_id BIGINT UNSIGNED NOT NULL COMMENT '线索/客户ID',
  old_status VARCHAR(64) NULL COMMENT '变更前状态',
  new_status VARCHAR(64) NOT NULL COMMENT '变更后状态',
  operator_id BIGINT UNSIGNED NULL COMMENT '操作人ID',
  change_reason VARCHAR(255) NULL COMMENT '变更原因',
  change_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '变更时间',
  PRIMARY KEY (id),
  KEY idx_lead_status_history_lead (lead_id),
  KEY idx_lead_status_history_time (change_time),
  KEY idx_lead_status_history_operator (operator_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='CRM客户阶段变化历史表';

CREATE TABLE IF NOT EXISTS marketing_channel_cost (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键',
  channel VARCHAR(64) NOT NULL COMMENT '渠道名称',
  cost_date DATE NOT NULL COMMENT '投放日期',
  campaign VARCHAR(128) NULL COMMENT '活动名称',
  cost_amount DECIMAL(12,2) NOT NULL DEFAULT 0 COMMENT '投放成本',
  create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (id),
  KEY idx_channel_cost_channel_date (channel, cost_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='市场渠道投放成本表';

CREATE TABLE IF NOT EXISTS customer_contract (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键',
  customer_id BIGINT UNSIGNED NOT NULL COMMENT '客户ID',
  lead_id BIGINT UNSIGNED NULL COMMENT '线索ID',
  channel VARCHAR(64) NULL COMMENT '归因渠道',
  contract_amount DECIMAL(12,2) NOT NULL DEFAULT 0 COMMENT '合同金额',
  signed_time DATETIME NULL COMMENT '签约时间',
  status VARCHAR(32) NOT NULL DEFAULT 'signed' COMMENT 'signed/cancelled/refunded',
  create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  update_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (id),
  KEY idx_contract_customer (customer_id),
  KEY idx_contract_channel_time (channel, signed_time),
  KEY idx_contract_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='客户合同表';

CREATE TABLE IF NOT EXISTS customer_payment (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键',
  contract_id BIGINT UNSIGNED NOT NULL COMMENT '合同ID',
  payment_amount DECIMAL(12,2) NOT NULL DEFAULT 0 COMMENT '回款金额',
  payment_time DATETIME NULL COMMENT '回款时间',
  status VARCHAR(32) NOT NULL DEFAULT 'paid' COMMENT 'paid/refunded/pending',
  create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (id),
  KEY idx_payment_contract (contract_id),
  KEY idx_payment_time (payment_time),
  KEY idx_payment_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='客户回款表';

CREATE TABLE IF NOT EXISTS report_action (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键',
  report_id BIGINT UNSIGNED NOT NULL COMMENT '报告ID',
  suggestion_text TEXT NOT NULL COMMENT '报告建议内容',
  risk_code VARCHAR(64) NULL COMMENT '风险编码，用于识别重复问题',
  owner_id BIGINT UNSIGNED NULL COMMENT '责任人ID',
  due_time DATETIME NULL COMMENT '截止时间',
  status VARCHAR(32) NOT NULL DEFAULT 'pending' COMMENT 'pending/confirmed/done/cancelled',
  target_value DECIMAL(12,2) NULL COMMENT '目标值',
  actual_value DECIMAL(12,2) NULL COMMENT '实际结果',
  completed_time DATETIME NULL COMMENT '完成时间',
  create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  update_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (id),
  KEY idx_report_action_report (report_id),
  KEY idx_report_action_owner (owner_id),
  KEY idx_report_action_status (status),
  KEY idx_report_action_risk_code (risk_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='报告行动闭环表';

CREATE TABLE IF NOT EXISTS student_feedback_ticket (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键',
  student_id BIGINT UNSIGNED NULL COMMENT '学生ID',
  ticket_type VARCHAR(32) NOT NULL DEFAULT 'complaint' COMMENT '工单类型',
  category VARCHAR(64) NULL COMMENT '问题分类',
  priority VARCHAR(32) NOT NULL DEFAULT 'medium' COMMENT 'urgent/high/medium/low',
  status VARCHAR(32) NOT NULL DEFAULT 'open' COMMENT 'open/processing/resolved/closed',
  content TEXT NULL COMMENT '投诉内容，报告快照不保存该原文',
  first_response_time DATETIME NULL COMMENT '首次响应时间',
  resolved_time DATETIME NULL COMMENT '解决时间',
  satisfaction_score INT NULL COMMENT '满意度评分',
  owner_id BIGINT UNSIGNED NULL COMMENT '处理人ID',
  create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  update_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (id),
  KEY idx_feedback_ticket_status (status),
  KEY idx_feedback_ticket_priority (priority),
  KEY idx_feedback_ticket_create_time (create_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='学生投诉反馈工单表';

CREATE TABLE IF NOT EXISTS student_psych_alert (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键',
  student_id BIGINT UNSIGNED NULL COMMENT '学生ID',
  risk_level VARCHAR(32) NOT NULL DEFAULT 'medium' COMMENT 'low/medium/high',
  status VARCHAR(32) NOT NULL DEFAULT 'pending' COMMENT 'pending/following/resolved',
  first_follow_time DATETIME NULL COMMENT '首次跟进时间',
  owner_id BIGINT UNSIGNED NULL COMMENT '跟进负责人ID',
  create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  update_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (id),
  KEY idx_psych_alert_level (risk_level),
  KEY idx_psych_alert_status (status),
  KEY idx_psych_alert_create_time (create_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='学生心理预警表';

