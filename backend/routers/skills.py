from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Annotated, List, Optional
import os
import shutil
import json
import re
import zipfile
import tempfile
from pathlib import Path

try:
    from agent_server.dependencies import get_current_user, get_db
    from config import PROJECT_ROOT
    from models import Skill
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.agent_server.dependencies import get_current_user, get_db
    from backend.config import PROJECT_ROOT
    from backend.models import Skill

router = APIRouter(prefix="/api/skills", tags=["Skills"])

# Skill 存储目录
SKILL_STORE_DIR = PROJECT_ROOT / "skill_store"


def ensure_skill_dir():
    """确保Skill存储目录存在"""
    SKILL_STORE_DIR.mkdir(exist_ok=True)


def parse_skill_md(file_path: str) -> dict:
    """解析 SKILL.md 文件，提取 name 和 description"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 解析 frontmatter
        frontmatter = {}
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                fm_text = parts[1]
                # 解析 frontmatter 字段
                for line in fm_text.strip().split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        frontmatter[key.strip()] = value.strip()
                
                # 获取 description
                description = frontmatter.get('description', '')
                
                # 尝试从内容中提取 Overview 作为描述
                if not description:
                    rest = parts[2]
                    overview_match = re.search(r'## Overview\s*\n(.+?)(?:\n##|\Z)', rest, re.DOTALL)
                    if overview_match:
                        description = overview_match.group(1).strip()[:200]
                
                return {
                    'name': frontmatter.get('name', ''),
                    'description': description
                }
        
        # 如果没有 frontmatter，使用文件名作为名称
        filename = os.path.basename(file_path)
        name = filename.replace('SKILL.md', '').replace('_', ' ').strip()
        if not name:
            name = '未命名 Skill'
        
        return {
            'name': name,
            'description': '从文件导入的 Skill'
        }
    except Exception as e:
        print(f"解析 SKILL.md 失败: {e}")
        return {
            'name': '未命名 Skill',
            'description': '导入时无法解析描述'
        }


@router.get("")
def get_skills(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    """获取 Skills 列表"""
    skills = db.query(Skill).all()
    
    total = len(skills)
    enabled = sum(1 for s in skills if s.is_enabled)
    
    return {
        "total": total,
        "enabled": enabled,
        "skills": [
            {
                "id": s.id,
                "name": s.name,
                "description": s.description,
                "is_enabled": bool(s.is_enabled),
                "created_at": s.created_at.isoformat() if s.created_at else None,
            }
            for s in skills
        ]
    }


@router.post("")
async def import_skill(
    file: UploadFile = File(None),
    files: List[UploadFile] = File(None),
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    db: Annotated[Session, Depends(get_db)] = None
):
    """导入新的 Skill
    支持三种方式：
    1. 选择文件夹（推荐）- 选择包含 SKILL.md 的文件夹，自动复制所有文件
    2. 上传 ZIP 文件 - 解压后验证包含 SKILL.md
    3. 上传单个 SKILL.md 文件 - 仅复制该文件（不推荐）
    """
    ensure_skill_dir()
    
    # 判断是哪种上传方式
    # files 参数用于文件夹上传（多个文件）
    # file 参数用于单文件上传（ZIP 或 MD）
    uploaded_files = []
    
    if files and len(files) > 0:
        # 方式一：文件夹上传（多个文件）
        print(f"[Skill] 检测为文件夹上传，共 {len(files)} 个文件")
        
        # 验证是否有 SKILL.md
        has_skill_md = False
        for f in files:
            if f.filename and ('SKILL.md' in f.filename or f.filename.endswith('/SKILL.md')):
                has_skill_md = True
                break
        
        if not has_skill_md:
            raise HTTPException(status_code=400, detail="文件夹中未找到 SKILL.md 文件")
        
        # 创建临时目录
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # 保存所有文件到临时目录，保留目录结构
            for f in files:
                if not f.filename:
                    continue
                    
                # 解析相对路径
                relative_path = f.filename.replace('\\', '/')
                # 移除开头的斜杠
                if relative_path.startswith('/'):
                    relative_path = relative_path[1:]
                
                # 创建目标路径
                file_path = temp_path / relative_path
                file_path.parent.mkdir(parents=True, exist_ok=True)
                
                # 写入文件
                content = await f.read()
                with open(file_path, 'wb') as pf:
                    pf.write(content)
            
            # 查找 SKILL.md
            skill_md_path = None
            skill_root = temp_path
            
            for root, dirs, files_list in os.walk(temp_path):
                if 'SKILL.md' in files_list:
                    skill_md_path = Path(root) / 'SKILL.md'
                    skill_root = Path(root)
                    break
            
            if not skill_md_path:
                raise HTTPException(status_code=400, detail="未能找到 SKILL.md 文件")
            
            # 解析 SKILL.md 获取名称和描述
            skill_info = parse_skill_md(str(skill_md_path))
            skill_name = skill_info['name'] or '未命名_Skill'
            skill_description = skill_info['description'] or '从文件夹导入的 Skill'
            
            # 检查是否已存在
            existing = db.query(Skill).filter(Skill.name == skill_name).first()
            if existing:
                raise HTTPException(status_code=400, detail=f"Skill '{skill_name}' 已存在")
            
            # 创建 Skill 存储目录
            safe_name = re.sub(r'[^\w\-_]', '_', skill_name)
            skill_dir = SKILL_STORE_DIR / safe_name
            
            if skill_dir.exists():
                shutil.rmtree(skill_dir)
            skill_dir.mkdir(exist_ok=True)
            
            # 复制所有文件到存储目录
            for item in skill_root.iterdir():
                dest = skill_dir / item.name
                if item.is_dir():
                    shutil.copytree(item, dest)
                else:
                    shutil.copy2(item, dest)
            
            dest_skill_md = skill_dir / "SKILL.md"
            import_method = "文件夹"
    
    elif file:
        # 单文件上传（ZIP 或 MD）
        filename = file.filename.lower()
        
        is_zip = filename.endswith('.zip')
        is_md = filename.endswith('.md')
        
        if not is_zip and not is_md:
            raise HTTPException(status_code=400, detail="请上传 .md 文件或 .zip 压缩包")
        
        # 创建临时目录
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            if is_zip:
                # 方式二：ZIP 文件
                print(f"[Skill] 检测为 ZIP 上传: {file.filename}")
                
                zip_path = temp_path / "upload.zip"
                content = await file.read()
                with open(zip_path, 'wb') as f:
                    f.write(content)
                
                # 解压 ZIP
                extract_dir = temp_path / "extracted"
                extract_dir.mkdir()
                
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_dir)
                
                # 查找 SKILL.md 文件
                skill_md_path = None
                for root, dirs, files_list in os.walk(extract_dir):
                    if 'SKILL.md' in files_list:
                        skill_md_path = Path(root) / 'SKILL.md'
                        skill_root = Path(root)
                        break
                
                if not skill_md_path:
                    raise HTTPException(status_code=400, detail="ZIP 包中未找到 SKILL.md 文件")
                
                # 解析 SKILL.md
                skill_info = parse_skill_md(str(skill_md_path))
                skill_name = skill_info['name'] or '未命名_Skill'
                skill_description = skill_info['description'] or '从 ZIP 包导入的 Skill'
                
                # 检查是否已存在
                existing = db.query(Skill).filter(Skill.name == skill_name).first()
                if existing:
                    raise HTTPException(status_code=400, detail=f"Skill '{skill_name}' 已存在")
                
                # 创建 Skill 存储目录
                safe_name = re.sub(r'[^\w\-_]', '_', skill_name)
                skill_dir = SKILL_STORE_DIR / safe_name
                
                if skill_dir.exists():
                    shutil.rmtree(skill_dir)
                skill_dir.mkdir(exist_ok=True)
                
                # 复制所有文件
                if skill_root == extract_dir:
                    for item in extract_dir.iterdir():
                        dest = skill_dir / item.name
                        if item.is_dir():
                            shutil.copytree(item, dest)
                        else:
                            shutil.copy2(item, dest)
                else:
                    for item in skill_root.iterdir():
                        dest = skill_dir / item.name
                        if item.is_dir():
                            shutil.copytree(item, dest)
                        else:
                            shutil.copy2(item, dest)
                
                dest_skill_md = skill_dir / "SKILL.md"
                import_method = "ZIP"
            
            else:
                # 方式三：单个 MD 文件
                print(f"[Skill] 检测为单个 MD 文件上传: {file.filename}")
                
                tmp_md = temp_path / "upload.md"
                content = await file.read()
                with open(tmp_md, 'wb') as f:
                    f.write(content)
                
                # 解析 SKILL.md
                skill_info = parse_skill_md(str(tmp_md))
                skill_name = skill_info['name'] or '未命名_Skill'
                skill_description = skill_info['description'] or '从文件导入的 Skill'
                
                # 检查是否已存在
                existing = db.query(Skill).filter(Skill.name == skill_name).first()
                if existing:
                    raise HTTPException(status_code=400, detail=f"Skill '{skill_name}' 已存在")
                
                # 创建 Skill 存储目录
                safe_name = re.sub(r'[^\w\-_]', '_', skill_name)
                skill_dir = SKILL_STORE_DIR / safe_name
                skill_dir.mkdir(exist_ok=True)
                
                dest_skill_md = skill_dir / "SKILL.md"
                shutil.copy2(tmp_md, dest_skill_md)
                import_method = "MD文件"
    else:
        raise HTTPException(status_code=400, detail="请上传文件或选择文件夹")
    
    # 验证 SKILL.md 是否存在
    if not dest_skill_md.exists():
        raise HTTPException(status_code=400, detail="SKILL.md 文件未能正确保存")
    
    # 保存到数据库
    skill = Skill(
        name=skill_name,
        description=skill_description,
        source_path=file.filename if file else "folder_upload",
        storage_path=str(skill_dir),
        is_enabled=0
    )
    db.add(skill)
    db.commit()
    db.refresh(skill)
    
    return {
        "id": skill.id,
        "name": skill.name,
        "description": skill.description,
        "is_enabled": bool(skill.is_enabled),
        "message": f"✅ Skill 导入成功（使用{import_method}方式）"
    }


@router.post("/{skill_id}/toggle")
def toggle_skill(
    skill_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    """启用/禁用 Skill"""
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill 不存在")
    
    # 切换状态
    skill.is_enabled = 1 if skill.is_enabled == 0 else 0
    db.commit()
    
    return {
        "id": skill.id,
        "name": skill.name,
        "is_enabled": bool(skill.is_enabled)
    }


@router.delete("/{skill_id}")
def delete_skill(
    skill_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    """删除 Skill"""
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill 不存在")
    
    # 删除存储目录
    if os.path.exists(skill.storage_path):
        shutil.rmtree(skill.storage_path)
    
    # 从数据库删除
    db.delete(skill)
    db.commit()
    
    return {"message": "Skill 已删除"}


@router.get("/{skill_id}/content")
def get_skill_content(
    skill_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    """获取 Skill 详细内容"""
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill 不存在")
    
    skill_md_path = os.path.join(skill.storage_path, "SKILL.md")
    if not os.path.exists(skill_md_path):
        raise HTTPException(status_code=404, detail="SKILL.md 文件不存在")
    
    with open(skill_md_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    return {
        "id": skill.id,
        "name": skill.name,
        "description": skill.description,
        "content": content
    }


@router.get("/enabled/list")
def get_enabled_skills(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    """获取已启用的 Skills 列表（用于加载到 LangGraph）"""
    skills = db.query(Skill).filter(Skill.is_enabled == 1).all()
    
    result = []
    for skill in skills:
        skill_md_path = os.path.join(skill.storage_path, "SKILL.md")
        content = ""
        if os.path.exists(skill_md_path):
            with open(skill_md_path, 'r', encoding='utf-8') as f:
                content = f.read()
        
        result.append({
            "id": skill.id,
            "name": skill.name,
            "description": skill.description,
            "content": content
        })

    return result


@router.post("/create")
def create_skill_by_ai(
    request: dict,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    """AI 根据用户需求创建 Skill
    请求体:
    {
        "name": "Skill名称",
        "description": "Skill描述",
        "prompt": "详细需求描述"
    }
    """
    skill_name = request.get("name", "").strip()
    skill_description = request.get("description", "").strip()
    prompt = request.get("prompt", "")

    if not skill_name:
        raise HTTPException(status_code=400, detail="Skill 名称不能为空")

    print(f"[AI Create Skill] 开始创建: {skill_name}")

    try:
        from openai import OpenAI
        from config import ARK_API_KEY, ARK_BASE_URL

        client = OpenAI(
            api_key=ARK_API_KEY,
            base_url=ARK_BASE_URL
        )

        system_prompt = """你是一个专业的 Skill 创建助手。请根据用户需求生成一个完整的 SKILL.md 文件。

SKILL.md 文件格式要求：
1. Frontmatter (YAML):
---
name: Skill名称
description: 简短描述
---

2. Overview: 功能概述

3. Usage: 使用方法

4. Examples: 使用示例

5. Notes: 注意事项

请直接返回完整的 SKILL.md 内容，不需要其他解释。"""

        response = client.chat.completions.create(
            model="doubao-seed-2-0-mini-260215",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )

        skill_content = response.choices[0].message.content
        print(f"[AI Create Skill] 生成内容长度: {len(skill_content)}")

        skill_content = skill_content.strip()
        if skill_content.startswith("```markdown"):
            skill_content = skill_content[11:]
        elif skill_content.startswith("```"):
            skill_content = skill_content[3]
        if skill_content.endswith("```"):
            skill_content = skill_content[:-3]
        skill_content = skill_content.strip()

    except Exception as e:
        print(f"[AI Create Skill] OpenAI API 调用失败: {e}")
        skill_content = f"""---
name: {skill_name}
description: {skill_description or 'AI创建的Skill'}
---

# {skill_name}

## Overview
{skill_description or '一个由AI创建的Skill。'}

## Usage
1. 激活此Skill
2. 按照指示使用

## Examples
暂无示例

## Notes
- 此Skill由AI自动创建
- 如有问题请联系管理员
"""

    ensure_skill_dir()

    safe_name = re.sub(r'[^\w\-_]', '_', skill_name)
    skill_dir = SKILL_STORE_DIR / safe_name

    if skill_dir.exists():
        shutil.rmtree(skill_dir)
    skill_dir.mkdir(exist_ok=True)

    skill_md_path = skill_dir / "SKILL.md"
    with open(skill_md_path, 'w', encoding='utf-8') as f:
        f.write(skill_content)

    final_name = skill_name
    final_desc = skill_description

    try:
        frontmatter_match = re.search(r'^---\s*\n(.*?)\n---', skill_content, re.DOTALL)
        if frontmatter_match:
            fm_text = frontmatter_match.group(1)
            for line in fm_text.strip().split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip()
                    value = value.strip()
                    if key == 'name' and value:
                        final_name = value
                    elif key == 'description' and value:
                        final_desc = value
    except:
        pass

    existing = db.query(Skill).filter(Skill.name == final_name).first()
    if existing:
        existing.source_path = "ai_created"
        existing.storage_path = str(skill_dir)
        existing.content = skill_content
        db.commit()
        skill = existing
        message = f"✅ Skill '{final_name}' 已更新"
    else:
        skill = Skill(
            name=final_name,
            description=final_desc or "AI创建的Skill",
            source_path="ai_created",
            storage_path=str(skill_dir),
            is_enabled=0
        )
        db.add(skill)
        db.commit()
        db.refresh(skill)
        message = f"✅ Skill '{final_name}' 创建成功"

    print(f"[AI Create Skill] {message}")

    return {
        "id": skill.id,
        "name": skill.name,
        "description": skill.description,
        "message": message
    }
