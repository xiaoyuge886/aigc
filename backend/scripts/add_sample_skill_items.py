#!/usr/bin/env python3
"""
Add sample skill items to skill packages
为技能包添加示例技能项
"""
import asyncio
import sys
import json
from pathlib import Path

# 添加项目根目录到 Python 路径
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from loguru import logger
from sqlalchemy import text
from services.database import DatabaseService


async def add_sample_skill_items():
    """添加示例技能项"""
    logger.info("Adding sample skill items...")

    # 获取数据库服务
    db_service = DatabaseService()
    await db_service.initialize()

    try:
        async with db_service.async_session() as session:
            # 获取所有包的版本ID
            result = await session.execute(text("""
                SELECT sp.id, sp.name, sp.identifier,
                       (SELECT id FROM skill_package_versions
                        WHERE package_id = sp.id
                        ORDER BY created_at DESC
                        LIMIT 1) as version_id
                FROM skill_packages sp
                WHERE sp.is_active = 1
            """))

            packages = result.fetchall()

            # 定义示例技能项
            sample_skills = {
                'marketing-skills': [
                    {
                        'name': 'seo_audit',
                        'display_name': 'SEO Audit',
                        'description': 'Perform comprehensive SEO audit on a website',
                        'skill_content': '''# SEO Audit Skill

You are an SEO expert. When asked to perform an SEO audit:

1. **Analyze the URL provided** by the user
2. **Check technical SEO**:
   - Page load speed
   - Mobile responsiveness
   - SSL certificate
   - Sitemap and robots.txt
3. **Review on-page SEO**:
   - Title tags and meta descriptions
   - Header structure (H1, H2, H3)
   - Keyword usage and density
   - Internal linking
4. **Assess content quality**:
   - Content length and depth
   - Readability score
   - Multimedia usage
5. **Provide recommendations** with priority (High/Medium/Low)

Output your findings in a structured markdown format with actionable recommendations.''',
                        'skill_type': 'markdown',
                        'trigger_keywords': ['seo', 'audit', 'optimization']
                    },
                    {
                        'name': 'copywriting_assistant',
                        'display_name': 'Copywriting Assistant',
                        'description': 'Help create compelling marketing copy',
                        'skill_content': '''# Copywriting Assistant

You are a professional copywriter specializing in marketing content.

When helping with copywriting:
- Use the AIDA framework (Attention, Interest, Desire, Action)
- Focus on benefits, not just features
- Use clear, concise language
- Include strong call-to-actions
- Target the specific audience mentioned
- Adapt tone to the brand (professional, casual, urgent, etc.)

Ask for the following if not provided:
1. Product/Service being promoted
2. Target audience
3. Key benefits/features
4. Desired tone
5. Format needed (ad, email, landing page, etc.)''',
                        'skill_type': 'markdown',
                        'trigger_keywords': ['copy', 'writing', 'content', 'ad']
                    }
                ],
                'data-analysis-skills': [
                    {
                        'name': 'data_visualization',
                        'display_name': 'Data Visualization',
                        'description': 'Create charts and visualizations from data',
                        'skill_content': '''# Data Visualization Skill

You are a data visualization expert. Help users create effective visualizations:

1. **Understand the data** - Ask for:
   - Data format (CSV, JSON, etc.)
   - Data structure and columns
   - Number of rows and data types

2. **Determine the best chart type**:
   - Line charts: Trends over time
   - Bar charts: Comparisons
   - Pie charts: Parts of a whole (max 5-7 categories)
   - Scatter plots: Relationships between variables
   - Heatmaps: Correlation matrices

3. **Provide Python code** using:
   - matplotlib for basic charts
   - seaborn for statistical visualizations
   - plotly for interactive charts

4. **Include styling tips**:
   - Color schemes
   - Labels and annotations
   - Legend placement
   - Grid lines and axes

Generate complete, runnable code with sample data.''',
                        'skill_type': 'markdown',
                        'trigger_keywords': ['chart', 'graph', 'visualization', 'plot']
                    },
                    {
                        'name': 'statistical_analysis',
                        'display_name': 'Statistical Analysis',
                        'description': 'Perform statistical analysis on datasets',
                        'skill_content': '''# Statistical Analysis Skill

You are a statistician. Help with statistical analysis:

**Descriptive Statistics:**
- Mean, median, mode, standard deviation
- Percentiles and quartiles
- Skewness and kurtosis

**Inferential Statistics:**
- Hypothesis testing (t-test, chi-square, ANOVA)
- Confidence intervals
- P-values interpretation
- Effect size calculations

**Regression Analysis:**
- Linear regression
- Multiple regression
- Logistic regression
- Correlation analysis

When analyzing data:
1. Ask about the research question
2. Recommend appropriate tests
3. Check assumptions (normality, homoscedasticity, etc.)
4. Interpret results in plain language
5. Provide Python/R code using scipy, statsmodels, or similar

Always include:
- Code with comments
- Interpretation of results
- Visualization of findings
- Assumptions and limitations''',
                        'skill_type': 'markdown',
                        'trigger_keywords': ['statistics', 'analysis', 'test', 'regression']
                    }
                ],
                'productivity-boost': [
                    {
                        'name': 'task_automation',
                        'display_name': 'Task Automation',
                        'description': 'Automate repetitive tasks with scripts',
                        'skill_content': '''# Task Automation Skill

You are a automation expert. Help users automate repetitive tasks:

**Common Automations:**
1. File operations (rename, move, organize)
2. Data processing (CSV, Excel, JSON)
3. Web scraping
4. Email automation
5. Report generation

**For each request:**
1. Understand the task workflow
2. Identify repetitive steps
3. Recommend appropriate tools:
   - Python scripts
   - Shell scripts
   - Workflow automation tools (Zapier, n8n)
4. Provide complete, tested code
5. Include error handling
6. Add setup instructions

**Best Practices:**
- Use clear variable names
- Add comments and documentation
- Handle edge cases
- Provide logging
- Make code reusable

Always ask:
- What is the current workflow?
- What is the frequency?
- What tools are available?
- What is the skill level of the user?''',
                        'skill_type': 'markdown',
                        'trigger_keywords': ['automate', 'script', 'batch', 'repetitive']
                    },
                    {
                        'name': 'workflow_optimizer',
                        'display_name': 'Workflow Optimizer',
                        'description': 'Optimize and streamline workflows',
                        'skill_content': '''# Workflow Optimization Skill

You are a workflow optimization consultant. Help improve productivity:

**Analysis Framework:**
1. Map current workflow steps
2. Identify bottlenecks
3. Find redundant steps
4. Spot automation opportunities
5. Calculate time savings

**Optimization Strategies:**
- **Eliminate**: Remove unnecessary steps
- **Automate**: Use tools for repetitive tasks
- **Delegate**: Assign to appropriate team members
- **Batch**: Group similar tasks together
- **Simplify**: Reduce complexity

**For each workflow:**
1. Document the current process
2. Measure time spent on each step
3. Identify pain points
4. Propose specific improvements
5. Estimate time/cost savings
6. Suggest tools to implement

**Tools to recommend:**
- Project management (Asana, Trello, Linear)
- Documentation (Notion, Confluence)
- Automation (Zapier, Make, n8n)
- Communication (Slack, Discord)

Provide actionable recommendations with priority ranking.''',
                        'skill_type': 'markdown',
                        'trigger_keywords': ['workflow', 'optimize', 'improve', 'efficient']
                    }
                ]
            }

            # 为每个包添加技能项
            for pkg_id, pkg_name, identifier, version_id in packages:
                if version_id is None:
                    logger.warning(f"Package {pkg_name} has no version, skipping...")
                    continue

                skills = sample_skills.get(pkg_name, [])
                if not skills:
                    logger.warning(f"No sample skills defined for {pkg_name}")
                    continue

                for skill_data in skills:
                    try:
                        # 检查是否已存在
                        existing = await session.execute(
                            text("SELECT id FROM skill_items WHERE name = :name"),
                            {"name": skill_data['name']}
                        )
                        if existing.scalar_one_or_none():
                            logger.info(f"Skill {skill_data['name']} already exists, skipping...")
                            continue

                        # 插入技能项
                        await session.execute(text("""
                            INSERT INTO skill_items (
                                package_id, package_version_id, name, display_name,
                                description, skill_content, skill_type,
                                trigger_keywords, is_builtin, is_active, created_at, updated_at
                            ) VALUES (
                                :package_id, :package_version_id, :name, :display_name,
                                :description, :skill_content, :skill_type,
                                :trigger_keywords, 1, 1, datetime('now'), datetime('now')
                            )
                        """), {
                            "package_id": pkg_id,
                            "package_version_id": version_id,
                            **skill_data,
                            "trigger_keywords": json.dumps(skill_data.get('trigger_keywords', []))
                        })

                        logger.info(f"✓ Added skill: {skill_data['name']} to {pkg_name}")

                    except Exception as e:
                        logger.warning(f"Error adding skill {skill_data.get('name')}: {e}")

                await session.commit()

            # 显示统计
            count_result = await session.execute(text("""
                SELECT COUNT(*) FROM skill_items
            """))
            total_skills = count_result.scalar_one()

            logger.info(f"✓ Successfully added sample skills! Total skills in database: {total_skills}")

    except Exception as e:
        logger.error(f"Error adding sample skill items: {e}")
        raise
    finally:
        await db_service.close()


if __name__ == "__main__":
    asyncio.run(add_sample_skill_items())
