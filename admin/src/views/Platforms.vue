<template>
  <div class="platforms-page">
    <h2>平台管理</h2>
    <el-table :data="platforms" stripe v-loading="loading">
      <el-table-column prop="code" label="代码" width="120" />
      <el-table-column prop="name" label="名称" width="120" />
      <el-table-column prop="category" label="分类" width="100" />
      <el-table-column prop="crawl_interval" label="采集间隔(s)" width="120" />
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">
            {{ row.is_active ? '启用' : '禁用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="160">
        <template #default="{ row }">
          <el-button type="primary" link size="small" @click="editPlatform(row)">
            编辑
          </el-button>
          <el-button type="primary" link size="small" @click="triggerCrawl(row)">
            手动抓取
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 编辑弹窗 -->
    <el-dialog v-model="editVisible" title="编辑平台配置" width="500px">
      <el-form :model="editForm" label-width="100px">
        <el-form-item label="采集间隔(s)">
          <el-input-number v-model="editForm.crawl_interval" :min="30" :max="86400" />
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="editForm.is_active" active-text="启用" inactive-text="禁用" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editVisible = false">取消</el-button>
        <el-button type="primary" @click="savePlatform">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { ElMessage } from "element-plus";

interface Platform {
  id: number;
  code: string;
  name: string;
  category: string;
  crawl_interval: number;
  is_active: boolean;
}

const platforms = ref<Platform[]>([]);
const loading = ref(false);
const editVisible = ref(false);
const editForm = ref({ id: 0, crawl_interval: 300, is_active: true });

async function fetchPlatforms() {
  loading.value = true;
  try {
    const res = await fetch("/api/v1/admin/platforms", {
      headers: { Authorization: `Bearer ${localStorage.getItem("trendscope_access_token")}` },
    });
    const data = await res.json();
    if (data.code === 0) {
      platforms.value = data.data.platforms;
    }
  } finally {
    loading.value = false;
  }
}

function editPlatform(row: Platform) {
  editForm.value = { id: row.id, crawl_interval: row.crawl_interval, is_active: row.is_active };
  editVisible.value = true;
}

async function savePlatform() {
  try {
    await fetch(`/api/v1/admin/platforms/${editForm.value.id}`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${localStorage.getItem("trendscope_access_token")}`,
      },
      body: JSON.stringify(editForm.value),
    });
    ElMessage.success("保存成功");
    editVisible.value = false;
    fetchPlatforms();
  } catch {
    ElMessage.error("保存失败");
  }
}

async function triggerCrawl(row: Platform) {
  try {
    const res = await fetch("/api/v1/admin/crawl/trigger", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${localStorage.getItem("trendscope_access_token")}`,
      },
      body: JSON.stringify({ platform_id: row.id, force: false }),
    });
    const data = await res.json();
    if (data.code === 0) ElMessage.success(`已触发 ${row.name} 采集`);
  } catch {
    ElMessage.error("触发失败");
  }
}

onMounted(fetchPlatforms);
</script>
