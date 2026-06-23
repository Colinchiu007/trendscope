"""管道联动 — 将热榜数据送入已有内容管道

当 feature_gates.yaml 中 trending_to_pipeline 开关启用时，
热榜采集完成后自动将 source_url 列表推送到 content-aggregator。
"""
import os
from datetime import datetime, timezone

import yaml
from loguru import logger


class PipelineBridge:
    """TrendScope → content-aggregator 管道桥接器"""

    def __init__(self, feature_gates_path: str = None):
        self.gates_path = feature_gates_path or os.getenv(
            "FEATURE_GATES_PATH",
            "/srv/projects/feature_gates.yaml",
        )

    def _load_gates(self) -> dict:
        """加载功能开关配置"""
        try:
            with open(self.gates_path, "r") as f:
                return yaml.safe_load(f) or {}
        except FileNotFoundError:
            logger.warning(f"[管道] 功能开关文件未找到: {self.gates_path}")
            return {}
        except Exception as e:
            logger.error(f"[管道] 加载开关失败: {e}")
            return {}

    def is_enabled(self, feature: str) -> bool:
        """检查功能是否启用"""
        gates = self._load_gates()
        features = gates.get("features", {})
        return features.get(feature, {}).get("enabled", False)

    async def push_to_pipeline(
        self,
        articles: list[dict],
        platform_code: str,
    ) -> int:
        """将热榜文章推入内容管道

        通过 HTTP 调用 content-aggregator 的采集端点。
        如果 content-aggregator 在同一进程（pip install -e），
        则可以直接函数调用，零网络开销。
        """
        if not self.is_enabled("trending_to_pipeline"):
            logger.debug(f"[管道] trending_to_pipeline 关闭，跳过推送")
            return 0

        count = 0
        # 优先尝试进程内调用
        try:
            from content_aggregator.services import fetch_and_rewrite
            for article in articles:
                source_url = article.get("source_url")
                if not source_url:
                    continue
                try:
                    await fetch_and_rewrite(
                        url=source_url,
                        style="公众号",
                        source="trendscope",
                    )
                    count += 1
                except Exception as e:
                    logger.warning(f"[管道] 推送失败: {source_url}, {e}")
        except ImportError:
            # 降级：HTTP 调用
            import httpx
            aggregator_url = os.getenv(
                "AGGREGATOR_API_URL",
                "http://localhost:8000/api/v1/content/fetch",
            )
            async with httpx.AsyncClient(timeout=30) as client:
                for article in articles:
                    source_url = article.get("source_url")
                    if not source_url:
                        continue
                    try:
                        resp = await client.post(aggregator_url, json={
                            "url": source_url,
                            "source": "trendscope",
                            "platform": platform_code,
                        })
                        if resp.status_code == 200:
                            count += 1
                    except Exception as e:
                        logger.warning(f"[管道] HTTP推送失败: {source_url}, {e}")
                        break

        if count > 0:
            logger.info(f"[管道] 推送 {count}/{len(articles)} 条到 content-aggregator")
        return count


# 单例
_bridge: PipelineBridge = None


def get_pipeline_bridge() -> PipelineBridge:
    global _bridge
    if _bridge is None:
        _bridge = PipelineBridge()
    return _bridge
