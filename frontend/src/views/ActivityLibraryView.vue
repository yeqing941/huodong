<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { request } from "../services/http";
import { session } from "../stores/session";
import type { Activity, ActivityPage } from "../types/api";

const route = useRoute();
const router = useRouter();
const canCreate = computed(() => session.user?.role === "operator" || session.user?.role === "admin");
const isPlaceholder = computed(() => Boolean(route.meta.placeholder));
const keyword = ref("");
const selectedType = ref("");
const selectedTag = ref("");
const activities = ref<Activity[]>([]);
const total = ref(0);
const loading = ref(false);

async function loadActivities() {
  if (isPlaceholder.value) return;
  loading.value = true;
  try {
    const params = new URLSearchParams();
    if (keyword.value) {
      params.set("game_name", keyword.value);
      params.set("activity_name", keyword.value);
    }
    if (selectedType.value) params.set("game_type_id", selectedType.value);
    if (selectedTag.value) params.set("tag_id", selectedTag.value);
    const endpoint = route.name === "favorites" ? "/favorites" : "/activities";
    const response = await request<ActivityPage>(`${endpoint}?${params.toString()}`);
    activities.value = response.data.items;
    total.value = response.data.total;
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "活动加载失败");
  } finally {
    loading.value = false;
  }
}

async function toggleFavorite(activity: Activity) {
  try {
    await request<never>(`/activities/${activity.id}/favorite`, { method: activity.is_favorite ? "DELETE" : "POST" });
    activity.is_favorite = !activity.is_favorite;
    if (route.name === "favorites" && !activity.is_favorite) await loadActivities();
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "收藏操作失败");
  }
}

onMounted(loadActivities);
watch([keyword, selectedType, selectedTag], loadActivities);
</script>

<template>
  <section v-if="isPlaceholder">
    <el-result icon="info" title="功能开发中" sub-title="该模块已预留路由，当前阶段暂未实现业务操作。" />
  </section>
  <section v-else>
    <div class="page-heading"><div><h2>{{ route.name === "favorites" ? "我的收藏" : "活动库" }}</h2><p>按活动形式、游戏类型和游戏名称快速定位参考素材</p></div><el-button v-if="canCreate" type="primary" @click="router.push('/activities/new')">新增活动</el-button></div>
    <el-card class="filters" shadow="never">
      <el-input v-model="keyword" placeholder="搜索活动或游戏名称" clearable />
      <el-select v-model="selectedType" placeholder="游戏类型" clearable><el-option label="RPG" value="RPG" /><el-option label="策略" value="策略" /></el-select>
      <el-select v-model="selectedTag" placeholder="活动形式" clearable><el-option label="签到" value="签到" /><el-option label="抽奖" value="抽奖" /></el-select>
      <el-button @click="keyword = ''; selectedType = ''; selectedTag = ''">清空筛选</el-button>
    </el-card>
    <el-alert v-if="!loading && total === 0" title="暂无活动数据，请先完成活动入库配置" type="info" :closable="false" />
    <el-row v-else v-loading="loading" :gutter="16">
      <el-col v-for="activity in activities" :key="activity.id" :xs="24" :sm="12" :lg="8">
        <el-card class="activity-card" shadow="hover" @click="router.push(`/activities/${activity.id}`)">
          <img v-if="activity.screenshots[0]" :src="activity.screenshots[0].url" :alt="activity.activity_name" class="cover" />
          <div class="activity-body">
            <div class="activity-title"><strong>{{ activity.activity_name }}</strong><el-button text @click.stop="toggleFavorite(activity)">{{ activity.is_favorite ? "已收藏" : "收藏" }}</el-button></div>
            <div>{{ activity.game_name }} · {{ activity.game_type.name }}</div>
            <div class="tags"><el-tag v-for="tag in activity.tags.slice(0, 2)" :key="tag.id" size="small">{{ tag.name }}</el-tag></div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </section>
</template>

<style scoped>
.page-heading { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; }
h2 { margin: 0 0 8px; }
p { color: #6b7280; margin: 0; }
.filters { display: flex; gap: 12px; margin-bottom: 24px; }
.filters .el-input { max-width: 280px; }
.filters .el-select { width: 160px; }
.activity-card { margin-bottom: 16px; }
.cover { display: block; width: 100%; height: 180px; object-fit: cover; background: #eef2f7; }
.activity-body { padding-top: 12px; }
.activity-title { display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; }
.tags { display: flex; gap: 6px; margin-top: 10px; }
</style>
