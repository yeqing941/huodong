import { createRouter, createWebHistory } from "vue-router";
import AppLayout from "../layouts/AppLayout.vue";
import ActivityCreateView from "../views/ActivityCreateView.vue";
import ActivityDetailView from "../views/ActivityDetailView.vue";
import ActivityLibraryView from "../views/ActivityLibraryView.vue";
import LoginView from "../views/LoginView.vue";

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/login", name: "login", component: LoginView },
    {
      path: "/",
      component: AppLayout,
      children: [
        { path: "", redirect: "/activities" },
        { path: "activities", name: "activities", component: ActivityLibraryView, meta: { roles: ["user", "operator", "admin"] } },
        { path: "activities/new", name: "activity-create", component: ActivityCreateView, meta: { roles: ["operator", "admin"] } },
        { path: "activities/:id", name: "activity-detail", component: ActivityDetailView, meta: { roles: ["user", "operator", "admin"] } },
        { path: "favorites", name: "favorites", component: ActivityLibraryView, meta: { roles: ["user", "operator", "admin"] } },
        { path: "crawler", name: "crawler", component: ActivityLibraryView, meta: { roles: ["operator", "admin"], placeholder: true } },
        { path: "reviews", name: "reviews", component: ActivityLibraryView, meta: { roles: ["operator", "admin"], placeholder: true } },
        { path: "settings", name: "settings", component: ActivityLibraryView, meta: { roles: ["admin"], placeholder: true } },
      ],
    },
  ],
});
