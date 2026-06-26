<template>
  <div class="users-page">
    <h2>用户管理</h2>
    <el-table :data="users" stripe v-loading="loading">
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="username" label="用户名" width="150" />
      <el-table-column prop="email" label="邮箱" min-width="200" />
      <el-table-column prop="phone" label="手机号" width="140" />
      <el-table-column prop="role" label="角色" width="80">
        <template #default="{ row }">
          <el-tag :type="row.role === 'admin' ? 'danger' : 'info'" size="small">{{ row.role }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="80">
        <template #default="{ row }">
          <el-tag :type="row.status === 'active' ? 'success' : 'danger'" size="small">{{ row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="注册时间" width="180" />
      <el-table-column label="操作" width="160">
        <template #default="{ row }">
          <el-button v-if="row.status === 'active'" type="danger" link size="small"
            @click="updateStatus(row.id, 'banned')">封禁</el-button>
          <el-button v-else type="success" link size="small"
            @click="updateStatus(row.id, 'active')">解封</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      v-model:current-page="page" :page-size="20" :total="total"
      layout="prev, pager, next" @current-change="fetchUsers"
      style="margin-top: 16px; justify-content: center"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";

const page = ref(1);
const total = ref(0);
const users = ref<any[]>([]);
const loading = ref(false);

async function fetchUsers() {
  loading.value = true;
  try {
    const res = await fetch(
      `/api/v1/admin/users?page=${page.value}&page_size=20`,
      { headers: { Authorization: `Bearer ${localStorage.getItem("trendscope_access_token")}` } }
    );
    const data = await res.json();
    if (data.code === 0) { users.value = data.data.items; total.value = data.pagination?.total || 0; }
  } finally { loading.value = false; }
}

async function updateStatus(id: number, status: string) {
  try {
    await ElMessageBox.confirm(`确认${status === 'banned' ? '封禁' : '解封'}该用户？`);
    const res = await fetch(`/api/v1/admin/users/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${localStorage.getItem("trendscope_access_token")}` },
      body: JSON.stringify({ status }),
    });
    if ((await res.json()).code === 0) { ElMessage.success("更新成功"); fetchUsers(); }
  } catch { /* cancelled */ }
}

onMounted(fetchUsers);
</script>
