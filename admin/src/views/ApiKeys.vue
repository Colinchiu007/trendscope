<template>
  <div class="apikeys-page">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px">
      <h2 style="margin: 0">API Key 管理</h2>
      <el-button type="primary" @click="showCreateDialog">创建 API Key</el-button>
    </div>

    <el-table :data="keys" stripe v-loading="loading">
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="name" label="名称" width="180" />
      <el-table-column prop="key_prefix" label="Key前缀" width="160" />
      <el-table-column prop="rate_limit" label="QPM限制" width="100" />
      <el-table-column label="状态" width="80">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">
            {{ row.is_active ? '活跃' : '已撤销' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="last_used_at" label="最后使用" width="180" />
      <el-table-column prop="expires_at" label="过期时间" width="180" />
      <el-table-column label="操作" width="100">
        <template #default="{ row }">
          <el-button v-if="row.is_active" type="danger" link size="small"
            @click="revoke(row.id)">撤销</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 创建弹窗 -->
    <el-dialog v-model="createVisible" title="创建 API Key" width="480px" @closed="newKey = null">
      <el-form :model="createForm" label-width="100px">
        <el-form-item label="用户ID" required>
          <el-input-number v-model="createForm.user_id" :min="1" />
        </el-form-item>
        <el-form-item label="名称" required>
          <el-input v-model="createForm.name" placeholder="如: 数据分析平台对接" />
        </el-form-item>
        <el-form-item label="QPM限制">
          <el-input-number v-model="createForm.rate_limit" :min="10" :max="10000" />
        </el-form-item>
        <el-form-item label="有效天数">
          <el-input-number v-model="createForm.expires_days" :min="1" :max="3650" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createVisible = false">取消</el-button>
        <el-button type="primary" @click="createKey" :loading="creating">创建</el-button>
      </template>
    </el-dialog>

    <!-- 创建结果显示 -->
    <el-dialog v-model="newKey" title="API Key 创建成功" width="520px">
      <el-alert type="warning" :closable="false" style="margin-bottom: 12px">
        请立即复制并安全保存此 Key，关闭后将无法再次查看完整 Key。
      </el-alert>
      <el-input v-model="newKey" readonly>
        <template #append>
          <el-button @click="copyKey">复制</el-button>
        </template>
      </el-input>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";

const keys = ref<any[]>([]);
const loading = ref(false);
const createVisible = ref(false);
const creating = ref(false);
const newKey = ref<string | null>(null);
const createForm = ref({ user_id: 1, name: "", rate_limit: 100, expires_days: 365 });

async function fetchKeys() {
  loading.value = true;
  try {
    const res = await fetch("/api/v1/admin/apikeys", {
      headers: { Authorization: `Bearer ${localStorage.getItem("trendscope_access_token")}` },
    });
    const data = await res.json();
    if (data.code === 0) keys.value = data.data.items;
  } finally { loading.value = false; }
}

function showCreateDialog() { createVisible.value = true; }

async function createKey() {
  creating.value = true;
  try {
    const res = await fetch("/api/v1/admin/apikeys", {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${localStorage.getItem("trendscope_access_token")}` },
      body: JSON.stringify(createForm.value),
    });
    const data = await res.json();
    if (data.code === 0) {
      createVisible.value = false;
      newKey.value = data.data.key;
      fetchKeys();
    } else { ElMessage.error(data.message); }
  } catch { ElMessage.error("创建失败"); }
  finally { creating.value = false; }
}

async function revoke(id: number) {
  try {
    await ElMessageBox.confirm("撤销后该 Key 将立即失效，确认？");
    const res = await fetch(`/api/v1/admin/apikeys/${id}`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${localStorage.getItem("trendscope_access_token")}` },
    });
    if ((await res.json()).code === 0) { ElMessage.success("已撤销"); fetchKeys(); }
  } catch { /* cancelled */ }
}

function copyKey() {
  if (newKey.value) { navigator.clipboard.writeText(newKey.value); ElMessage.success("已复制"); }
}

onMounted(fetchKeys);
</script>
