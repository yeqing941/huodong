<script setup lang="ts">
import { onMounted, ref } from "vue";
import { ElMessage } from "element-plus";
import { request } from "../services/http";
import type { CrawlerTask } from "../types/api";

const tasks = ref<CrawlerTask[]>([]);
const configs = ref<Array<{ id: number; source: string; enabled: boolean }>>([]);
const selectedConfig = ref<number>();
async function load() {
  const [taskResponse, configResponse] = await Promise.all([request<{ items: CrawlerTask[] }>("/crawler/tasks"), request<{ items: typeof configs.value }>("/crawler/configs")]);
  tasks.value = taskResponse.data.items;
  configs.value = configResponse.data.items;
}
async function trigger() {
  if (!selectedConfig.value) return;
  try { await request(`/crawler/tasks`, { method: "POST", body: JSON.stringify({ config_id: selectedConfig.value }) }); await load(); ElMessage.success("任务已执行"); } catch (error) { ElMessage.error(error instanceof Error ? error.message : "触发失败"); }
}
onMounted(load);
</script>
<template><section><div class="page-heading"><div><h2>爬虫任务</h2><p>执行固定测试适配器并查看真实持久化统计。</p></div><div class="actions"><el-select v-model="selectedConfig" placeholder="选择启用配置" clearable><el-option v-for="item in configs.filter((x) => x.enabled)" :key="item.id" :label="item.source" :value="item.id" /></el-select><el-button type="primary" :disabled="!selectedConfig" @click="trigger">手动触发</el-button></div></div><el-table :data="tasks" stripe><el-table-column prop="id" label="任务" width="80" /><el-table-column prop="source" label="来源" /><el-table-column prop="status" label="状态" /><el-table-column prop="discovered_count" label="发现" /><el-table-column prop="new_count" label="新增" /><el-table-column prop="duplicate_count" label="重复" /><el-table-column prop="failed_count" label="失败" /><el-table-column label="操作"><template #default="{ row }"><router-link :to="`/crawler/tasks/${row.id}`">查看详情</router-link></template></el-table-column></el-table></section></template>
<style scoped>.page-heading{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:20px}.page-heading h2{margin:0 0 8px}.page-heading p{color:#6b7280}.actions{display:flex;gap:12px}</style>
