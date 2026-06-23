"""话题自动分类模块

基于关键词匹配的简单分类器，后续可升级为 NLP 模型分类。
"""

CATEGORY_RULES = {
    "tech": ["AI", "人工智能", "大模型", "芯片", "5G", "6G", "科技", "苹果", "华为", "特斯拉", "SpaceX", "GPT", "Claude"],
    "entertainment": ["电影", "电视剧", "综艺", "明星", "演唱会", "音乐", "游戏", "直播"],
    "social": ["政策", "民生", "房价", "教育", "医疗", "高考", "考研", "结婚", "生育"],
    "finance": ["股市", "A股", "美股", "基金", "比特币", "经济", "央行", "加息", "降息"],
    "sports": ["NBA", "足球", "世界杯", "奥运会", "马拉松", "冠军", "比赛"],
}


def classify(title: str) -> str:
    """根据标题关键词进行分类"""
    for category, keywords in CATEGORY_RULES.items():
        for kw in keywords:
            if kw.lower() in title.lower():
                return category
    return "general"
