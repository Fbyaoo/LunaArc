import {
  createRouter,
  createWebHistory,
  type RouteRecordRaw,
} from 'vue-router'

import Landing from '../pages/Landing/Landing.vue'
import Home from '../pages/Home/Home.vue'

function hasToken(){

    return Boolean(
    localStorage.getItem(
    'access_token'
    )
  )

}

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'landing',
    component: Landing,
    meta: {
      requiresAuth: false,
    },
  },
  {
    path: '/home',
    name: 'home',
    component: Home,
    meta: {
      requiresAuth: true,
    },
  },

{
  path: '/reading/daily',
  name: 'reading-daily',
  component: () =>
    import('@/pages/Reading/DailyFortune.vue'),
},
{
  path: '/reading/quick',
  name: 'reading-quick',
  component: () =>
    import('@/pages/Reading/QuickQuestion.vue'),
},
{
  path: '/reading/deep',
  name: 'reading-deep',
  component: () =>
    import('@/pages/Reading/DeepReading.vue'),
},
  {
    path: '/guide',
    name: 'ai-guide',
    component: Home,
    meta: {
      requiresAuth: true,
    },
  },
  {
    path: '/history',
    name: 'reading-history',
    component: Home,
    meta: {
      requiresAuth: true,
    },
  },
  {
    path: '/history/:id',
    name: 'reading-detail',
    component: Home,
    meta: {
      requiresAuth: true,
    },
  },
  {
    path: '/saved',
    name: 'saved-readings',
    component: Home,
    meta: {
      requiresAuth: true,
    },
  },
  {
    path: '/profile',
    name: 'profile',
    component: Home,
    meta: {
      requiresAuth: true,
    },
  },
  {
    path: '/subscription',
    name: 'subscription',
    component: Home,
    meta: {
      requiresAuth: true,
    },
  },
  {
    path: '/settings',
    name: 'settings',
    component: Home,
    meta: {
      requiresAuth: true,
    },
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/',
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,

  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    }

    if (to.path !== from.path) {
      return {
        top: 0,
        behavior: 'smooth',
      }
    }

    return false
  },
})

router.beforeEach((to) => {
  const requiresAuth = Boolean(to.meta.requiresAuth)

  if (!requiresAuth) {
    return true
  }

  if (!hasToken()) {
    return {
      path: '/',
      query: {
        redirect: to.fullPath,
      },
    }
  }

  return true
})

export default router