<script setup lang="ts">
import { reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { request } from "../services/http";

const router = useRouter();
const loading = ref(false);
const form = reactive({ email: "", password: "" });

async function submit() {
  loading.value = true;
  try {
    const response = await request<{ access_token: string }>("/auth/login", {
      method: "POST",
      body: JSON.stringify(form),
    });
    localStorage.setItem("activity-reference-token", response.data.access_token);
    await router.push("/activities");
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "登录失败");
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div class="login-page">
    <el-card class="login-card">
      <h1>游戏活动参考库</h1>
      <p>登录后浏览活动素材与玩法标签</p>
      <el-form @submit.prevent="submit">
        <el-form-item label="邮箱"><el-input v-model="form.email" autocomplete="username" /></el-form-item>
        <el-form-item label="密码"><el-input v-model="form.password" type="password" show-password autocomplete="current-password" /></el-form-item>
        <el-button type="primary" native-type="submit" :loading="loading" style="width: 100%">登录</el-button>
      </el-form>
    </el-card>
  </div>
</template>

<style scoped>
.login-page { min-height: 100vh; display: grid; place-items: center; background: #eef4ff; }
.login-card { width: min(420px, calc(100% - 32px)); }
h1 { margin: 0 0 8px; }
p { color: #6b7280; margin: 0 0 24px; }
</style>
