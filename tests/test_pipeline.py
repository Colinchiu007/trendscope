"""管道模块单元测试"""
import os
import sys

# 将 crawler-engine 加入路径
_crawler_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "crawler-engine")
)
if _crawler_path not in sys.path:
    sys.path.insert(0, _crawler_path)

from pipeline.normalizer import parse_hot_value
from pipeline.cleaner import clean_data
from pipeline.deduplicator import deduplicate
from pipeline.classifier import classify


class TestParseHotValue:
    def test_basic_number(self):
        assert parse_hot_value("3976422") == 3976422.0

    def test_wan_unit(self):
        assert parse_hot_value("397.6万") == 3976000.0

    def test_yi_unit(self):
        assert parse_hot_value("1.2亿") == 120000000.0

    def test_plus_suffix(self):
        assert parse_hot_value("999+") == 999.0

    def test_with_comma(self):
        assert parse_hot_value("1,234,567") == 1234567.0

    def test_empty_string(self):
        assert parse_hot_value("") == 0.0

    def test_text_only(self):
        assert parse_hot_value("暂无数据") == 0.0

    def test_wan_no_decimal(self):
        assert parse_hot_value("100万") == 1000000.0

    def test_yi_no_decimal(self):
        assert parse_hot_value("3亿") == 300000000.0

    def test_weibo_real_format(self):
        assert parse_hot_value("12345678") == 12345678.0

    def test_douyin_format(self):
        assert parse_hot_value("1598.3万") == 15983000.0


class TestCleanData:
    def test_normal_items_strip_whitespace(self):
        items = [
            {"rank": 1, "title": " 高考成绩公布 ", "hot_value": "397万"},
            {"rank": 2, "title": "AI大模型新突破", "hot_value": "200万"},
        ]
        result = clean_data("weibo", items)
        assert len(result) == 2
        assert result[0]["title"] == "高考成绩公布"

    def test_empty_title_filtered(self):
        items = [
            {"rank": 1, "title": "", "hot_value": "100"},
            {"rank": 2, "title": "正常标题", "hot_value": "50"},
        ]
        result = clean_data("weibo", items)
        assert len(result) == 1
        assert result[0]["title"] == "正常标题"

    def test_whitespace_only_title_filtered(self):
        items = [
            {"rank": 1, "title": "   ", "hot_value": "100"},
            {"rank": 2, "title": "正常标题", "hot_value": "50"},
        ]
        result = clean_data("weibo", items)
        assert len(result) == 1

    def test_zero_rank_filtered(self):
        items = [
            {"rank": 0, "title": "无排名话题", "hot_value": "100"},
            {"rank": 1, "title": "正常话题", "hot_value": "50"},
        ]
        result = clean_data("weibo", items)
        assert len(result) == 1

    def test_negative_rank_filtered(self):
        items = [
            {"rank": -1, "title": "排名异常", "hot_value": "100"},
            {"rank": 1, "title": "正常", "hot_value": "50"},
        ]
        result = clean_data("weibo", items)
        assert len(result) == 1

    def test_html_tags_stripped(self):
        items = [
            {"rank": 1, "title": "<em>高考</em>成绩公布<a href='#'>查看</a>", "hot_value": "100"},
        ]
        result = clean_data("weibo", items)
        assert result[0]["title"] == "高考成绩公布查看"

    def test_empty_input(self):
        assert clean_data("weibo", []) == []


class TestDeduplicate:
    def test_exact_duplicates_removed(self):
        items = [
            {"rank": 1, "title": "相同标题", "hot_value": "100"},
            {"rank": 2, "title": "相同标题", "hot_value": "90"},
        ]
        result = deduplicate("weibo", items)
        assert len(result) == 1

    def test_similar_titles_removed(self):
        items = [
            {"rank": 1, "title": "AI大模型新突破引发全行业震动与关注", "hot_value": "100"},
            {"rank": 2, "title": "AI大模型新突破引发全行业震动", "hot_value": "90"},
        ]
        result = deduplicate("weibo", items, threshold=0.85)
        assert len(result) == 1

    def test_different_titles_preserved(self):
        items = [
            {"rank": 1, "title": "高考成绩公布", "hot_value": "100"},
            {"rank": 2, "title": "NBA总决赛第四场", "hot_value": "90"},
            {"rank": 3, "title": "央行宣布降息", "hot_value": "80"},
        ]
        result = deduplicate("weibo", items)
        assert len(result) == 3

    def test_single_item_preserved(self):
        items = [{"rank": 1, "title": "唯一话题", "hot_value": "100"}]
        result = deduplicate("weibo", items)
        assert len(result) == 1

    def test_empty_input(self):
        assert deduplicate("weibo", []) == []

    def test_first_occurrence_kept(self):
        """确保保留第一次出现的高排名条目"""
        items = [
            {"rank": 1, "title": "相同标题", "hot_value": "100万"},
            {"rank": 25, "title": "相同标题", "hot_value": "30万"},
        ]
        result = deduplicate("weibo", items)
        assert len(result) == 1
        assert result[0]["rank"] == 1
        assert result[0]["hot_value"] == "100万"


class TestClassify:
    def test_tech(self):
        assert classify("苹果秋季新品发布会") == "tech"
        assert classify("华为Mate70正式开售") == "tech"
        assert classify("GPT-5即将发布震撼业界") == "tech"
        assert classify("Claude新模型评测") == "tech"

    def test_entertainment(self):
        assert classify("新电影票房破10亿") == "entertainment"
        assert classify("明星演唱会门票秒空") == "entertainment"
        assert classify("热门游戏新赛季") == "entertainment"

    def test_social(self):
        assert classify("高考分数线正式公布") == "social"
        assert classify("房价调控新政策出台") == "social"
        assert classify("考研成绩查询入口") == "social"

    def test_finance(self):
        assert classify("A股三大指数集体上涨") == "finance"
        assert classify("央行宣布降息25个基点") == "finance"
        assert classify("比特币突破10万美元") == "finance"

    def test_sports(self):
        assert classify("NBA总决赛第四场战报") == "sports"
        assert classify("世界杯预选赛国足获胜") == "sports"
        assert classify("奥运冠军再创世界纪录") == "sports"

    def test_general_fallback(self):
        assert classify("日常生活小妙招") == "general"
        assert classify("今天天气真好适合出行") == "general"
        assert classify("一只猫走进便利店") == "general"
