<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { request } from "../services/http";
import type { Activity } from "../types/api";

const route = useRoute();
const router = useRouter();
const activity = ref<Activity | null>(null);
const loading = ref(true);
const favoriteLoading = ref(false);

async function loadActivity() {
  loading.value = true;
  try {
    const response = await request<Activity>(`/activities/${route.params.id}`);
    activity.value = response.data;
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "活动加载失败");
  } finally {
    loading.value = false;
  }
}

async function toggleFavorite() {
  if (!activity.value) return;
  favoriteLoading.value = true;
  try {
    await request<never>(`/activities/${activity.value.id}/favorite`, {
      method: activity.value.is_favorite ? "DELETE" : "POST",
    });
    activity.value.is_favorite = !activity.value.is_favorite;
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "收藏操作失败");
  } finally {
    favoriteLoading.value = false;
  }
}

function formatDate(value: string | null) {
  return value ? new Date(value).toLocaleString() : "未设置";
}

onMounted(loadActivity);
</script>

<template>
  <section v-loading="loading">
    <div class="page-heading">
      <el-button @click="router.push('/activities')">返回活动库</el-button>
      <el-button v-if="activity" type="primary" :loading="favoriteLoading" @click="toggleFavorite">
        {{ activity.is_favorite ? "取消收藏" : "收藏活动" }}
      </el-button>
    </div>

    <el-empty v-if="!loading && !activity" description="活动不存在或加载失败" />

    <template v-if="activity">
      <el-card class="hero" shadow="never">
        <div class="eyebrow">{{ activity.game_name }} · {{ activity.game_type.name }}</div>
        <h1>{{ activity.activity_name }}</h1>
        <el-tag>{{ activity.status }}</el-tag>
      </el-card>

      <el-row :gutter="16" class="content-grid">
        <el-col :xs="24" :lg="16">
          <el-card>
            <template #header>活动说明</template>
            <p class="description">{{ activity.description || "暂无活动说明" }}</p>
          </el-card>

          <el-card class="screenshots">
            <template #header>活动截图</template>
            <el-row v-if="activity.screenshots.length" :gutter="12">
              <el-col v-for="screenshot in activity.screenshots" :key="screenshot.id" :xs="24" :sm="12">
                <img :src="screenshot.url" :alt="screenshot.caption || activity.activity_name" />
                <p v-if="screenshot.caption">{{ screenshot.caption }}</p>
              </el-col>
            </el-row>
            <el-empty v-else description="暂无截图" />
          </el-card>
        </el-col>

        <el-col :xs="24" :lg="8">
          <el-card>
            <template #header>活动信息</template>
            <dl>
              <dt>开始时间</dt><dd>{{ formatDate(activity.activity_start) }}</dd>
              <dt>结束时间</dt><dd>{{ formatDate(activity.activity_end) }}</dd>
              <dt>来源站点</dt><dd>{{ activity.source_site }}</dd>
              <dt>标签</dt><dd><el-tag v-for="tag in activity.tags" :key="tag.id" class="tag">{{ tag.name }}</el-tag></dd>
            </dl>
            <el-link v-if="activity.source_url" :href="activity.source_url" target="_blank" type="primary">查看来源页面</el-link>
          </el-card>
        </el-col>
      </el-row>
    </template>
  </section>
</template>

<style scoped>
.page-heading { display: flex; justify-content: space-between; margin-bottom: 16px; }
.hero { margin-bottom: 16px; }
.eyebrow { color: #6b7280; }
h1 { margin: 8px 0 12px; }
.content-grid { margin-bottom: 16px; }
.description { white-space: pre-wrap; line-height: 1.7; }
.screenshots { margin-top: 16px; }
.screenshots img { width: 100%; height: 220px; object-fit: cover; background: #eef2f7; }
dl { margin: 0 0 16px; }
dt { color: #6b7280; margin-top: 12px; }
dd { margin: 4px 0 0; }
.tag { margin: 0 6px 6px 0; }
</style>
