/**
 * TrendScope k6 性能压测脚本
 *
 * 用法: k6 run scripts/k6-load-test.js
 *      k6 run --vus 100 --duration 60s scripts/k6-load-test.js
 */
import http from "k6/http";
import { check, sleep, group } from "k6";

const BASE_URL = __ENV.BASE_URL || "http://localhost:8001/api/v1";

export const options = {
  stages: [
    { duration: "30s", target: 50 },   // 爬坡 50 VUs
    { duration: "60s", target: 100 },  // 稳定 100 VUs
    { duration: "60s", target: 200 },  // 爬坡 200 VUs
    { duration: "30s", target: 0 },    // 冷却
  ],
  thresholds: {
    http_req_duration: ["p(95)<500", "p(99)<1000"],  // P95<500ms, P99<1s
    http_req_failed: ["rate<0.01"],                   // 错误率<1%
  },
};

export default function () {
  group("Hot endpoints", () => {
    // 聚合热榜
    const aggRes = http.get(`${BASE_URL}/trending?page=1&page_size=20`);
    check(aggRes, { "trending agg 200": (r) => r.status === 200 });

    // 平台列表
    const platRes = http.get(`${BASE_URL}/trending/platforms`);
    check(platRes, { "platforms 200": (r) => r.status === 200 });

    sleep(1);

    // 单平台热榜
    const platforms = ["weibo", "zhihu", "baidu", "bilibili", "toutiao"];
    const plat = platforms[Math.floor(Math.random() * platforms.length)];
    const pRes = http.get(`${BASE_URL}/trending/${plat}?page=1&page_size=30`);
    check(pRes, { [`trending ${plat} 200`]: (r) => r.status === 200 });

    sleep(1);

    // 文章列表
    const artRes = http.get(`${BASE_URL}/articles?page=1&page_size=20`);
    check(artRes, { "articles 200": (r) => r.status === 200 });
  });

  sleep(2);

  group("Search", () => {
    const keywords = ["AI", "科技", "高考", "NBA", "电影"];
    const kw = keywords[Math.floor(Math.random() * keywords.length)];
    const res = http.get(`${BASE_URL}/articles/search?q=${kw}&page=1`);
    check(res, { "search 200": (r) => r.status === 200 });
  });

  sleep(3);

  group("Health", () => {
    const res = http.get("http://localhost:8001/health");
    check(res, { "health 200": (r) => r.status === 200 });
  });
}
