<template>
  <div class="articles-page">
    <h2>内容审核</h2>
    <el-tabs v-model="tab" @tab-change="fetchArticles">
      <el-tab-pane label="待审核" name="pending" />
      <el-tab-pane label="已通过" name="approved" />
      <el-tab-pane label="已驳回" name="rejected" />
    </el-tabs>

    <el-table :data="articles" stripe v-loading="loading">
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="title" label="标题" min-width="240" show-overflow-tooltip />
      <el-table-column prop="platform_id" label="平台" width="80" />
      <el-table-column prop="read_count" label="阅读量" width="100" />
      <el-table-column prop="like_count" label="点赞" width="80" />
      <el-table-column prop="status" label="状态" width="80">
        <template #default="{ row }">
          <el-tag :type="statusType(row.status)" size="small">{{ row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200">
        <template #default="{ row }">
          <el-button v-if="row.status === 'pending'" type="success" link size="small"
            @click="audit(row.id, 'approved')">通过</el-button>
          <el-button v-if="row.status === 'pending'" type="danger" link size="small"
            @click="audit(row.id, 'rejected')">驳回</el-button>
          <el-button type="primary" link size="small" @click="openSource(row.source_url)">
            查看原文
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      v-model:current-page="page" :page-size="20"
      :total="total" layout="prev, pager, next" @current-change="fetchArticles"
      style="margin-top: 16px; justify-content: center"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { ElMessage } from "element-plus";

const tab = ref("pending");
const page = ref(1);
const total = ref(0);
const articles = ref<any[]>([]);
const loading = ref(false);

function statusType(s: string) { return s === "approved" ? "success" : s === "rejected" ? "danger" : "warning"; }

async function fetchArticles() {
  loading.value = true;
  try {
    const res = await fetch(
      `/api/v1/admin/articles?status=${tab.value}&page=${page.value}&page_size=20`,
      { headers: { Authorization: `Bearer ${localStorage.getItem("trendscope_access_token")}` } }
    );
    const data = await res.json();
    if (data.code === 0) { articles.value = data.data.items; total.value = data.pagination?.total || 0; }
  } finally { loading.value = false; }
}

async function audit(id: number, status: string) {
  try {
    const res = await fetch(`/api/v1/admin/articles/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${localStorage.getItem("trendscope_access_token")}` },
      body: JSON.stringify({ status }),
    });
    if ((await res.json()).code === 0) { ElMessage.success("审核完成"); fetchArticles(); }
  } catch { ElMessage.error("审核失败"); }
}

function openSource(url: string) { if (url) window.open(url, "_blank"); }

onMounted(fetchArticles);
</script>
