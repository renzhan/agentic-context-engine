#!/bin/bash

# ACE Ticket Learning 启动脚本
# 用于运行 ticket 学习训练

# 设置脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# 切换到项目根目录
cd "$PROJECT_ROOT"

# 运行 ACE Ticket Learning
python ACE_Ticket/ace_ticket_learning.py \
    --source ticket \
    --max-tickets 200 \
    --max-concurrent 1 \
    --batch-size 5

