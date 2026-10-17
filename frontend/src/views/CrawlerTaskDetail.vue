<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import { ElMessage } from "element-plus";
import { request } from "../services/http";
import type { CrawlerTask } from "../types/api";
const route=useRoute(); const task=ref<CrawlerTask & {failures?:Array<{id:number;url:string;reason:string;retry_count:number;status:string}>}>();
async function load(){task.value=(await request<typeof task.value>(`/crawler/tasks/${route.params.id}`)).data;}
async function retry(path:string){try{await request(path,{method:"POST"});await load();ElMessage.success("重试已完成");}catch(e){ElMessage.error(e instanceof Error?e.message:"重试失败");}}
onMounted(load);
</script>
<template><section v-if="task"><div class="page-heading"><div><h2>任务 #{{task.id}} 详情</h2><p>{{task.source}} · {{task.status}}</p></div><el-button type="primary" :disabled="!task.failed_count" @click="retry(`/crawler/tasks/${task.id}/retry`)">重试全部失败</el-button></div><el-descriptions border :column="3"><el-descriptions-item label="发现">{{task.discovered_count}}</el-descriptions-item><el-descriptions-item label="新增">{{task.new_count}}</el-descriptions-item><el-descriptions-item label="重复">{{task.duplicate_count}}</el-descriptions-item><el-descriptions-item label="失败">{{task.failed_count}}</el-descriptions-item><el-descriptions-item label="待打标">{{task.pending_tagging_count}}</el-descriptions-item></el-descriptions><h3>失败记录</h3><el-table :data="task.failures || []"><el-table-column prop="url" label="URL"/><el-table-column prop="reason" label="原因"/><el-table-column prop="retry_count" label="重试次数"/><el-table-column prop="status" label="状态"/><el-table-column label="操作"><template #default="{row}"><el-button text type="primary" :disabled="row.status==='resolved'" @click="retry(`/crawler/tasks/${task.id}/failures/${row.id}/retry`)">重试</el-button></template></el-table-column></el-table></section></template>
<style scoped>.page-heading{display:flex;justify-content:space-between;margin-bottom:20px}.page-heading h2{margin:0 0 8px}.page-heading p{color:#6b7280}h3{margin-top:24px}</style>
