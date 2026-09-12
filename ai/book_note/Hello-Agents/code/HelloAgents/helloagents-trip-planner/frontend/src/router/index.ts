import { createRouter, createWebHistory } from "vue-router";

import HomeView from "../views/HomeView.vue";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/",
      name: "home",
      component: HomeView,
    },
    {
      path: "/result",
      name: "result",
      component: () => import("../views/ResultView.vue"),
    },
    {
      path: "/:pathMatch(.*)*",
      redirect: "/",
    },
  ],
  scrollBehavior: () => ({ top: 0 }),
});

export default router;
