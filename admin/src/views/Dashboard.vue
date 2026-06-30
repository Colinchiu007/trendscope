<template>
  <div class="dashboard">
    <h2>数据面板</h2>

    <!-- 统计卡片（8 张） -->
    <el-row :gutter="16" style="margin-bottom: 24px">
      <el-col :span="6" v-for="card in statCards" :key="card.key">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-value">{{ card.value }}</div>
            <div class="stat-label">{{ card.label }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    <el-row :gutter="16" style="margin-bottom: 24px">
      <el-col :span="6" v-for="card in statCards2" :key="card.key">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-value">{{ card.value }}</div>
            <div class="stat-label">{{ card.label }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 图表行 -->
    <el-row :gutter="16">
      <el-col :span="16">
        <el-card>
          <template #header>访问趋势（7天）</template>
          <div ref="trendChartRef" style="height: 300px"></div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card>
          <template #header>平台分布</template>
          <div ref="pieChartRef" style="height: 300px"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 最近采集日志 -->
    <el-card style="margin-top: 16px">
      <template #header>最近采集日志</template>
      <el-table :data="crawlLogs" empty-text="暂无采集记录" stripe v-loading="loadingLogs">
        <el-table-column prop="platform_name" label="平台" width="120" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'success' ? 'success' : 'danger'" size="small">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="items_count" label="采集条数" width="100" />
        <el-table-column prop="duration_ms" label="耗时(ms)" width="100" />
        <el-table-column prop="started_at" label="时间" />
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick } from "vue"
// 注：需要 npm install echarts 后取消注释以下 import
// import * as echarts from "echarts"
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const echarts = (window as any).echarts

interface StatCard {
  key: string
  label: string
  value: string | number
}

// ── State ──
const statCards = ref<StatCard[]>([
  { key: "active_platforms", label: "活跃平台", value: "-" },
  { key: "active_users", label: "活跃用户", value: "-" },
  { key: "today_articles", label: "今日文章", value: "-" },
  { key: "today_topics", label: "今日话题", value: "-" },
])
const statCards2 = ref<StatCard[]>([
  { key: "today_api_calls", label: "API 调用", value: "-" },
  { key: "crawl_success_rate", label: "采集成功率", value: "-" },
  { key: "total_articles", label: "累计文章", value: "-" },
  { key: "total_topics", label: "累计话题", value: "-" },
])
const crawlLogs = ref<any[]>([])
const loadingLogs = ref(false)

// ── Chart refs ──
const trendChartRef = ref<HTMLElement | null>(null)
const pieChartRef = ref<HTMLElement | null>(null)
let trendChart: any = null
let pieChart: any = null

// ── Data fetching ──
async function fetchDashboard() {
  try {
    const res = await fetch("/api/v1/admin/dashboard")
    const json = await res.json()
    if (json.code !== 0) return

    const d = json.data
    const s = d.stats || {}

    statCards.value = [
      { key: "active_platforms", label: "活跃平台", value: s.active_platforms ?? "-" },
      { key: "active_users", label: "活跃用户", value: s.active_users ?? "-" },
      { key: "today_articles", label: "今日文章", value: s.today_articles ?? "-" },
      { key: "today_topics", label: "今日话题", value: s.today_topics ?? "-" },
    ]
    statCards2.value = [
      { key: "today_api_calls", label: "API 调用", value: s.today_api_calls ?? "-" },
      { key: "crawl_success_rate", label: "采集成功率", value: (s.crawl_success_rate ?? "-") + "%" },
      { key: "total_articles", label: "累计文章", value: s.total_articles ?? "-" },
      { key: "total_topics", label: "累计话题", value: s.total_topics ?? "-" },
    ]

    await nextTick()
    renderTrendChart(d.visit_trend || [])
    renderPieChart(d.platform_distribution || [])
  } catch (e) {
    console.error("仪表盘数据加载失败", e)
  }
}

async function fetchCrawlLogs() {
  loadingLogs.value = true
  try {
    const res = await fetch("/api/v1/admin/crawl/logs?page=1&page_size=10")
    const json = await res.json()
    if (json.code === 0) {
      crawlLogs.value = (json.data?.items || []).map((log: any) => ({
        ...log,
        platform_name: `#${log.platform_id}`,
      }))
    }
  } catch {
    crawlLogs.value = []
  } finally {
    loadingLogs.value = false
  }
}

// ── Charts ──
function renderTrendChart(data: Array<{ date: string; count: number }>) {
  if (!trendChartRef.value || !echarts) return
  if (!trendChart) trendChart = echarts.init(trendChartRef.value)
  trendChart.setOption({
    tooltip: { trigger: "axis" },
    grid: { left: "3%", right: "4%", bottom: "3%", containLabel: true },
    xAxis: { type: "category", data: data.map(d => d.date?.slice(5) ?? ""), boundaryGap: false },
    yAxis: { type: "value", minInterval: 1 },
    series: [{
      type: "line", smooth: true,
      data: data.map(d => d.count),
      areaStyle: { opacity: 0.25 },
      lineStyle: { width: 2 },
      itemStyle: { color: "#409eff" },
    }],
  })
}

function renderPieChart(data: Array<{ name: string; count: number }>) {
  if (!pieChartRef.value || !echarts) return
  if (!pieChart) pieChart = echarts.init(pieChartRef.value)
  pieChart.setOption({
    tooltip: { trigger: "item" },
    series: [{
      type: "pie", radius: ["30%", "60%"],
      data: data.map(d => ({ name: d.name || "-", value: d.count })),
      label: { show: true, formatter: "{b}: {c}" },
    }],
  })
}

function onResize() { trendChart?.resize(); pieChart?.resize() }

onMounted(() => {
  fetchDashboard()
  fetchCrawlLogs()
  window.addEventListener("resize", onResize)
})

onUnmounted(() => {
  window.removeEventListener("resize", onResize)
  trendChart?.dispose()
  pieChart?.dispose()
})
</script>

<style scoped>
.dashboard { max-width: 1200px; }
.stat-card { text-align: center; padding: 8px 0; }
.stat-value { font-size: 28px; font-weight: 700; color: #409eff; }
.stat-label { font-size: 13px; color: #999; margin-top: 4px; }
:deep(.el-card__header) { font-weight: 600; font-size: 14px; }
</style>
