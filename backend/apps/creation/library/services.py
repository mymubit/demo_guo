# -*- coding: utf-8 -*-
"""
素材库服务层。
"""
from __future__ import annotations

import logging
import uuid
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class MaterialParserService:
    """素材解析服务"""

    def parse(self, material_id: uuid.UUID) -> dict:
        """
        解析参考素材，提取结构化内容。
        支持：PDF / Word / TXT
        使用 LLM 提取：world / characters / plot_structure / themes

        返回解析后的结构化内容 dict。
        """
        from apps.creation.library.models import ReferenceMaterial

        try:
            material = ReferenceMaterial.objects.get(pk=material_id)
        except ReferenceMaterial.DoesNotExist:
            return {"error": f"素材 {material_id} 不存在"}

        if not material.file_path:
            return {"error": "素材文件路径为空"}

        # 更新状态为解析中
        material.parse_status = ReferenceMaterial.STATUS_PARSING
        material.save(update_fields=["parse_status", "updated_at"])

        try:
            # 1. 从文件提取纯文本
            text = self._extract_text_from_file(material.file_path)

            if not text or len(text) < 100:
                raise ValueError("文件内容过短或无法提取文本")

            # 2. 调用 LLM 提取结构化内容
            parsed = self._call_llm_extract(text)

            # 3. 更新素材解析内容
            material.parsed_content = parsed
            material.parse_status = ReferenceMaterial.STATUS_READY
            material.save(update_fields=["parsed_content", "parse_status", "updated_at"])

            return parsed

        except Exception as exc:
            logger.exception("[MaterialParser] 解析失败 material_id=%s", material_id)
            material.parse_status = ReferenceMaterial.STATUS_FAILED
            material.parse_error = str(exc)
            material.save(update_fields=["parse_status", "parse_error", "updated_at"])
            return {"error": str(exc)}

    def _extract_text_from_file(self, file_path: str) -> str:
        """
        从文件提取纯文本。

        支持格式：.txt / .pdf / .docx / .doc
        """
        import os

        # 文件路径安全检查
        if not file_path:
            return ""

        # 判断文件扩展名
        ext = os.path.splitext(file_path)[1].lower()

        if ext == ".txt":
            return self._extract_txt(file_path)
        elif ext in (".pdf",):
            return self._extract_pdf(file_path)
        elif ext in (".docx",):
            return self._extract_docx(file_path)
        elif ext in (".doc",):
            return self._extract_doc(file_path)
        else:
            # 尝试作为文本文件读取
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    return f.read()
            except Exception:
                return ""

    def _extract_txt(self, file_path: str) -> str:
        """读取纯文本文件。"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except UnicodeDecodeError:
            with open(file_path, "r", encoding="gbk", errors="ignore") as f:
                return f.read()

    def _extract_pdf(self, file_path: str) -> str:
        """从 PDF 提取文本。"""
        try:
            import PyPDF2

            text_parts = []
            with open(file_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
            return "\n".join(text_parts)
        except ImportError:
            logger.warning("[MaterialParser] PyPDF2 未安装，无法解析 PDF")
            return ""
        except Exception as exc:
            logger.warning("[MaterialParser] PDF 解析失败: %s", exc)
            return ""

    def _extract_docx(self, file_path: str) -> str:
        """从 Word DOCX 提取文本。"""
        try:
            from docx import Document

            doc = Document(file_path)
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            return "\n".join(paragraphs)
        except ImportError:
            logger.warning("[MaterialParser] python-docx 未安装，无法解析 DOCX")
            return ""
        except Exception as exc:
            logger.warning("[MaterialParser] DOCX 解析失败: %s", exc)
            return ""

    def _extract_doc(self, file_path: str) -> str:
        """从 Word DOC 提取文本。"""
        try:
            import subprocess

            # 使用 antiword 转换 doc 为 txt
            result = subprocess.run(
                ["antiword", file_path],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                return result.stdout
            return ""
        except FileNotFoundError:
            logger.warning("[MaterialParser] antiword 未安装，无法解析 DOC")
            return ""
        except Exception as exc:
            logger.warning("[MaterialParser] DOC 解析失败: %s", exc)
            return ""

    def _call_llm_extract(self, text: str) -> dict:
        """
        调用 LLM 提取结构化内容。

        复用现有的 LlmService。
        """
        from apps.skill.llm.chat import LlmService

        # 控制输入长度，避免超出模型上下文限制
        max_chars = 50000
        if len(text) > max_chars:
            text = text[:max_chars]

        system_prompt = """你是一个专业的故事分析师。请从文本中提取以下结构化信息：

1. **world（世界观）**：
   - setting：故事发生的背景环境
   - rules：世界的规则和限制（列表）

2. **characters（角色列表）**：
   - 每条记录包含：name（角色名）、role（角色类型/定位）、description（角色简介）

3. **plot_structure（剧情结构）**：
   - acts：各幕概览（列表）
   - twists：关键反转点（列表）

4. **themes（主题）**：
   - 故事的主要主题列表

请以 JSON 格式输出，键为 world/characters/plot_structure/themes。"""

        user_prompt = f"请分析以下文本并提取结构化内容：\n\n{text}"

        try:
            result = LlmService.generate_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.3,
                max_tokens=8192,
                json_mode=True,
            )
            return result if isinstance(result, dict) else {}
        except Exception as exc:
            logger.warning("[MaterialParser] LLM 提取失败: %s", exc)
            # 返回空结构而不是崩溃
            return {
                "world": {"setting": "", "rules": []},
                "characters": [],
                "plot_structure": {"acts": [], "twists": []},
                "themes": [],
            }


class MaterialInjectionService:
    """素材注入服务"""

    def inject_to_context(
        self,
        project: "apps.creation.models.Project",
        material_id: uuid.UUID,
        fields: List[str],
    ) -> dict:
        """
        将素材内容注入创作上下文。

        参数：
        - project: 创作项目
        - material_id: 素材 ID
        - fields: 要注入的字段列表，如 ["world", "characters"]

        返回注入后的上下文片段（供 Prompt 组装使用）。

        同时创建 ReferenceMaterialInjection 记录追踪注入历史。
        """
        from apps.creation.library.models import ReferenceMaterial, ReferenceMaterialInjection

        try:
            material = ReferenceMaterial.objects.get(pk=material_id)
        except ReferenceMaterial.DoesNotExist:
            return {"error": f"素材 {material_id} 不存在"}

        if material.parse_status != ReferenceMaterial.STATUS_READY:
            return {"error": f"素材尚未解析完成，当前状态：{material.parse_status}"}

        parsed = material.parsed_content or {}
        injected_fields = []
        context_fragment: Dict[str, Any] = {}

        for field in fields:
            if field == "world":
                world_data = parsed.get("world", {})
                context_fragment["world"] = world_data
                injected_fields.append("world")
            elif field == "characters":
                characters = parsed.get("characters", [])
                context_fragment["characters"] = characters
                injected_fields.append("characters")
            elif field == "plot_structure":
                plot = parsed.get("plot_structure", {})
                context_fragment["plot_structure"] = plot
                injected_fields.append("plot_structure")
            elif field == "themes":
                themes = parsed.get("themes", [])
                context_fragment["themes"] = themes
                injected_fields.append("themes")

        # 记录注入历史
        if injected_fields:
            ReferenceMaterialInjection.objects.create(
                project=project,
                material=material,
                injected_fields=injected_fields,
            )

        return {
            "material_id": str(material_id),
            "material_name": material.name,
            "injected_fields": injected_fields,
            "context_fragment": context_fragment,
        }
