#!/bin/bash

# Skill Market Setup Script
# 技能市场设置脚本

echo "🚀 Setting up Skill Market environment..."

# 激活虚拟环境
echo "📦 Activating virtual environment..."
source venv/bin/activate

# 升级 pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# 安装依赖
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# 初始化数据库
echo "🗄️  Initializing database..."
python scripts/init_skill_market.py

echo ""
echo "✅ Setup complete!"
echo ""
echo "To start the server:"
echo "  1. Activate virtual environment: source venv/bin/activate"
echo "  2. Run server: python main.py"
echo ""
echo "API will be available at: http://localhost:8000"
echo "API docs at: http://localhost:8000/docs"
