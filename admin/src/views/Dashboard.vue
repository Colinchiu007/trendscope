<template>
  <div class="dashboard">
    <h2>数据面板</h2>

    <!-- 统计卡片 -->
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

    <!-- 图表行 -->
    <el-row :gutter="16">
      <el-col :span="16">
        <el-card title="访问趋势（7天）">
          <div class="chart-placeholder">
            📈 访问趋势图表（接入 ECharts 渲染）
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card title="平台分布">
          <div class="chart-placeholder">
            🥧 平台热榜数据分布
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 最近采集日志 -->
    <el-card title="最近采集日志" style="margin-top: 16px">
      <el-table :data="[]" empty-text="暂无采集记录" stripe>
        <el-table-column prop="platform" label="平台" width="120" />
        <el-table-column prop="status" label="状态" width="100" />
        <el-table-column prop="items_count" label="采集条数" width="100" />
        <el-table-column prop="duration_ms" label="耗时(ms)" width="100" />
        <el-table-column prop="created_at" label="时间" />
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";

const statCards = ref([
  { key: "platforms", label: "活跃平台", value: 12 },
  { key: "users", label: "活跃用户", value: 0 },
  { key: "articles", label: "今日文章", value: 0 },
  { key: "success_rate", label: "采集成功率", value: "0%" },
]);
</script>

<style scoped>
.stat-card { text-align: center; padding: 8px 0; }
.stat-value { font-size: 28px; font-weight: 700; color: #3b82f6; }
.stat-label { font-size: 13px; color: #999; margin-top: 4px; }
.chart-placeholder {
  height: 240px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #bbb;
  font-size: 14px;
}
</style>
