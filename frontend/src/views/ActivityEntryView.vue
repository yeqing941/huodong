<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { request } from "../services/http";
import type { Activity, GameTypeOption, TagOption } from "../types/api";

const route = useRoute();
const router = useRouter();
const editing = Boolean(route.params.id);
const loading = ref(true);
const submitting = ref(false);
const importing = ref(false);
const gameTypes = ref<GameTypeOption[]>([]);
const tags = ref<TagOption[]>([]);
const selectedFile = ref<File | null>(null);
const batchFile = ref<File | null>(null);
const importResult = ref<{ status: string; valid_count: number; issue_count: number; issues: Array<{ row: number; message: string }> } | null>(null);
const form = reactive({
  source_url: "",
  source_site: "manual",
  game_name: "",
  game_type_id: "",
  activity_name: "",
  activity_start: "",
  activity_end: "",
  description: "",
  tag_ids: [] as string[],
});

async function load() {
  try {
    const [gameTypeResponse, tagResponse] = await Promise.all([request<GameTypeOption[]>("/game-types"), request<TagOption[]>("/tags")]);
    gameTypes.value = gameTypeResponse.data;
    tags.value = tagResponse.data;
    if (editing) {
      const response = await request<Activity>(`/activities/${route.params.id}`);
      const activity = response.data;
      Object.assign(form, {
        source_url: activity.source_url,
        source_site: activity.source_site,
        game_name: activity.game_name,
        game_type_id: activity.game_type.id,
        activity_name: activity.activity_name,
        activity_start: activity.activity_start ?? "",
        activity_end: activity.activity_end ?? "",
        description: activity.description,
        tag_ids: activity.tags.map((tag) => tag.id),
      });
    }
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "活动加载失败");
  } finally {
    loading.value = false;
  }
}

function onFileChange(event: Event) {
  selectedFile.value = (event.target as HTMLInputElement).files?.[0] ?? null;
}

function onBatchFileChange(event: Event) {
  batchFile.value = (event.target as HTMLInputElement).files?.[0] ?? null;
}

async function submit() {
  if (!form.activity_name.trim() || !form.game_name.trim() || !form.source_url.trim() || !form.game_type_id || !form.tag_ids.length || (!editing && !selectedFile.value)) {
    ElMessage.warning(editing ? "请填写必填活动字段" : "请填写必填字段并选择截图");
    return;
  }
  submitting.value = true;
  try {
    let body: BodyInit;
    if (!editing && selectedFile.value) {
      const formData = new FormData();
      Object.entries(form).forEach(([key, value]) => {
        if (Array.isArray(value)) value.forEach((item) => formData.append(key, item));
        else formData.append(key, value);
      });
      formData.append("image", selectedFile.value);
      body = formData;
    } else {
      body = JSON.stringify(form);
    }
    const response = await request<Activity>(editing ? `/activities/${route.params.id}` : "/activities", {
      method: editing ? "PATCH" : "POST",
      body,
    });
    if (editing && selectedFile.value) {
      const uploadBody = new FormData();
      uploadBody.append("image", selectedFile.value);
      await request(`/activities/${response.data.id}/screenshots`, { method: "POST", body: uploadBody });
    }
    ElMessage.success(editing ? "活动更新成功" : "活动创建成功");
    await router.push(`/activities/${response.data.id}`);
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "保存失败");
  } finally {
    submitting.value = false;
  }
}

async function importCsv() {
  if (!batchFile.value) {
    ElMessage.warning("请选择 CSV 文件");
    return;
  }
  importing.value = true;
  try {
    const body = new FormData();
    body.append("file", batchFile.value);
    const response = await request<typeof importResult.value>("/activities/import", { method: "POST", body });
    importResult.value = response.data;
    ElMessage.success("批量导入已处理");
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "批量导入失败");
  } finally {
    importing.value = false;
  }
}

onMounted(load);
</script>

<template>
  <section v-loading="loading">
    <div class="page-heading">
      <div><h2>{{ editing ? "编辑活动" : "新增活动" }}</h2><p>录入活动素材、日期和标签</p></div>
      <el-button @click="router.push('/activities')">返回活动库</el-button>
    </div>
    <el-card>
      <el-form label-position="top" @submit.prevent="submit">
        <el-row :gutter="16">
          <el-col :xs="24" :sm="12"><el-form-item label="活动名称" required><el-input v-model="form.activity_name" /></el-form-item></el-col>
          <el-col :xs="24" :sm="12"><el-form-item label="游戏名称" required><el-input v-model="form.game_name" /></el-form-item></el-col>
          <el-col :xs="24" :sm="12"><el-form-item label="游戏类型" required><el-select v-model="form.game_type_id" style="width: 100%"><el-option v-for="item in gameTypes" :key="item.id" :label="item.name" :value="item.id" /></el-select></el-form-item></el-col>
          <el-col :xs="24" :sm="12"><el-form-item label="活动标签" required><el-select v-model="form.tag_ids" multiple style="width: 100%"><el-option v-for="tag in tags" :key="tag.id" :label="tag.name" :value="tag.id" /></el-select></el-form-item></el-col>
          <el-col :xs="24" :sm="12"><el-form-item label="来源 URL" required><el-input v-model="form.source_url" /></el-form-item></el-col>
          <el-col :xs="24" :sm="12"><el-form-item label="来源站点"><el-input v-model="form.source_site" /></el-form-item></el-col>
          <el-col :xs="24" :sm="12"><el-form-item label="活动开始"><el-date-picker v-model="form.activity_start" type="date" value-format="YYYY-MM-DD" style="width: 100%" /></el-form-item></el-col>
          <el-col :xs="24" :sm="12"><el-form-item label="活动结束"><el-date-picker v-model="form.activity_end" type="date" value-format="YYYY-MM-DD" style="width: 100%" /></el-form-item></el-col>
          <el-col :span="24"><el-form-item label="截图" :required="!editing"><input type="file" accept="image/*" @change="onFileChange" /><small>{{ editing ? "可选：上传新截图，不会清空旧截图" : "请选择图片文件" }}</small></el-form-item></el-col>
          <el-col :span="24"><el-form-item label="活动说明"><el-input v-model="form.description" type="textarea" :rows="5" /></el-form-item></el-col>
        </el-row>
        <div class="actions"><el-button @click="router.push('/activities')">取消</el-button><el-button type="primary" native-type="submit" :loading="submitting">保存活动</el-button></div>
      </el-form>
    </el-card>

    <el-card class="batch-panel">
      <template #header>批量录入</template>
      <p>CSV 列：activity_name、game_name、game_type、source_url、source_site、tag、description</p>
      <input type="file" accept=".csv,text/csv" @change="onBatchFileChange" />
      <el-button type="primary" :loading="importing" @click="importCsv">上传并导入</el-button>
      <el-alert v-if="importResult" :title="`状态：${importResult.status}，有效 ${importResult.valid_count} 行，问题 ${importResult.issue_count} 行`" type="info" show-icon />
      <el-table v-if="importResult?.issues.length" :data="importResult.issues" size="small"><el-table-column prop="row" label="行号" width="90" /><el-table-column prop="message" label="问题" /></el-table>
    </el-card>
  </section>
</template>

<style scoped>
.page-heading { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; }
h2 { margin: 0 0 8px; } p, small { color: #6b7280; } .actions { display: flex; justify-content: flex-end; gap: 12px; } .batch-panel { margin-top: 20px; } .batch-panel input { margin-right: 12px; } .batch-panel .el-alert { margin-top: 16px; }
</style>
