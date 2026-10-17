<script setup lang="ts">
import { computed, ref } from "vue";
import { ElMessage } from "element-plus";
import { request } from "../services/http";
import type { ReviewRecord, TagOption } from "../types/api";

const props = defineProps<{ review: ReviewRecord | null; tags: TagOption[]; visible: boolean }>();
const emit = defineEmits<{ updated: []; "update:visible": [value: boolean] }>();
const selected = ref<string[]>([]);
const note = ref("");
const busy = ref(false);
const review = computed(() => props.review);
const isAdmin = computed(() => review.value?.status === "pending_admin_review");

async function post(path: string, body: Record<string, unknown>) {
  if (!review.value) return;
  busy.value = true;
  try {
    const response = await request<ReviewRecord>(`/reviews/${review.value.id}${path}`, { method: "POST", body: JSON.stringify(body) });
    emit("updated");
    ElMessage.success("操作成功");
  } catch (error) { ElMessage.error(error instanceof Error ? error.message : "操作失败"); }
  finally { busy.value = false; }
}
function submit() { return post(isAdmin.value ? "/admin" : "/operator", isAdmin.value ? { action: "approve", tag_ids: selected.value, reason: note.value } : { action: "submit", tag_ids: selected.value, note: note.value }); }
</script>

<template>
  <el-drawer :model-value="visible" @update:model-value="emit('update:visible', $event)" title="审核详情" size="460px">
    <template v-if="review">
      <el-descriptions :column="1" border><el-descriptions-item label="状态">{{ review.status }}</el-descriptions-item><el-descriptions-item label="活动">{{ review.original_data.activity_name }}</el-descriptions-item><el-descriptions-item label="AI 失败">{{ review.ai_error || "无" }}</el-descriptions-item></el-descriptions>
      <el-form label-position="top" class="form"><el-form-item label="标签"><el-select v-model="selected" multiple style="width: 100%"><el-option v-for="tag in tags" :key="tag.id" :label="tag.name" :value="tag.id" /></el-select></el-form-item><el-form-item label="备注"><el-input v-model="note" type="textarea" /></el-form-item></el-form>
      <div class="actions"><el-button :loading="busy" @click="post(isAdmin ? '/admin' : '/operator', { action: isAdmin ? 'return' : 'cancel', reason: note })">退回/取消</el-button><el-button type="primary" :loading="busy" @click="submit">{{ isAdmin ? "确认通过" : "提交管理员审核" }}</el-button></div>
    </template>
  </el-drawer>
</template>
<style scoped>.form{margin-top:20px}.actions{display:flex;justify-content:flex-end;gap:12px;margin-top:20px}</style>
