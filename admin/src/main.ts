import { createApp } from "vue";
import { createRouter, createWebHashHistory } from "vue-router";
import ElementPlus from "element-plus";
import "element-plus/dist/index.css";
import App from "./App.vue";

// Lazy-load views
const Dashboard = () => import("./views/Dashboard.vue");
const Platforms = () => import("./views/Platforms.vue");
const Articles = () => import("./views/Articles.vue");
const Users = () => import("./views/Users.vue");
const ApiKeys = () => import("./views/ApiKeys.vue");

const routes = [
  { path: "/", redirect: "/dashboard" },
  { path: "/dashboard", component: Dashboard },
  { path: "/platforms", component: Platforms },
  { path: "/crawl", component: Dashboard },    // NOTE: 爬虫日志视图暂用 Dashboard 占位；后续可实现独立日志查看页（按平台/状态/时间筛选）
  { path: "/articles", component: Articles },
  { path: "/users", component: Users },
  { path: "/apikeys", component: ApiKeys },
];

const router = createRouter({
  history: createWebHashHistory(),
  routes,
});

const app = createApp(