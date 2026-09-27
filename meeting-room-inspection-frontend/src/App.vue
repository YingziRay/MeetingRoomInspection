<template>
  <div class="app-container" :class="{ 'wide-mode': route.meta.wide }">
    <router-view />
  </div>
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router'
const route = useRoute()
</script>

<style>
* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  background-color: #f7f8fa;
  font-family: -apple-system, BlinkMacSystemFont, 'Helvetica Neue', Helvetica, Segoe UI, Arial, Roboto,
    'PingFang SC', 'miui', 'Hiragino Sans GB', 'Microsoft Yahei', sans-serif;
  -webkit-font-smoothing: antialiased;
}

.app-container {
  max-width: 600px;
  margin: 0 auto;
  min-height: 100vh;
  background-color: #fff;
  position: relative;
  transition: max-width 0.2s ease;
}

.app-container.wide-mode {
  max-width: 1320px;
  background-color: #f7f8fa;
}
</style>

