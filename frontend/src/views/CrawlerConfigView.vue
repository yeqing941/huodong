<script setup lang="ts">
import { onMounted, ref } from "vue";
import { ElMessage } from "element-plus";
import { request } from "../services/http";
import type { CrawlerConfig } from "../types/api";
const items = ref<CrawlerConfig[]>([]); const form = ref({ source: "test-adapter", rule_summary: "固定测试规则", game_scope: ["测试游戏"], cron: "0 0 * * *", enabled: true });
async function load(){ items.value=(await request<{items:CrawlerConfig[]}>("/crawler/configs")).data.items; }
async function add(){ try{ await request("/crawler/configs",{method:"POST",body:JSON.stringify(form.value)}); await load(); ElMessage.success("配置已保存"); }catch(e){ElMessage.error(e instanceof Error?e.message:"保存失败");} }
async function toggle(row:CrawlerConfig){ try{await request(`/crawler/configs/${row.id}/${row.enabled?"disable":"enable"}`,{method:"POST",body:row.enabled?JSON.stringify({reason:"管理员操作"}):undefined});await load();}catch(e){ElMessage.error(e instanceof Error?e.message:"操作失败");} }
onMounted(load);
</script>
<template><section><div class="page-heading"><div><h2>爬虫配置</h2><p>仅管理员可以维护来源、规则与调度。</p></div></div><el-card shadow="never" class="form"><el-form inline><el-form-item label="来源"><el-input v-model="form.source" /></el-form-item><el-form-item label="规则"><el-input v-model="form.rule_summary" /></el-form-item><el-form-item label="Cron"><el-input v-model="form.cron" /></el-form-item><el-form-item><el-button type="primary" @click="add">新增配置</el-button></el-form-item></el-form></el-card><el-table :data="items" stripe><el-table-column prop="source" label="来源"/><el-table-column prop="rule_summary" label="规则摘要"/><el-table-column prop="cron" label="Cron"/><el-table-column label="状态"><template #default="{row}"><el-tag :type="row.enabled?'success':'info'">{{row.auto_paused?'自动暂停':row.enabled?'启用':'停用'}}</el-tag></template></el-table-column><el-table-column label="操作"><template #default="{row}"><el-button text @click="toggle(row)">{{row.enabled?'停用':'启用'}}</el-button></template></el-table-column></el-table></section></template>
<style scoped>.page-heading{margin-bottom:20px}.page-heading h2{margin:0 0 8px}.page-heading p{color:#6b7280}.form{margin-bottom:20px}</style>
