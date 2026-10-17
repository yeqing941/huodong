<script setup lang="ts">
import { onMounted, ref } from "vue";
import { ElMessage } from "element-plus";
import { request } from "../services/http";
import { session } from "../stores/session";
import TagTreeEditor from "../components/TagTreeEditor.vue";
import type { GameTypeOption, TagOption } from "../types/api";

const tags = ref<TagOption[]>([]);
const gameTypes = ref<GameTypeOption[]>([]);
const gameTypeName = ref("");

async function load() {
  const [tagResponse, typeResponse] = await Promise.all([request<TagOption[]>("/taxonomy/tags?include_inactive=true"), request<GameTypeOption[]>("/taxonomy/game-types?include_inactive=true")]);
  tags.value = tagResponse.data;
  gameTypes.value = typeResponse.data;
}
async function addGameType() {
  try {
    await request<GameTypeOption>("/taxonomy/game-types", { method: "POST", body: JSON.stringify({ name: gameTypeName.value }) });
    gameTypeName.value = "";
    await load();
  } catch (error) { ElMessage.error(error instanceof Error ? error.message : "游戏类型新增失败"); }
}
async function disableGameType(item: GameTypeOption) {
  try { await request(`/taxonomy/game-types/${item.id}/disable`, { method: "POST" }); await load(); } catch (error) { ElMessage.error(error instanceof Error ? error.message : "游戏类型停用失败"); }
}
onMounted(load);
</script>

<template>
  <section>
    <div class="page-heading"><div><h2>分类管理</h2><p>维护标签树和游戏类型，停用仅影响新活动。</p></div></div>
    <TagTreeEditor :tags="tags" @changed="load" />
    <el-card class="types" shadow="never">
      <template #header>游戏类型</template>
      <div class="editor-row"><el-input v-model="gameTypeName" placeholder="游戏类型名称" /><el-button type="primary" :disabled="!gameTypeName" @click="addGameType">新增类型</el-button></div>
      <el-table :data="gameTypes"><el-table-column prop="name" label="名称" /><el-table-column label="状态"><template #default="{ row }"><el-tag :type="row.is_active === false ? 'info' : 'success'">{{ row.is_active === false ? '停用' : '启用' }}</el-tag></template></el-table-column><el-table-column label="操作"><template #default="{ row }"><el-button v-if="row.is_active !== false" text type="danger" @click="disableGameType(row)">停用</el-button></template></el-table-column></el-table>
    </el-card>
  </section>
</template>

<style scoped>.page-heading { margin-bottom: 20px; }.page-heading h2 { margin: 0 0 8px; }.page-heading p { color: #6b7280; }.types { margin-top: 20px; }.editor-row { display: flex; gap: 12px; margin-bottom: 18px; }.editor-row .el-input { max-width: 280px; }</style>
