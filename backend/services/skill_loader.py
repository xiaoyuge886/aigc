"""
Skill Loader Service

Loads skills from .claude/skills directory and parses SKILL.md files
"""
import re
import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional
from loguru import logger


class SkillLoader:
    """Load and parse skills from file system"""
    
    def __init__(self, skills_dir: Optional[Path] = None):
        """
        Initialize skill loader
        
        Args:
            skills_dir: Path to skills directory, defaults to ~/.claude/skills
        """
        if skills_dir is None:
            # Default to project's .claude/skills directory
            project_root = Path(__file__).parent.parent.parent
            skills_dir = project_root / ".claude" / "skills"
        
        self.skills_dir = Path(skills_dir)
        if not self.skills_dir.exists():
            logger.warning(f"Skills directory not found: {self.skills_dir}")
    
    def parse_frontmatter(self, content: str) -> tuple[Dict[str, Any], str]:
        """
        Parse frontmatter from markdown content
        
        Args:
            content: Markdown content with frontmatter
            
        Returns:
            Tuple of (frontmatter_dict, markdown_content)
        """
        # Match frontmatter pattern: ---\n...\n---
        frontmatter_pattern = r'^---\s*\n(.*?)\n---\s*\n(.*)$'
        match = re.match(frontmatter_pattern, content, re.DOTALL)
        
        if not match:
            return {}, content
        
        frontmatter_text = match.group(1)
        markdown_content = match.group(2)
        
        try:
            frontmatter = yaml.safe_load(frontmatter_text) or {}
            return frontmatter, markdown_content
        except yaml.YAMLError as e:
            logger.warning(f"Failed to parse frontmatter YAML: {e}")
            return {}, content
    
    def load_skill_from_file(self, skill_path: Path) -> Optional[Dict[str, Any]]:
        """
        Load a single skill from SKILL.md file
        
        Args:
            skill_path: Path to SKILL.md file
            
        Returns:
            Skill dictionary or None if failed
        """
        try:
            if not skill_path.exists():
                return None
            
            content = skill_path.read_text(encoding='utf-8')
            frontmatter, markdown_content = self.parse_frontmatter(content)
            
            # Extract skill directory name as skill_id
            skill_dir = skill_path.parent
            skill_id = skill_dir.name
            
            # Build skill data
            skill_data = {
                'skill_id': skill_id,
                'name': frontmatter.get('name', skill_id),
                'description': frontmatter.get('description', ''),
                'category': frontmatter.get('category', '其他'),
                'allowed_tools': frontmatter.get('allowed-tools', ''),
                'skill_content': markdown_content,
                'skill_config': None,  # Can be loaded from skill.json if exists
                'is_public': True,  # Skills from file system are public by default
                'is_default': False,
                'usage_count': 0,
                'file_path': str(skill_path),
                'skill_dir': str(skill_dir),
            }
            
            # Try to load skill.json if exists
            skill_json_path = skill_dir / 'skill.json'
            if skill_json_path.exists():
                try:
                    import json
                    with open(skill_json_path, 'r', encoding='utf-8') as f:
                        skill_json = json.load(f)
                        # Merge additional metadata from skill.json
                        if 'description' in skill_json and not skill_data['description']:
                            skill_data['description'] = skill_json.get('description', '')
                        if 'category' in skill_json:
                            skill_data['category'] = skill_json.get('category', skill_data['category'])
                        if 'tags' in skill_json:
                            skill_data['tags'] = skill_json.get('tags', [])
                        skill_data['skill_config'] = json.dumps(skill_json, ensure_ascii=False, indent=2)
                except Exception as e:
                    logger.warning(f"Failed to load skill.json from {skill_json_path}: {e}")
            
            return skill_data
            
        except Exception as e:
            logger.error(f"Error loading skill from {skill_path}: {e}")
            return None
    
    def load_all_skills(self) -> List[Dict[str, Any]]:
        """
        Load all skills from .claude/skills directory
        
        Returns:
            List of skill dictionaries
        """
        skills = []
        
        if not self.skills_dir.exists():
            logger.warning(f"Skills directory does not exist: {self.skills_dir}")
            return skills
        
        # Find all SKILL.md files
        skill_files = list(self.skills_dir.glob('*/SKILL.md'))
        
        logger.info(f"Found {len(skill_files)} skill files in {self.skills_dir}")
        
        for skill_file in skill_files:
            skill_data = self.load_skill_from_file(skill_file)
            if skill_data:
                skills.append(skill_data)
        
        return skills
    
    def get_skill_by_id(self, skill_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific skill by ID
        
        Args:
            skill_id: Skill ID (directory name)
            
        Returns:
            Skill dictionary or None if not found
        """
        skill_path = self.skills_dir / skill_id / "SKILL.md"
        if skill_path.exists():
            return self.load_skill_from_file(skill_path)
        return None


# Global instance
_skill_loader: Optional[SkillLoader] = None


def get_skill_loader() -> SkillLoader:
    """Get or create global skill loader instance"""
    global _skill_loader
    if _skill_loader is None:
        _skill_loader = SkillLoader()
    return _skill_loader
