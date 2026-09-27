<template>
  <div class="task-list-page">
    <van-nav-bar title="会议室智能巡检" fixed placeholder>
      <template #right>
        <div class="nav-btn-group">
          <van-button
            size="small"
            plain
            round
            icon="chart-trending-o"
            @click="goToDashboard"
          >
            大盘
          </van-button>
          <van-button
            size="small"
            type="primary"
            plain
            round
            icon="apps-o"
            @click="goToRooms"
          >
            会议室
          </van-button>
        </div>
      </template>
    </van-nav-bar>

    <!-- Notice Bar -->
    <van-notice-bar
      left-icon="volume-o"
      text="每日巡检请按规定拍摄前、后两张照片，AI将自动检测灯光、空调、显示器等指标。"
    />

    <!-- Quick Generator Bar -->
    <div class="quick-action-bar">
      <van-button
        type="default"
        size="small"
        round
        icon="bullhorn-o"
        :loading="testingNotification"
        @click="sendTestNotification"
      >
        测试群推送
      </van-button>
      <van-button
        type="primary"
        size="small"
        round
        icon="plus"
        :loading="generating"
        @click="generateTodayTask"
      >
        生成今日巡检任务
      </van-button>
    </div>

    <!-- Room Filter Chips -->
    <div class="room-filter-scroller" v-if="rooms.length > 0">
      <div
        class="filter-chip"
        :class="{ active: selectedRoomId === 0 }"
        @click="selectedRoomId = 0"
      >
        全部会议室 ({{ tasks.length }})
      </div>
      <div
        v-for="r in rooms"
        :key="r.id"
        class="filter-chip"
        :class="{ active: selectedRoomId === r.id }"
        @click="selectedRoomId = r.id"
      >
        {{ r.room_name }}
      </div>
    </div>

    <!-- Period Tabs -->
    <van-tabs v-model:active="activeTab" color="#1989fa" shrink sticky>
      <van-tab title="全部时段" name="ALL" />
      <van-tab title="上午巡检" name="MORNING" />
      <van-tab title="中午巡检" name="NOON" />
      <van-tab title="晚间巡检" name="EVENING" />
    </van-tabs>

    <!-- Task List -->
    <van-pull-refresh v-model="refreshing" @refresh="onRefresh">
      <div v-if="filteredTasks.length > 0" class="task-cards-container">
        <div
          v-for="task in filteredTasks"
          :key="task.id"
          class="task-card"
          @click="goToInspect(task.id)"
        >
          <div class="task-card-header">
            <div class="title-wrap">
              <span class="room-title">{{ roomNameMap[task.room_id] || '会议室' }}</span>
              <van-tag type="primary" plain class="code-tag">
                {{ roomCodeMap[task.room_id] || `ID:${task.room_id}` }}
              </van-tag>
            </div>
            <van-tag :type="getStatusTagType(task.status)">
              {{ getStatusLabel(task.status) }}
            </van-tag>
          </div>

          <div class="task-meta">
            <div class="meta-item location-item" v-if="roomLocMap[task.room_id]">
              <van-icon name="location-o" />
              <span>{{ roomLocMap[task.room_id] }}</span>
            </div>
            <div class="meta-item">
              <van-icon name="calendar-o" />
              <span>{{ task.inspection_date }} ({{ getPeriodLabel(task.period) }})</span>
            </div>
            <div class="meta-item">
              <van-icon name="label-o" />
              <span>编号: {{ task.task_no }}</span>
            </div>
          </div>

          <div class="task-card-footer">
            <span class="due-text" v-if="task.completed_at">已于 {{ formatTime(task.completed_at) }} 完成</span>
            <span class="due-text" v-else>点击进入巡检流程</span>
            <van-button size="small" type="primary" plain round>
              {{ task.status === 'COMPLETED' ? '查看报告' : '开始巡检' }}
            </van-button>
          </div>
        </div>
      </div>

      <van-empty v-else description="暂无符合条件的巡检任务" />
    </van-pull-refresh>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showToast, showSuccessToast, showDialog } from 'vant'
import { taskApi, roomApi, notificationApi } from '../api'
import type { InspectionTask, MeetingRoom } from '../types'

const router = useRouter()
const activeTab = ref('ALL')
const selectedRoomId = ref(0)
const tasks = ref<InspectionTask[]>([])
const rooms = ref<MeetingRoom[]>([])
const refreshing = ref(false)
const generating = ref(false)
const testingNotification = ref(false)

const sendTestNotification = async () => {
  testingNotification.value = true
  try {
    const res = await notificationApi.test()
    if (res.data.webhook_configured) {
      showSuccessToast('已成功向工作群推送测试卡片！')
    } else {
      showDialog({
        title: '未配置群 Webhook',
        message: '目前处于本地 Mock 模式（消息已打印在后台控制台）。请在后端 .env 中配置 DINGTALK_WEBHOOK_URL 后即可推送到真实群。',
        theme: 'round-button',
      })
    }
  } catch (e: any) {
    showToast('测试推送失败: ' + (e.message || '网络异常'))
  } finally {
    testingNotification.value = false
  }
}

const goToRooms = () => {
  router.push('/rooms')
}

const goToDashboard = () => {
  router.push('/dashboard')
}

const roomNameMap = computed(() => {
  const map: Record<number, string> = {}
  rooms.value.forEach((r) => {
    map[r.id] = r.room_name
  })
  return map
})

const roomCodeMap = computed(() => {
  const map: Record<number, string> = {}
  rooms.value.forEach((r) => {
    map[r.id] = r.room_code
  })
  return map
})

const roomLocMap = computed(() => {
  const map: Record<number, string> = {}
  rooms.value.forEach((r) => {
    map[r.id] = `${r.building || '大楼'} · ${r.floor || ''} ${r.location_desc ? '（' + r.location_desc + '）' : ''}`
  })
  return map
})

const filteredTasks = computed(() => {
  return tasks.value.filter((t) => {
    const matchPeriod = activeTab.value === 'ALL' || t.period === activeTab.value
    const matchRoom = selectedRoomId.value === 0 || t.room_id === selectedRoomId.value
    return matchPeriod && matchRoom
  })
})

const loadData = async () => {
  try {
    // 1. Load Rooms
    const roomRes = await roomApi.list({ status: 'ACTIVE' })
    rooms.value = roomRes.data.items || []

    // 2. Load today's generated tasks for all rooms
    const today = new Date().toISOString().split('T')[0]
    const allTasks: InspectionTask[] = []
    for (const p of ['MORNING', 'NOON', 'EVENING']) {
      try {
        const res = await taskApi.generate(today, p)
        allTasks.push(...res.data)
      } catch (e) {
        // ignore
      }
    }
    const unique = Array.from(new Map(allTasks.map((t) => [t.id, t])).values())
    unique.sort((a, b) => b.id - a.id)
    tasks.value = unique
  } catch (err: any) {
    showToast('加载巡检任务失败: ' + (err.message || '网络异常'))
  } finally {
    refreshing.value = false
  }
}

const onRefresh = async () => {
  await loadData()
}

const generateTodayTask = async () => {
  generating.value = true
  try {
    const today = new Date().toISOString().split('T')[0]
    await taskApi.generate(today, 'MORNING')
    await taskApi.generate(today, 'NOON')
    await taskApi.generate(today, 'EVENING')
    showSuccessToast('已为全部会议室生成今日任务')
    await loadData()
  } catch (e: any) {
    showToast('生成失败: ' + e.message)
  } finally {
    generating.value = false
  }
}

const goToInspect = (taskId: number) => {
  router.push({ path: '/inspect', query: { taskId } })
}

const getStatusTagType = (status: string) => {
  switch (status) {
    case 'COMPLETED':
      return 'success'
    case 'WAITING_CONFIRM':
      return 'warning'
    case 'AI_ANALYZING':
    case 'IN_PROGRESS':
      return 'primary'
    default:
      return 'default'
  }
}

const getStatusLabel = (status: string) => {
  switch (status) {
    case 'COMPLETED':
      return '已完成'
    case 'WAITING_CONFIRM':
      return '待人工核验'
    case 'AI_ANALYZING':
      return 'AI研判中'
    case 'IN_PROGRESS':
      return '巡检中'
    default:
      return '待巡检'
  }
}

const getPeriodLabel = (period: string) => {
  switch (period) {
    case 'MORNING':
      return '上午巡检'
    case 'NOON':
      return '中午巡检'
    case 'EVENING':
      return '晚间巡检'
    default:
      return period
  }
}

const formatTime = (isoString?: string) => {
  if (!isoString) return ''
  const date = new Date(isoString)
  return `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.task-list-page {
  padding-bottom: 24px;
}

.nav-btn-group {
  display: flex;
  gap: 6px;
}

.quick-action-bar {
  padding: 12px 16px 8px 16px;
  display: flex;
  justify-content: space-between;
  gap: 8px;
}

.room-filter-scroller {
  display: flex;
  overflow-x: auto;
  padding: 4px 16px 8px;
  gap: 8px;
  -webkit-overflow-scrolling: touch;
}

.room-filter-scroller::-webkit-scrollbar {
  display: none;
}

.filter-chip {
  flex-shrink: 0;
  padding: 4px 12px;
  border-radius: 14px;
  background-color: #f2f3f5;
  color: #646566;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.filter-chip.active {
  background-color: #e8f4ff;
  color: #1989fa;
  font-weight: 600;
}

.task-cards-container {
  padding: 12px 16px;
}

.task-card {
  background: #ffffff;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  border: 1px solid #ebedf0;
  transition: all 0.2s ease;
}

.task-card:active {
  background-color: #f7f8fa;
}

.task-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.title-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
}

.room-title {
  font-size: 17px;
  font-weight: 600;
  color: #323233;
}

.code-tag {
  font-size: 11px;
}

.task-meta {
  margin-bottom: 12px;
}

.location-item {
  color: #969799;
  font-size: 12px;
  margin-bottom: 6px;
}

.meta-item {
  display: flex;
  align-items: center;
  font-size: 13px;
  color: #646566;
  margin-bottom: 4px;
}

.meta-item .van-icon {
  margin-right: 6px;
  font-size: 14px;
}

.task-card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-top: 1px solid #f2f3f5;
  padding-top: 10px;
}

.due-text {
  font-size: 12px;
  color: #969799;
}
</style>
