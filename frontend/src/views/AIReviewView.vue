<script setup lang="ts">
import { onMounted, ref } from "vue";
import { ElMessage } from "element-plus";
import { request } from "../services/http";
import ReviewDrawer from "../components/ReviewDrawer.vue";
import type { ReviewRecord, TagOption } from "../types/api";

const reviews = ref<ReviewRecord[]>([]);
const tags = ref<TagOption[]>([]);
const selected = ref<ReviewRecord | null>(null);
const drawerVisible = ref(false);
const loading = ref(false);
async function load() {
  loading.value = true;
  try { const [reviewResponse, tagResponse] = await Promise.all([request<ReviewRecord[]>("/reviews"), request<TagOption[]>("/tags")]); reviews.value = reviewResponse.data; tags.value = tagResponse.data; }
  catch (error) { ElMessage.error(error instanceof Error ? error.message : "审核列表加载失败"); }
  finally { loading.value = false; }
}
function open(review: ReviewRecord) { selected.value = review; drawerVisible.value = true; }
onMounted(load);
</script>
<template>
  <section v-loading="loading"><div class="page-heading"><div><h2>AI 审核</h2><p>查看 AI 候选标签并完成运营、管理员审核。</p></div><el-button @click="load">刷新</el-button></div><el-card><el-table :data="reviews" stripe><el-table-column prop="id" label="审核 ID" width="100" /><el-table-column prop="original_data.activity_name" label="活动名称" /><el-table-column prop="status" label="状态" /><el-table-column prop="ai_error" label="AI 失败信息"><template #default="scope">{{ scope.row.ai_error || "—" }}</template></el-table-column><el-table-column label="操作" width="100"><template #default="scope"><el-button link type="primary" @click="open(scope.row)">处理</el-button></template></el-table-column></el-table></el-card><ReviewDrawer v-model:visible="drawerVisible" :review="selected" :tags="tags" @updated="load" /></section>
</template>
<style scoped>.page-heading{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:20px}h2{margin:0 0 8px}p{color:#6b7280;margin:0}</style>
