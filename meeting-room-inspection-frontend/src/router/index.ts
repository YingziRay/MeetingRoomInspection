import { createRouter, createWebHashHistory } from 'vue-router'
import TaskList from '../views/TaskList.vue'
import InspectionFlow from '../views/InspectionFlow.vue'

const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    {
      path: '/',
      name: 'TaskList',
      component: TaskList,
      meta: { title: '巡检任务列表' },
    },
    {
      path: '/inspect',
      name: 'InspectionFlow',
      component: InspectionFlow,
      meta: { title: '会议室智能巡检' },
    },
  ],
})

router.beforeEach((to, _from, next) => {
  if (to.meta.title) {
    document.title = to.meta.title as string
  }
  next()
})

export default router
