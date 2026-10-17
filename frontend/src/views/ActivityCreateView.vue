<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { request } from "../services/http";
import type { Activity, GameTypeOption, TagOption } from "../types/api";

const router = useRouter();
const loading = ref(true);
const submitting = ref(false);
const gameTypes = ref<GameTypeOption[]>([]);
const tags = ref<TagOption[]>([]);
const form = reactive({
  source_url: "",
  source_site: "manual",
  game_name: "",
  game_type_id: "",
  activity_name: "",
  description: "",
  tag_ids: [] as string[],
  screenshot: "",
});

async function loadOptions() {
  try {
    const [gameTypeResponse, tagResponse] = await Promise.all([
      request<GameTypeOption[]>("/game-types"),
      request<TagOption[]>("/tags"),
    ]);
    gameTypes.value = gameTypeResponse.data;
    tags.value = tagResponse.data;
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "选项加载失败");
  } finally {
    loading.value = false;
  }
}

async function submit() {
  if (!form.activity_name.trim() || !form.game_name.trim() || !form.source_url.trim() || !form.game_type_id || !form.tag_ids.length || !form.screenshot.trim()) {
    ElMessage.warning("请填写活动名称、游戏名称、来源 URL、游戏类型、标签和截图路径");
    return;
  }

  submitting.value = true;
  try {
    const response = await request<Activity>("/activities", {
      method: "POST",
      body: JSON.stringify(form),
    });
    ElMessage.success("活动创建成功");
    await router.push(`/activities/${response.data.id}`);
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "活动创建失败");
  } finally {
    submitting.value = false;
  }
}

onMounted(loadOptions);
</script>

<template>
  <section v-loading="loading">
    <div class="page-heading">
      <div>
        <h2>新增活动</h2>
        <p>录入可复用的竞品活动素材和玩法信息</p>
      </div>
      <el-button @click="router.push('/activities')">返回活动库</el-button>
    </div>

    <el-card>
      <el-form label-position="top" @submit.prevent="submit">
        <el-row :gutter="16">
          <el-col :xs="24" :sm="12">
            <el-form-item label="活动名称" required><el-input v-model="form.activity_name" /></el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12">
            <el-form-item label="游戏名称" required><el-input v-model="form.game_name" /></el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12">
            <el-form-item label="游戏类型" required><el-select v-model="form.game_type_id" placeholder="请选择游戏类型" style="width: 100%"><el-option v-for="item in gameTypes" :key="item.id" :label="item.name" :value="item.id" /></el-select></el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12">
            <el-form-item label="活动标签" required><el-select v-model="form.tag_ids" multiple placeholder="请选择标签" style="width: 100%"><el-option v-for="tag in tags" :key="tag.id" :label="tag.name" :value="tag.id" /></el-select></el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12">
            <el-form-item label="来源 URL" required><el-input v-model="form.source_url" placeholder="https://..." /></el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12">
            <el-form-item label="来源站点"><el-input v-model="form.source_site" /></el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="截图路径" required><el-input v-model="form.screenshot" placeholder="例如：activities/example.png 或图片 URL" /></el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="活动说明"><el-input v-model="form.description" type="textarea" :rows="5" /></el-form-item>
          </el-col>
        </el-row>
        <div class="actions"><el-button @click="router.push('/activities')">取消</el-button><el-button type="primary" native-type="submit" :loading="submitting">创建活动</el-button></div>
      </el-form>
    </el-card>
  </section>
</template>

<style scoped>
.page-heading { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; }
h2 { margin: 0 0 8px; }
p { color: #6b7280; margin: 0; }
.actions { display: flex; justify-content: flex-end; gap: 12px; }
</style>
