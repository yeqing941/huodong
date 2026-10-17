<script setup lang="ts">
import { computed, ref } from "vue";
import { useRoute } from "vue-router";

const route = useRoute();
const isPlaceholder = computed(() => Boolean(route.meta.placeholder));
const keyword = ref("");
const selectedType = ref("");
const selectedTag = ref("");
</script>

<template>
  <section v-if="isPlaceholder">
    <el-result icon="info" title="功能开发中" sub-title="该模块已预留路由，当前阶段暂未实现业务操作。" />
  </section>
  <section v-else>
    <div class="page-heading"><div><h2>{{ route.name === "favorites" ? "我的收藏" : "活动库" }}</h2><p>按活动形式、游戏类型和游戏名称快速定位参考素材</p></div><el-button type="primary">新增活动</el-button></div>
    <el-card class="filters" shadow="never">
      <el-input v-model="keyword" placeholder="搜索活动或游戏名称" clearable />
      <el-select v-model="selectedType" placeholder="游戏类型" clearable><el-option label="RPG" value="RPG" /><el-option label="策略" value="策略" /></el-select>
      <el-select v-model="selectedTag" placeholder="活动形式" clearable><el-option label="签到" value="签到" /><el-option label="抽奖" value="抽奖" /></el-select>
      <el-button>清空筛选</el-button>
    </el-card>
    <el-empty description="暂无活动数据，请先完成登录和活动入库配置" />
  </section>
</template>

<style scoped>
.page-heading { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; }
h2 { margin: 0 0 8px; }
p { color: #6b7280; margin: 0; }
.filters { display: flex; gap: 12px; margin-bottom: 24px; }
.filters .el-input { max-width: 280px; }
.filters .el-select { width: 160px; }
</style>
