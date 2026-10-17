<script setup lang="ts">
import { computed, ref } from "vue";
import { ElMessage } from "element-plus";
import { request } from "../services/http";
import type { TagOption } from "../types/api";

const props = defineProps<{ tags: TagOption[] }>();
const emit = defineEmits<{ changed: [] }>();
const name = ref("");
const parentId = ref("");
const level = computed(() => (parentId.value ? Number(props.tags.find((tag) => tag.id === parentId.value)?.level ?? 0) + 1 : 1));

async function addTag() {
  try {
    await request<TagOption>("/taxonomy/tags", { method: "POST", body: JSON.stringify({ name: name.value, parent_id: parentId.value || null, level: level.value }) });
    name.value = "";
    parentId.value = "";
    emit("changed");
    ElMessage.success("标签已新增");
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "标签新增失败");
  }
}

async function disable(tag: TagOption) {
  try {
    await request(`/taxonomy/tags/${tag.id}/disable`, { method: "POST" });
    emit("changed");
    ElMessage.success("标签已停用");
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "标签停用失败");
  }
}
</script>

<template>
  <el-card shadow="never">
    <template #header>标签树</template>
    <div class="editor-row">
      <el-input v-model="name" placeholder="标签名称" />
      <el-select v-model="parentId" clearable placeholder="一级标签（可选）">
        <el-option v-for="tag in props.tags.filter((item) => item.level < 3 && item.is_active !== false)" :key="tag.id" :label="`${'　'.repeat(tag.level - 1)}${tag.name}`" :value="tag.id" />
      </el-select>
      <el-button type="primary" :disabled="!name" @click="addTag">新增标签</el-button>
    </div>
    <el-tree :data="props.tags.filter((tag) => !tag.parent_id)" node-key="id" :props="{ label: 'name', children: 'children' }">
      <template #default="{ data }"><span>{{ data.name }}</span><el-button v-if="data.is_active !== false" text type="danger" @click="disable(data)">停用</el-button></template>
    </el-tree>
  </el-card>
</template>

<style scoped>.editor-row { display: flex; gap: 12px; margin-bottom: 18px; }.editor-row .el-input { max-width: 240px; }.editor-row .el-select { width: 220px; }</style>
