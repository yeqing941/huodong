<script setup lang="ts">
import { onMounted, ref } from "vue";
import { ElMessage } from "element-plus";
import { request } from "../services/http";
import type { Role, User } from "../types/api";

const users = ref<User[]>([]);
async function load() { users.value = (await request<{ items: User[] }>("/users")).data.items; }
async function updateRole(user: User, role: Role) {
  try { await request<User>(`/users/${user.id}`, { method: "PATCH", body: JSON.stringify({ role }) }); await load(); } catch (error) { ElMessage.error(error instanceof Error ? error.message : "角色修改失败"); }
}
async function toggle(user: User) {
  try { await request<User>(`/users/${user.id}/${user.status === "active" ? "disable" : "enable"}`, { method: "POST" }); await load(); } catch (error) { ElMessage.error(error instanceof Error ? error.message : "状态修改失败"); }
}
onMounted(load);
</script>
<template>
  <section><div class="page-heading"><h2>用户管理</h2><p>管理员可调整角色并停用或启用账号。</p></div><el-table :data="users"><el-table-column prop="email" label="邮箱" /><el-table-column prop="username" label="用户名" /><el-table-column label="角色"><template #default="{ row }"><el-select :model-value="row.role" @change="(role: Role) => updateRole(row, role)"><el-option label="普通用户" value="user" /><el-option label="运营" value="operator" /><el-option label="管理员" value="admin" /></el-select></template></el-table-column><el-table-column label="状态"><template #default="{ row }"><el-tag>{{ row.status === "active" ? "启用" : "停用" }}</el-tag></template></el-table-column><el-table-column label="操作"><template #default="{ row }"><el-button text type="primary" @click="toggle(row)">{{ row.status === "active" ? "停用" : "启用" }}</el-button></template></el-table-column></el-table></section>
</template>
<style scoped>.page-heading { margin-bottom: 20px; }.page-heading h2 { margin: 0 0 8px; }.page-heading p { color: #6b7280; }</style>
