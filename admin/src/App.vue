<template>
  <div id="admin-app">
    <el-container>
      <el-header>
        <h3>热榜 TrendScope - 管理后台</h3>
        <span class="version">v0.1.0</span>
      </el-header>
      <el-container>
        <el-aside width="200px">
          <el-menu router :default-active="$route.path">
            <el-menu-item index="/dashboard">
              <span>数据面板</span>
            </el-menu-item>
            <el-menu-item index="/platforms">
              <span>平台管理</span>
            </el-menu-item>
            <el-menu-item index="/crawl">
              <span>采集调度</span>
            </el-menu-item>
            <el-menu-item index="/articles">
              <span>内容审核</span>
            </el-menu-item>
            <el-menu-item index="/users">
              <span>用户管理</span>
            </el-menu-item>
            <el-menu-item index="/apikeys">
              <span>API Key 管理</span>
            </el-menu-item>
          </el-menu>
        </el-aside>
        <el-main>
          <router-view />
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup lang="ts">
// Admin app root - integrates into existing content-aggregator Vue3 admin
</script>

<style scoped>
#admin-app { height: 100vh; }
.el-header {
  background: #fff;
  border-bottom: 1px solid #ebeef5;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
}
.el-header h3 { margin: 0; }
.version { color: #999; font-size: 12px; }
.el-aside { background: #fafafa; border-right: 1px solid #ebeef5; }
.el-main { background: #f5f5f5; padding: 24px; }
</style>
