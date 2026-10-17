<script setup lang="ts">
import { computed } from "vue";
import { useRoute, useRouter } from "vue-router";

const route = useRoute();
const router = useRouter();
const activePath = computed(() => route.path);
const menu = [
  { path: "/activities", label: "活动库" },
  { path: "/favorites", label: "我的收藏" },
  { path: "/crawler", label: "爬虫任务" },
  { path: "/reviews", label: "AI 审核" },
  { path: "/settings", label: "系统设置" },
];

function logout() {
  localStorage.removeItem("activity-reference-token");
  router.push("/login");
}
</script>

<template>
  <el-container class="shell">
    <el-aside width="220px" class="sidebar">
      <div class="brand">活动参考库</div>
      <el-menu :default-active="activePath" router>
        <el-menu-item v-for="item in menu" :key="item.path" :index="item.path">{{ item.label }}</el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="header">
        <div>竞品活动素材与玩法知识库</div>
        <el-button text @click="logout">退出登录</el-button>
      </el-header>
      <el-main class="main"><router-view /></el-main>
    </el-container>
  </el-container>
</template>

<style scoped>
.shell { min-height: 100vh; }
.sidebar { background: #fff; border-right: 1px solid #e5e7eb; }
.brand { padding: 24px 20px; font-size: 20px; font-weight: 700; color: #2563eb; }
.header { display: flex; align-items: center; justify-content: space-between; background: #fff; border-bottom: 1px solid #e5e7eb; }
.main { padding: 24px; }
</style>
