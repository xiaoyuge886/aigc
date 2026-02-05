"""
GitHub Skill Service
从 GitHub 拉取技能到本地调试目录
"""
import os
import re
import shutil
import subprocess
import yaml
from pathlib import Path
from typing import Optional, List, Dict, Any
from urllib.parse import urlparse
import httpx
from loguru import logger

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.database import SkillDB, UserDB


class GitHubSkillService:
    """GitHub 技能服务 - 拉取和管理 GitHub 上的技能"""

    def __init__(self, db: AsyncSession):
        self.db = db
        # 调试目录
        self.debug_skills_dir = Path(__file__).parent.parent / ".claude" / "debug_skills"
        self.debug_skills_dir.mkdir(parents=True, exist_ok=True)

        # 临时克隆目录
        self.clone_cache_dir = Path(__file__).parent.parent / ".claude" / "git_cache"
        self.clone_cache_dir.mkdir(parents=True, exist_ok=True)

        # GitHub API 配置
        self.github_api_base = "https://api.github.com"
        self.github_token = os.getenv("GITHUB_TOKEN")  # 可选，提高速率限制

    # ========================================================================
    # GitHub 搜索
    # ========================================================================

    async def search_github_repos(
        self,
        query: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        搜索 GitHub 仓库

        Args:
            query: 搜索关键词
            limit: 返回结果数量

        Returns:
            仓库列表
        """
        try:
            headers = {
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "AIGC-Skills-Hub/1.0"
            }

            if self.github_token:
                headers["Authorization"] = f"token {self.github_token}"

            async with httpx.AsyncClient(timeout=30.0) as client:
                params = {
                    "q": f"{query} in:name,description",
                    "sort": "stars",
                    "order": "desc",
                    "per_page": min(limit, 100)
                }

                response = await client.get(
                    f"{self.github_api_base}/search/repositories",
                    headers=headers,
                    params=params
                )
                response.raise_for_status()

                data = response.json()
                repos = []

                for item in data.get("items", []):
                    repos.append({
                        "name": item["name"],
                        "full_name": item["full_name"],
                        "description": item.get("description", ""),
                        "url": item["html_url"],
                        "clone_url": item["clone_url"],
                        "stars": item["stargazers_count"],
                        "language": item.get("language"),
                        "updated_at": item.get("updated_at")
                    })

                logger.info(f"Found {len(repos)} repos for query: {query}")
                return repos

        except Exception as e:
            logger.error(f"Error searching GitHub: {e}")
            raise

    # ========================================================================
    # Git 操作
    # ========================================================================

    def parse_github_url(self, url: str) -> Dict[str, str]:
        """
        解析 GitHub URL

        支持格式：
        - https://github.com/owner/repo
        - https://github.com/owner/repo.git
        - git@github.com:owner/repo.git
        - owner/repo

        Returns:
            {"owner": "...", "repo": "...", "url": "..."}
        """
        from urllib.parse import unquote

        # 如果 URL 被编码了，先解码
        decoded_url = unquote(url)

        # SSH 格式
        if decoded_url.startswith("git@github.com:"):
            match = re.match(r"git@github\.com:(.+)/(.+\.git)", decoded_url)
            if match:
                owner, repo = match.groups()
                return {
                    "owner": owner,
                    "repo": repo.replace(".git", ""),
                    "url": decoded_url
                }

        # HTTPS 格式
        if decoded_url.startswith("https://"):
            parsed = urlparse(decoded_url)
            parts = parsed.path.strip("/").split("/")
            if len(parts) >= 2:
                owner, repo = parts[0], parts[1].replace(".git", "")
                return {
                    "owner": owner,
                    "repo": repo,
                    "url": f"https://github.com/{owner}/{repo}.git"
                }

        # owner/repo 格式
        if "/" in decoded_url and not decoded_url.startswith("http"):
            parts = decoded_url.split("/")
            if len(parts) == 2:
                owner, repo = parts
                return {
                    "owner": owner,
                    "repo": repo,
                    "url": f"https://github.com/{owner}/{repo}.git"
                }

        raise ValueError(f"Invalid GitHub URL: {url}")

    async def clone_repository(
        self,
        repo_url: str,
        branch: Optional[str] = None,
        timeout: int = 300
    ) -> Path:
        """
        克隆 GitHub 仓库到临时目录（异步执行）

        Args:
            repo_url: 仓库 URL
            branch: 分支名（可选）
            timeout: 超时时间（秒）

        Returns:
            克隆目录路径
        """
        import asyncio

        try:
            parsed = self.parse_github_url(repo_url)
            cache_dir = self.clone_cache_dir / f"{parsed['owner']}_{parsed['repo']}"

            # 清理旧的缓存 - 确保完全删除
            if cache_dir.exists():
                try:
                    shutil.rmtree(cache_dir)
                    logger.info(f"Cleaned up existing cache: {cache_dir}")
                except Exception as e:
                    logger.warning(f"Failed to remove cache directory, will retry: {e}")
                    # 尝试强制删除
                    import time
                    time.sleep(0.5)
                    if cache_dir.exists():
                        shutil.rmtree(cache_dir, ignore_errors=True)

            # 构建克隆命令 - 简化选项避免兼容性问题
            cmd = [
                "git", "clone",
                "--depth", "1",           # 浅克隆
                "--no-tags",              # 不下载标签
                "--single-branch",        # 只克隆指定分支
            ]

            if branch:
                cmd.extend(["--branch", branch])

            cmd.append(parsed['url'])
            cmd.append(str(cache_dir))

            logger.info(f"Cloning repository: {parsed['url']} to {cache_dir}")

            # 使用 asyncio 执行异步子进程
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )

                if process.returncode != 0:
                    error_msg = stderr.decode() if stderr else "Unknown error"
                    logger.error(f"Git clone failed: {error_msg}")
                    # 清理失败的克隆
                    if cache_dir.exists():
                        shutil.rmtree(cache_dir, ignore_errors=True)
                    raise ValueError(f"Clone failed: {error_msg}")

                # 验证克隆是否成功
                if not cache_dir.exists():
                    raise ValueError(f"Clone directory not created: {cache_dir}")

                git_dir = cache_dir / ".git"
                if not git_dir.exists():
                    shutil.rmtree(cache_dir)
                    raise ValueError(f"Clone incomplete: .git directory missing")

            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                logger.error(f"Git clone timeout after {timeout}s")
                if cache_dir.exists():
                    shutil.rmtree(cache_dir, ignore_errors=True)
                raise ValueError(f"Clone timeout: {repo_url}")

            logger.info(f"Repository cloned successfully to: {cache_dir}")
            return cache_dir

        except Exception as e:
            logger.error(f"Error cloning repository: {e}")
            raise

    # ========================================================================
    # 技能检测和安装
    # ========================================================================

    def detect_skills(self, repo_dir: Path) -> List[Dict[str, Any]]:
        """
        在仓库目录中检测技能

        查找包含 skill.md 或 SKILL.md 的目录

        Args:
            repo_dir: 仓库目录

        Returns:
            技能列表
        """
        skills = []

        # 查找所有 skill.md/SKILL.md 文件
        for skill_md in repo_dir.rglob("skill.md"):
            skill_dir = skill_md.parent
            skills.append(self._parse_skill_info(skill_dir, skill_md, repo_root=repo_dir))

        for SKILL_MD in repo_dir.rglob("SKILL.md"):
            skill_dir = SKILL_MD.parent
            # 避免重复（如果同时有 skill.md 和 SKILL.md）
            if not any(s["path"] == skill_dir for s in skills):
                skills.append(self._parse_skill_info(skill_dir, SKILL_MD, repo_root=repo_dir))

        logger.info(f"Detected {len(skills)} skills in repository")
        return skills

    def _parse_skill_info(self, skill_dir: Path, skill_md: Path, repo_root: Optional[Path] = None) -> Dict[str, Any]:
        """
        解析技能信息

        Args:
            skill_dir: 技能目录
            skill_md: skill.md 文件路径
            repo_root: 仓库根目录（用于计算相对路径）
        """
        # 读取 skill.md 内容
        content = skill_md.read_text(encoding="utf-8", errors="ignore")

        # 解析 YAML front matter
        frontmatter = {}
        markdown_content = content

        frontmatter_pattern = r'^---\s*\n(.*?)\n---\s*\n(.*)$'
        match = re.match(frontmatter_pattern, content, re.DOTALL)

        if match:
            frontmatter_text = match.group(1)
            markdown_content = match.group(2)
            try:
                frontmatter = yaml.safe_load(frontmatter_text) or {}
            except yaml.YAMLError as e:
                logger.warning(f"Failed to parse YAML frontmatter in {skill_md}: {e}")

        # 从 frontmatter 中提取 name 和 description
        skill_id = skill_dir.name
        name = frontmatter.get('name', skill_id)
        description = frontmatter.get('description', '')

        # 如果 frontmatter 中没有 description，则从 markdown 内容中提取
        if not description:
            lines = markdown_content.split("\n")
            for line in lines[:30]:
                line = line.strip()
                if line.startswith("#"):
                    description = line.lstrip("#").strip()
                    break
                if line and not line.startswith("<!--") and not line.startswith("---"):
                    description = line[:200]
                    break

        # 如果仍然没有找到描述，使用备用逻辑
        if not description:
            description = f"{name} - 技能"

        # 检查是否有 skill.json
        skill_json = skill_dir / "skill.json"
        config = None
        if skill_json.exists():
            import json
            try:
                config = json.loads(skill_json.read_text(encoding="utf-8"))
            except Exception as e:
                logger.warning(f"Failed to parse skill.json: {e}")

        # 计算相对路径
        relative_path = str(skill_dir)  # 默认使用绝对路径
        if repo_root:
            try:
                relative_path = str(skill_dir.relative_to(repo_root))
            except ValueError:
                # skill_dir 不在 repo_root 下，使用父目录作为参考
                relative_path = str(skill_md.relative_to(skill_md.parents[1]))

        return {
            "name": name,
            "path": skill_dir,
            "description": description,
            "content": content,
            "config": config,
            "relative_path": relative_path
        }

    async def install_skill_from_github(
        self,
        repo_url: str,
        skill_name: str,
        subpath: Optional[str] = None,
        branch: Optional[str] = None,
        author_id: Optional[int] = None
    ) -> SkillDB:
        """
        从 GitHub 安装技能到调试目录

        Args:
            repo_url: GitHub 仓库 URL
            skill_name: 技能名称
            subpath: 技能子路径（如果仓库包含多个技能）
            branch: 分支名
            author_id: 作者 ID

        Returns:
            创建的技能记录
        """
        try:
            # 1. 克隆仓库
            repo_dir = await self.clone_repository(repo_url, branch=branch)

            # 2. 定位技能目录
            if subpath:
                skill_source_dir = repo_dir / subpath
            else:
                skill_source_dir = repo_dir / skill_name

            if not skill_source_dir.exists():
                raise ValueError(f"Skill directory not found: {skill_source_dir}")

            # 3. 检查技能文件
            skill_md = skill_source_dir / "skill.md"
            if not skill_md.exists():
                skill_md = skill_source_dir / "SKILL.md"

            if not skill_md.exists():
                raise ValueError(f"skill.md not found in {skill_source_dir}")

            # 4. 复制到调试目录
            skill_target_dir = self.debug_skills_dir / skill_name
            if skill_target_dir.exists():
                shutil.rmtree(skill_target_dir)

            shutil.copytree(skill_source_dir, skill_target_dir)

            logger.info(f"Skill installed to: {skill_target_dir}")

            # 6. 创建数据库记录（查找实际的 skill.md 或 SKILL.md）
            actual_skill_md = skill_target_dir / "skill.md"
            if not actual_skill_md.exists():
                actual_skill_md = skill_target_dir / "SKILL.md"
            skill_info = self._parse_skill_info(skill_target_dir, actual_skill_md, repo_root=repo_dir)

            # 检查是否已存在
            existing = await self.db.execute(
                select(SkillDB).where(SkillDB.name == skill_name)
            )
            existing_skill = existing.scalar_one_or_none()

            if existing_skill:
                # 更新现有记录
                existing_skill.skill_path = str(skill_target_dir)
                existing_skill.status = 'testing'
                existing_skill.description = skill_info["description"]
                await self.db.commit()
                await self.db.refresh(existing_skill)
                logger.info(f"Updated existing skill: {skill_name}")
                return existing_skill

            # 创建新记录
            new_skill = SkillDB(
                name=skill_name,
                description=skill_info["description"],
                skill_path=str(skill_target_dir),
                status='testing',  # 新安装的技能标记为测试中
                author_id=author_id,
                usage_count=0,
                source='github'  # 标记为 GitHub 拉取
            )

            self.db.add(new_skill)
            await self.db.commit()
            await self.db.refresh(new_skill)

            logger.info(f"Created new skill record: {new_skill.id} - {new_skill.name}")
            return new_skill

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error installing skill from GitHub: {e}")
            raise

    async def list_repo_skills(self, repo_url: str) -> List[Dict[str, Any]]:
        """
        列出仓库中的所有技能

        Args:
            repo_url: GitHub 仓库 URL

        Returns:
            技能列表
        """
        try:
            # 克隆仓库
            repo_dir = await self.clone_repository(repo_url)

            # 检测技能
            skills = self.detect_skills(repo_dir)

            # 转换为响应格式
            result = []
            for skill in skills:
                result.append({
                    "name": skill["name"],
                    "description": skill["description"],
                    "relative_path": skill["relative_path"],
                    "has_config": skill["config"] is not None
                })

            return result

        except Exception as e:
            logger.error(f"Error listing repo skills: {e}")
            raise

        finally:
            # 清理缓存
            pass  # 保留缓存以便重复使用

    # ========================================================================
    # 清理
    # ========================================================================

    def cleanup_cache(self, max_age_hours: int = 24):
        """清理旧的克隆缓存"""
        import time
        try:
            current_time = time.time()
            max_age_seconds = max_age_hours * 3600

            for cache_dir in self.clone_cache_dir.iterdir():
                if cache_dir.is_dir():
                    # 检查目录年龄
                    dir_age = current_time - cache_dir.stat().st_mtime
                    if dir_age > max_age_seconds:
                        shutil.rmtree(cache_dir)
                        logger.info(f"Cleaned up old cache: {cache_dir}")

        except Exception as e:
            logger.error(f"Error cleaning up cache: {e}")
