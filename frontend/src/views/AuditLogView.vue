<script setup lang="ts">
import { onMounted, ref } from "vue";
import { ElMessage } from "element-plus";
import { request } from "../services/http";

type AuditItem = { id: string; actor_email: string | null; action: string; object_type: string; object_id: string; success: boolean; before_data: Record<string, unknown>; after_data: Record<string, unknown>; note: string; created_at: string };
const items = ref<AuditItem[]>([]); const action = ref(""); const objectType = ref("");
async function load() { try { items.value = (await request<{ items: AuditItem[] }>(`/audit-logs?action=${encodeURIComponent(action.value)}&object_type=${encodeURIComponent(objectType.value)}`)).data.items; } catch (error) { ElMessage.error(error instanceof Error ? error.message : "审计日志加载失败"); } }
onMounted(load);
</script>
<template>
  <section><div class="page-heading"><h2>审计日志</h2><p>查询关键操作的操作者、结果及变更前后数据。</p></div><div class="filters"><el-input v-model="action" placeholder="动作" /><el-input v-model="objectType" placeholder="对象类型" /><el-button type="primary" @click="load">查询</el-button></div><el-table :data="items"><el-table-column prop="created_at" label="时间" width="190" /><el-table-column prop="actor_email" label="操作者" /><el-table-column prop="action" label="动作" /><el-table-column prop="object_type" label="对象类型" /><el-table-column prop="object_id" label="对象 ID" /><el-table-column label="结果"><template #default="{ row }"><el-tag :type="row.success ? 'success' : 'danger'">{{ row.success ? "成功" : "失败" }}</el-tag></template></el-table-column><el-table-column prop="note" label="备注" /></el-table></section>
</template>
<style scoped>.page-heading { margin-bottom: 20px; }.page-heading h2 { margin: 0 0 8px; }.page-heading p { color: #6b7280; }.filters { display: flex; gap: 12px; margin-bottom: 18px; }.filters .el-input { max-width: 220px; }</style>
