import { createRouter, createWebHistory } from "vue-router";
import AppLayout from "../layouts/AppLayout.vue";
import ActivityEntryView from "../views/ActivityEntryView.vue";
import ActivityDetailView from "../views/ActivityDetailView.vue";
import ActivityLibraryView from "../views/ActivityLibraryView.vue";
import LoginView from "../views/LoginView.vue";
import TagManagementView from "../views/TagManagementView.vue";
import CrawlerTaskView from "../views/CrawlerTaskView.vue";
import CrawlerConfigView from "../views/CrawlerConfigView.vue";
import CrawlerTaskDetail from "../views/CrawlerTaskDetail.vue";
import AIReviewView from "../views/AIReviewView.vue";

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
        { path: "activities/new", name: "activity-create", component: ActivityEntryView, meta: { roles: ["operator", "admin"] } },
        { path: "activities/:id/edit", name: "activity-edit", component: ActivityEntryView, meta: { roles: ["operator", "admin"] } },
        { path: "activities/:id", name: "activity-detail", component: ActivityDetailView, meta: { roles: ["user", "operator", "admin"] } },
        { path: "favorites", name: "favorites", component: ActivityLibraryView, meta: { roles: ["user", "operator", "admin"] } },
        { path: "crawler", name: "crawler", component: CrawlerTaskView, meta: { roles: ["operator", "admin"] } },
        { path: "crawler/tasks/:id", name: "crawler-task-detail", component: CrawlerTaskDetail, meta: { roles: ["operator", "admin"] } },
        { path: "reviews", name: "reviews", component: AIReviewView, meta: { roles: ["operator", "admin"] } },
        { path: "settings", name: "settings", component: TagManagementView, meta: { roles: ["admin"] } },
        { path: "crawler/settings", name: "crawler-settings", component: CrawlerConfigView, meta: { roles: ["admin"] } },
      ],
    },
  ],
});
