<template>
  <div class="dashboard-page">
    <!-- Top Header Bar -->
    <header class="top-nav-header">
      <div class="header-left">
        <h1 class="system-title">
          <van-icon name="chart-trending-o" class="title-icon" />
          会议室巡检运营大盘 & 综合台账
        </h1>
        <span class="sub-title">全域会议室智能化质检数据留档与运维效能分析</span>
      </div>
      <div class="header-right">
        <van-button
          type="primary"
          size="small"
          round
          icon="down"
          :loading="exporting"
          @click="handleExport"
        >
          导出 Excel/CSV 台账
        </van-button>
        <van-button
          plain
          size="small"
          round
          icon="replay"
          :loading="loadingStats"
          @click="refreshAll"
        >
          刷新
        </van-button>
        <van-button
          plain
          size="small"
          round
          icon="apps-o"
          @click="router.push('/rooms')"
        >
          会议室档案
        </van-button>
        <van-button
          plain
          size="small"
          round
          icon="todo-list-o"
          @click="router.push('/')"
        >
          移动巡检端
        </van-button>
      </div>
    </header>

    <!-- Date Filter Bar -->
    <section class="date-filter-bar">
      <div class="quick-ranges">
        <span class="range-label">统计周期：</span>
        <button
          v-for="item in dateRangeOptions"
          :key="item.value"
          class="range-btn"
          :class="{ active: selectedRangeDays === item.value }"
          @click="selectDateRange(item.value)"
        >
          {{ item.label }}
        </button>
      </div>
      <div class="current-range-text">
        <van-icon name="calendar-o" />
        <span>{{ statsData?.start_date || '2026-09-12' }} 至 {{ statsData?.end_date || '2026-09-26' }}</span>
      </div>
    </section>

    <!-- 1. KPI Overview Cards -->
    <section class="kpi-grid">
      <div class="kpi-card">
        <div class="kpi-head">
          <span class="kpi-title">巡检任务总数</span>
          <van-tag type="primary" plain>执行度</van-tag>
        </div>
        <div class="kpi-val">{{ statsData?.total_tasks || 0 }}</div>
        <div class="kpi-sub">
          <span>已完成 {{ statsData?.completed_tasks || 0 }} 场</span>
          <span class="completion-rate">完成率 {{ statsData?.completion_rate || 0 }}%</span>
        </div>
        <van-progress
          :percentage="Math.min(statsData?.completion_rate || 0, 100)"
          stroke-width="4px"
          color="#1989fa"
          :show-pivot="false"
        />
      </div>

      <div class="kpi-card">
        <div class="kpi-head">
          <span class="kpi-title">综合整洁合格率</span>
          <van-tag :type="(statsData?.normal_rate || 0) >= 85 ? 'success' : 'warning'" plain>品质指标</van-tag>
        </div>
        <div class="kpi-val text-success">{{ statsData?.normal_rate || 0 }}%</div>
        <div class="kpi-sub">
          <span>全部达标 {{ statsData?.normal_tasks || 0 }} 场</span>
          <span class="text-muted">基准线: 90%</span>
        </div>
        <van-progress
          :percentage="Math.min(statsData?.normal_rate || 0, 100)"
          stroke-width="4px"
          color="#07c160"
          :show-pivot="false"
        />
      </div>

      <div class="kpi-card">
        <div class="kpi-head">
          <span class="kpi-title">异常巡检场次</span>
          <van-tag type="danger" plain>待处置</van-tag>
        </div>
        <div class="kpi-val text-danger">{{ statsData?.abnormal_tasks || 0 }}</div>
        <div class="kpi-sub">
          <span>占已完成 {{ calcAbnormalPercent }}%</span>
          <span class="text-danger">已推钉钉群告警</span>
        </div>
        <van-progress
          :percentage="Math.min(calcAbnormalPercent, 100)"
          stroke-width="4px"
          color="#ee0a24"
          :show-pivot="false"
        />
      </div>

      <div class="kpi-card">
        <div class="kpi-head">
          <span class="kpi-title">累计发现违规指标</span>
          <van-tag type="warning" plain>细分项</van-tag>
        </div>
        <div class="kpi-val text-warning">{{ statsData?.total_abnormal_items || 0 }}</div>
        <div class="kpi-sub">
          <span>涉及桌、椅、灯具等</span>
          <span class="text-muted">已留档取证</span>
        </div>
        <van-progress
          :percentage="100"
          stroke-width="4px"
          color="#ff976a"
          :show-pivot="false"
        />
      </div>
    </section>

    <!-- 2. Dual Analytics Charts -->
    <section class="charts-section">
      <!-- Left: Top Abnormal Indicators -->
      <div class="chart-card">
        <div class="card-title-bar">
          <h3>
            <van-icon name="warning-o" color="#ee0a24" />
            高频异常违规项排行榜 (Top Issues)
          </h3>
          <span class="tip-desc">按指标违规出现频次倒序排列</span>
        </div>
        <div class="indicator-rank-list" v-if="statsData?.top_abnormal_indicators?.length">
          <div
            v-for="(ind, idx) in statsData.top_abnormal_indicators"
            :key="ind.indicator_id"
            class="rank-row"
          >
            <div class="rank-index" :class="{ 'top-3': idx < 3 }">{{ idx + 1 }}</div>
            <div class="ind-info">
              <div class="ind-head">
                <span class="ind-title">{{ ind.indicator_name }}</span>
                <van-tag :type="ind.category === 'DEVICE' ? 'primary' : 'warning'" plain>
                  {{ ind.category === 'DEVICE' ? '设备设施' : '环境卫生' }}
                </van-tag>
                <span class="count-tag">{{ ind.count }} 次违规</span>
              </div>
              <div class="ind-bar-wrap">
                <div class="bar-fill" :style="{ width: `${ind.percent}%` }"></div>
                <span class="percent-label">{{ ind.percent }}%</span>
              </div>
            </div>
          </div>
        </div>
        <div v-else class="empty-chart">
          <van-icon name="passed" size="48" color="#07c160" />
          <p>统计周期内未发生指标违规记录，所有会议室保持规范整洁！</p>
        </div>
      </div>

      <!-- Right: Room Health Ranking -->
      <div class="chart-card">
        <div class="card-title-bar">
          <h3>
            <van-icon name="hotel-o" color="#1989fa" />
            会议室运维健康度分析 (Room Health)
          </h3>
          <span class="tip-desc">各会议室巡检完成度与合格率对比</span>
        </div>
        <div class="room-stats-table-wrap" v-if="statsData?.room_stats?.length">
          <table class="room-stats-table">
            <thead>
              <tr>
                <th>会议室</th>
                <th>位置</th>
                <th>巡检场次</th>
                <th>异常场次</th>
                <th>整洁合格率</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="r in statsData.room_stats" :key="r.room_id">
                <td class="font-bold">{{ r.room_name }}</td>
                <td class="text-muted">{{ r.building }} {{ r.floor }}F</td>
                <td>{{ r.completed_tasks }} / {{ r.total_tasks }}</td>
                <td>
                  <span :class="{ 'text-danger font-bold': r.abnormal_tasks > 0 }">
                    {{ r.abnormal_tasks }}
                  </span>
                </td>
                <td>
                  <van-tag :type="r.pass_rate >= 80 ? 'success' : 'danger'" plain>
                    {{ r.pass_rate }}%
                  </van-tag>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </section>

    <!-- 3. Comprehensive Historical Tasks Ledger -->
    <section class="ledger-section">
      <div class="ledger-header">
        <div class="title-wrap">
          <h2>
            <van-icon name="records-o" class="text-primary" />
            综合巡检历史电子台账 (Inspection Ledger)
          </h2>
          <span class="count-badge">共检索到 {{ ledgerTotal }} 条留档凭证</span>
        </div>
      </div>

      <!-- Filter Controls Row -->
      <div class="ledger-filter-row">
        <div class="filter-item">
          <span class="f-label">会议室：</span>
          <select v-model="filterRoomId" class="custom-select" @change="onFilterChange">
            <option :value="undefined">全部会议室</option>
            <option v-for="r in allRooms" :key="r.id" :value="r.id">
              {{ r.room_name }} ({{ r.room_code }})
            </option>
          </select>
        </div>

        <div class="filter-item">
          <span class="f-label">巡检时段：</span>
          <select v-model="filterPeriod" class="custom-select" @change="onFilterChange">
            <option :value="undefined">全部时段</option>
            <option value="MORNING">上午巡检</option>
            <option value="NOON">中午巡检</option>
            <option value="EVENING">晚间巡检</option>
          </select>
        </div>

        <div class="filter-item">
          <span class="f-label">巡检状态：</span>
          <select v-model="filterStatus" class="custom-select" @change="onFilterChange">
            <option :value="undefined">全部状态</option>
            <option value="COMPLETED">已完成</option>
            <option value="WAITING_CONFIRM">待人工核验</option>
            <option value="IN_PROGRESS">巡检中</option>
            <option value="PENDING">待巡检</option>
          </select>
        </div>

        <div class="filter-item">
          <span class="f-label">仅看异常：</span>
          <van-switch
            v-model="filterHasAbnormal"
            size="20px"
            @change="onFilterChange"
          />
        </div>

        <div class="filter-actions">
          <van-button size="small" plain @click="resetFilters">重置筛选</van-button>
        </div>
      </div>

      <!-- Table / Cards List -->
      <div class="ledger-table-container">
        <table class="ledger-table" v-if="ledgerItems.length > 0">
          <thead>
            <tr>
              <th>任务编号</th>
              <th>巡检日期 / 时段</th>
              <th>会议室</th>
              <th>状态</th>
              <th>现场实拍留档</th>
              <th>指标检测与异常清单</th>
              <th>巡检人员</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in ledgerItems" :key="item.id">
              <td class="task-no-cell font-mono">{{ item.task_no }}</td>
              <td>
                <div class="date-text font-bold">{{ item.inspection_date }}</div>
                <div class="period-text text-muted">{{ getPeriodLabel(item.period) }}</div>
              </td>
              <td>
                <div class="room-name-cell font-bold">{{ item.room_name }}</div>
                <div class="room-sub-cell text-muted">{{ item.building }} {{ item.floor }}F</div>
              </td>
              <td>
                <van-tag :type="getStatusTagType(item.status)">
                  {{ getStatusLabel(item.status) }}
                </van-tag>
              </td>
              <td>
                <div class="photo-thumbs-box">
                  <div
                    v-if="item.front_photo_url"
                    class="thumb-wrap"
                    @click="previewImage(item.front_photo_url)"
                    title="点击放大前视角原图"
                  >
                    <img :src="item.front_photo_url" class="thumb-img" alt="前视角" />
                    <span class="thumb-tag">前</span>
                  </div>
                  <div
                    v-if="item.rear_photo_url"
                    class="thumb-wrap"
                    @click="previewImage(item.rear_photo_url)"
                    title="点击放大后视角原图"
                  >
                    <img :src="item.rear_photo_url" class="thumb-img" alt="后视角" />
                    <span class="thumb-tag">后</span>
                  </div>
                  <span v-if="!item.front_photo_url && !item.rear_photo_url" class="text-muted text-xs">
                    未留档
                  </span>
                </div>
              </td>
              <td>
                <div v-if="item.abnormal_count > 0" class="abnormal-list-cell">
                  <div
                    v-for="(abn, aIdx) in item.abnormal_summary"
                    :key="aIdx"
                    class="abn-chip"
                  >
                    <span class="abn-name">🔴 {{ abn.indicator_name }}:</span>
                    <span class="abn-reason">{{ abn.reason }}</span>
                  </div>
                </div>
                <div v-else-if="item.status === 'COMPLETED'" class="all-normal-cell text-success">
                  <van-icon name="checked" />
                  <span>全部 {{ item.normal_count }} 项达标</span>
                </div>
                <div v-else class="text-muted text-xs">
                  待巡检核对
                </div>
              </td>
              <td>
                <div class="inspector-text">{{ item.inspector_id || '-' }}</div>
                <div class="completed-time text-xs text-muted" v-if="item.completed_at">
                  {{ formatDateTime(item.completed_at) }}
                </div>
              </td>
              <td>
                <van-button
                  size="small"
                  plain
                  type="primary"
                  round
                  @click="openTaskDetail(item.id)"
                >
                  详情档案
                </van-button>
              </td>
            </tr>
          </tbody>
        </table>

        <div v-else class="empty-ledger">
          <van-empty description="暂无符合条件的巡检台账记录" />
        </div>
      </div>

      <!-- Pagination -->
      <div class="pagination-bar" v-if="ledgerTotal > 0">
        <van-pagination
          v-model="currentPage"
          :total-items="ledgerTotal"
          :items-per-page="pageSize"
          mode="simple"
          @change="loadLedger"
        />
      </div>
    </section>

    <!-- 4. Detail Drawer (Task Inspection Record) -->
    <van-popup
      v-model:show="showDetailDrawer"
      position="right"
      :style="{ width: '85%', maxWidth: '640px', height: '100%' }"
    >
      <div class="detail-drawer-content" v-if="detailData">
        <div class="drawer-header">
          <div class="title-box">
            <h3>{{ detailData.room?.room_name }} · 巡检电子档案</h3>
            <span class="task-no-sub">任务编号: {{ detailData.task?.task_no }}</span>
          </div>
          <van-icon name="cross" size="20" class="close-icon" @click="showDetailDrawer = false" />
        </div>

        <div class="drawer-body">
          <!-- Room & Task Info -->
          <div class="info-block">
            <div class="info-grid">
              <div class="info-item">
                <span class="lbl">巡检日期：</span>
                <span class="val">{{ detailData.task?.inspection_date }} ({{ getPeriodLabel(detailData.task?.period) }})</span>
              </div>
              <div class="info-item">
                <span class="lbl">会议室编号：</span>
                <span class="val font-mono">{{ detailData.room?.room_code }}</span>
              </div>
              <div class="info-item">
                <span class="lbl">所在位置：</span>
                <span class="val">{{ detailData.room?.building }} · {{ detailData.room?.floor }}F</span>
              </div>
              <div class="info-item">
                <span class="lbl">任务状态：</span>
                <span class="val">
                  <van-tag :type="getStatusTagType(detailData.task?.status)">
                    {{ getStatusLabel(detailData.task?.status) }}
                  </van-tag>
                </span>
              </div>
              <div class="info-item">
                <span class="lbl">巡检人员：</span>
                <span class="val">{{ detailData.task?.inspector_id || '-' }}</span>
              </div>
              <div class="info-item">
                <span class="lbl">归档时间：</span>
                <span class="val">{{ formatDateTime(detailData.task?.completed_at) }}</span>
              </div>
            </div>
          </div>

          <!-- Photo Captures -->
          <div class="detail-section">
            <h4 class="section-title">现场实拍留档照片</h4>
            <div class="photos-row">
              <div
                v-for="photo in detailData.photos"
                :key="photo.id"
                class="detail-photo-card"
                @click="previewImage(photo.photo_url)"
              >
                <img :src="photo.photo_url" class="photo-card-img" alt="现场照片" />
                <div class="photo-info-bar">
                  <span class="p-type">{{ photo.photo_type === 'FRONT' ? '前视角 (主讲台)' : (photo.photo_type === 'AC_PANEL' ? '空调开关界面' : '后视角 (入户门)') }}</span>
                  <van-tag type="success">质检合格</van-tag>
                </div>
              </div>
            </div>
          </div>

          <!-- Indicators Check Results -->
          <div class="detail-section">
            <h4 class="section-title">指标核对与智能研判清单</h4>
            <div class="results-list">
              <div
                v-for="res in detailData.results"
                :key="res.id"
                class="result-item-card"
                :class="{ 'is-abnormal': res.final_status === 'ABNORMAL' }"
              >
                <div class="res-head">
                  <div class="ind-meta">
                    <span class="ind-name">{{ res.indicator_name }}</span>
                    <van-tag :type="res.category === 'DEVICE' ? 'primary' : 'warning'" plain>
                      {{ res.category === 'DEVICE' ? '设备' : '环境' }}
                    </van-tag>
                  </div>
                  <van-tag :type="res.final_status === 'NORMAL' ? 'success' : 'danger'">
                    {{ res.final_status === 'NORMAL' ? '正常合格' : '发现异常' }}
                  </van-tag>
                </div>

                <div class="res-body">
                  <div class="ai-opinion">
                    <span class="opinion-label">AI研判依据：</span>
                    <span class="opinion-text">{{ res.ai_reason || '正常' }}</span>
                    <span class="confidence-tag" v-if="res.ai_confidence">
                      置信度 {{ (res.ai_confidence * 100).toFixed(0) }}%
                    </span>
                  </div>
                  <div class="human-opinion" v-if="res.human_remark">
                    <span class="opinion-label">人工复核说明：</span>
                    <span class="opinion-text">{{ res.human_remark }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </van-popup>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showToast, showSuccessToast, showImagePreview } from 'vant'
import { dashboardApi, roomApi } from '../api'

const router = useRouter()

// Date ranges
const selectedRangeDays = ref(14)
const dateRangeOptions = [
  { label: '今日', value: 0 },
  { label: '近 7 天', value: 7 },
  { label: '近 14 天', value: 14 },
  { label: '近 30 天', value: 30 },
]

// Stats
const statsData = ref<any>(null)
const loadingStats = ref(false)
const exporting = ref(false)

// Rooms
const allRooms = ref<any[]>([])

// Ledger Query Filters
const currentPage = ref(1)
const pageSize = ref(15)
const filterRoomId = ref<number | undefined>(undefined)
const filterPeriod = ref<string | undefined>(undefined)
const filterStatus = ref<string | undefined>(undefined)
const filterHasAbnormal = ref(false)

const ledgerItems = ref<any[]>([])
const ledgerTotal = ref(0)

// Detail Drawer
const showDetailDrawer = ref(false)
const detailData = ref<any>(null)

// Calculate abnormal percentage
const calcAbnormalPercent = computed(() => {
  if (!statsData.value?.completed_tasks) return 0
  const rate = (statsData.value.abnormal_tasks / statsData.value.completed_tasks) * 100
  return Number(rate.toFixed(1))
})

const getDatesForRange = (days: number) => {
  const end = new Date()
  const start = new Date()
  if (days === 0) {
    // Today
    const todayStr = end.toISOString().split('T')[0]
    return { startDate: todayStr, endDate: todayStr }
  }
  start.setDate(end.getDate() - days)
  return {
    startDate: start.toISOString().split('T')[0],
    endDate: end.toISOString().split('T')[0],
  }
}

const selectDateRange = (days: number) => {
  selectedRangeDays.value = days
  loadStats()
  loadLedger()
}

const loadStats = async () => {
  loadingStats.value = true
  try {
    const { startDate, endDate } = getDatesForRange(selectedRangeDays.value)
    const res = await dashboardApi.getStats(startDate, endDate)
    statsData.value = res.data
  } catch (e: any) {
    showToast('加载统计大盘失败: ' + (e.message || '网络异常'))
  } finally {
    loadingStats.value = false
  }
}

const loadLedger = async () => {
  try {
    const { startDate, endDate } = getDatesForRange(selectedRangeDays.value)
    const res = await dashboardApi.listTasks({
      page: currentPage.value,
      page_size: pageSize.value,
      start_date: startDate,
      end_date: endDate,
      room_id: filterRoomId.value,
      period: filterPeriod.value,
      status: filterStatus.value,
      has_abnormal: filterHasAbnormal.value ? true : undefined,
    })
    ledgerItems.value = res.data.items || []
    ledgerTotal.value = res.data.total || 0
  } catch (e: any) {
    showToast('加载台账失败: ' + (e.message || '网络异常'))
  }
}

const loadRooms = async () => {
  try {
    const res = await roomApi.list({})
    allRooms.value = res.data.items || []
  } catch (e) {
    // ignore
  }
}

const onFilterChange = () => {
  currentPage.value = 1
  loadLedger()
}

const resetFilters = () => {
  filterRoomId.value = undefined
  filterPeriod.value = undefined
  filterStatus.value = undefined
  filterHasAbnormal.value = false
  currentPage.value = 1
  loadLedger()
}

const refreshAll = async () => {
  await Promise.all([loadStats(), loadLedger(), loadRooms()])
  showSuccessToast('数据已刷新')
}

const handleExport = () => {
  exporting.value = true
  try {
    const { startDate, endDate } = getDatesForRange(selectedRangeDays.value)
    const url = dashboardApi.getExportUrl({
      start_date: startDate,
      end_date: endDate,
      room_id: filterRoomId.value,
      period: filterPeriod.value,
      status: filterStatus.value,
    })
    // Trigger download via hidden anchor
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', '')
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    showSuccessToast('已生成并开始下载巡检台账')
  } catch (e: any) {
    showToast('导出失败: ' + e.message)
  } finally {
    exporting.value = false
  }
}

const previewImage = (url?: string) => {
  if (!url) return
  showImagePreview([url])
}

const openTaskDetail = async (taskId: number) => {
  try {
    showToast({ type: 'loading', message: '正在加载档案...', duration: 0 })
    const res = await dashboardApi.getTaskDetail(taskId)
    detailData.value = res.data
    showDetailDrawer.value = true
  } catch (e: any) {
    showToast('加载详情失败: ' + e.message)
  }
}

const getPeriodLabel = (period?: string) => {
  switch (period) {
    case 'MORNING':
      return '上午巡检'
    case 'NOON':
      return '中午巡检'
    case 'EVENING':
      return '晚间巡检'
    default:
      return period || '-'
  }
}

const getStatusLabel = (status?: string) => {
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

const getStatusTagType = (status?: string) => {
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

const formatDateTime = (isoString?: string) => {
  if (!isoString) return '-'
  const d = new Date(isoString)
  return `${d.getFullYear()}-${(d.getMonth() + 1).toString().padStart(2, '0')}-${d.getDate().toString().padStart(2, '0')} ${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`
}

onMounted(() => {
  loadStats()
  loadLedger()
  loadRooms()
})
</script>

<style scoped>
.dashboard-page {
  padding: 16px 20px 40px;
  background-color: #f7f8fa;
  min-height: 100vh;
}

/* Header */
.top-nav-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #ffffff;
  padding: 16px 20px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  margin-bottom: 16px;
  flex-wrap: wrap;
  gap: 12px;
}

.system-title {
  font-size: 20px;
  font-weight: 700;
  color: #323233;
  display: flex;
  align-items: center;
  gap: 8px;
}

.title-icon {
  color: #1989fa;
  font-size: 24px;
}

.sub-title {
  font-size: 13px;
  color: #969799;
  margin-top: 4px;
  display: block;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

/* Date Filter */
.date-filter-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #ffffff;
  padding: 12px 18px;
  border-radius: 10px;
  margin-bottom: 16px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.03);
  flex-wrap: wrap;
  gap: 10px;
}

.quick-ranges {
  display: flex;
  align-items: center;
  gap: 6px;
}

.range-label {
  font-size: 13px;
  color: #646566;
}

.range-btn {
  background: #f2f3f5;
  border: none;
  padding: 4px 12px;
  border-radius: 14px;
  font-size: 12px;
  color: #646566;
  cursor: pointer;
  transition: all 0.2s;
}

.range-btn.active {
  background: #e8f4ff;
  color: #1989fa;
  font-weight: 600;
}

.current-range-text {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #969799;
}

/* KPI Cards */
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 14px;
  margin-bottom: 16px;
}

.kpi-card {
  background: #ffffff;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.kpi-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.kpi-title {
  font-size: 14px;
  color: #646566;
  font-weight: 500;
}

.kpi-val {
  font-size: 30px;
  font-weight: 700;
  color: #323233;
  margin: 8px 0;
}

.kpi-sub {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  color: #969799;
  margin-bottom: 8px;
}

.completion-rate {
  color: #1989fa;
  font-weight: 600;
}

/* Charts Section */
.charts-section {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(420px, 1fr));
  gap: 16px;
  margin-bottom: 20px;
}

.chart-card {
  background: #ffffff;
  border-radius: 12px;
  padding: 18px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.card-title-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.card-title-bar h3 {
  font-size: 16px;
  font-weight: 600;
  color: #323233;
  display: flex;
  align-items: center;
  gap: 6px;
}

.tip-desc {
  font-size: 12px;
  color: #969799;
}

/* Indicator Rank */
.indicator-rank-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.rank-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.rank-index {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #f2f3f5;
  color: #646566;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
  flex-shrink: 0;
}

.rank-index.top-3 {
  background: #ffefe8;
  color: #ee0a24;
}

.ind-info {
  flex: 1;
}

.ind-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}

.ind-title {
  font-size: 14px;
  font-weight: 500;
  color: #323233;
  margin-right: 8px;
}

.count-tag {
  font-size: 12px;
  color: #ee0a24;
  font-weight: 600;
}

.ind-bar-wrap {
  width: 100%;
  height: 8px;
  background: #f2f3f5;
  border-radius: 4px;
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
}

.bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #ff976a, #ee0a24);
  border-radius: 4px;
}

.percent-label {
  position: absolute;
  right: 6px;
  font-size: 10px;
  color: #969799;
}

.empty-chart {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px 0;
  color: #969799;
  font-size: 13px;
  gap: 10px;
}

/* Room Stats Table */
.room-stats-table-wrap {
  overflow-x: auto;
}

.room-stats-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.room-stats-table th {
  background: #fafafa;
  color: #646566;
  font-weight: 600;
  text-align: left;
  padding: 10px 12px;
  border-bottom: 1px solid #ebedf0;
}

.room-stats-table td {
  padding: 10px 12px;
  border-bottom: 1px solid #f2f3f5;
  color: #323233;
}

/* Ledger Section */
.ledger-section {
  background: #ffffff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.ledger-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.ledger-header h2 {
  font-size: 18px;
  font-weight: 700;
  color: #323233;
  display: flex;
  align-items: center;
  gap: 8px;
}

.count-badge {
  font-size: 13px;
  color: #969799;
  margin-left: 10px;
}

.ledger-filter-row {
  display: flex;
  align-items: center;
  gap: 14px;
  flex-wrap: wrap;
  padding: 12px 14px;
  background: #fafafa;
  border-radius: 8px;
  margin-bottom: 16px;
}

.filter-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
}

.f-label {
  color: #646566;
}

.custom-select {
  border: 1px solid #dcdee0;
  border-radius: 6px;
  padding: 4px 8px;
  font-size: 13px;
  background: #ffffff;
  outline: none;
}

.filter-actions {
  margin-left: auto;
}

/* Ledger Table */
.ledger-table-container {
  overflow-x: auto;
}

.ledger-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.ledger-table th {
  background: #f7f8fa;
  color: #646566;
  font-weight: 600;
  text-align: left;
  padding: 12px 14px;
  border-bottom: 1px solid #ebedf0;
  white-space: nowrap;
}

.ledger-table td {
  padding: 12px 14px;
  border-bottom: 1px solid #f2f3f5;
  color: #323233;
  vertical-align: middle;
}

.task-no-cell {
  color: #1989fa;
  font-size: 12px;
}

.photo-thumbs-box {
  display: flex;
  gap: 6px;
  align-items: center;
}

.thumb-wrap {
  width: 44px;
  height: 44px;
  border-radius: 4px;
  overflow: hidden;
  position: relative;
  cursor: pointer;
  border: 1px solid #ebedf0;
}

.thumb-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.thumb-tag {
  position: absolute;
  bottom: 0;
  right: 0;
  background: rgba(0, 0, 0, 0.6);
  color: #fff;
  font-size: 9px;
  padding: 0 3px;
  border-top-left-radius: 3px;
}

.abnormal-list-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.abn-chip {
  background: #fff1f0;
  border: 1px solid #ffa39e;
  border-radius: 4px;
  padding: 2px 6px;
  font-size: 11px;
}

.abn-name {
  font-weight: 600;
  color: #cf1322;
}

.abn-reason {
  color: #434343;
  margin-left: 4px;
}

.pagination-bar {
  display: flex;
  justify-content: flex-end;
  padding-top: 16px;
}

/* Detail Drawer */
.detail-drawer-content {
  padding: 20px 24px;
  height: 100%;
  overflow-y: auto;
  box-sizing: border-box;
}

.drawer-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  border-bottom: 1px solid #ebedf0;
  padding-bottom: 14px;
  margin-bottom: 16px;
}

.title-box h3 {
  font-size: 18px;
  font-weight: 700;
  color: #323233;
}

.task-no-sub {
  font-size: 12px;
  color: #969799;
  font-family: monospace;
}

.close-icon {
  cursor: pointer;
  color: #969799;
}

.info-block {
  background: #fafafa;
  border-radius: 8px;
  padding: 12px 14px;
  margin-bottom: 18px;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 8px;
  font-size: 13px;
}

.info-item .lbl {
  color: #969799;
}

.info-item .val {
  color: #323233;
  font-weight: 500;
}

.detail-section {
  margin-bottom: 20px;
}

.section-title {
  font-size: 15px;
  font-weight: 600;
  color: #323233;
  margin-bottom: 10px;
}

.photos-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.detail-photo-card {
  border: 1px solid #ebedf0;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
}

.photo-card-img {
  width: 100%;
  height: 140px;
  object-fit: cover;
  display: block;
}

.photo-info-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 8px;
  background: #fafafa;
  font-size: 11px;
}

.results-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.result-item-card {
  border: 1px solid #ebedf0;
  border-radius: 8px;
  padding: 10px 12px;
  background: #fafafa;
}

.result-item-card.is-abnormal {
  border-color: #ffa39e;
  background: #fff1f0;
}

.res-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.ind-meta {
  display: flex;
  align-items: center;
  gap: 6px;
}

.ind-name {
  font-weight: 600;
  font-size: 14px;
}

.res-body {
  font-size: 12px;
  color: #646566;
}

.opinion-label {
  color: #969799;
}

.confidence-tag {
  color: #1989fa;
  font-size: 11px;
  margin-left: 6px;
}

/* Utility */
.font-bold {
  font-weight: 600;
}

.font-mono {
  font-family: monospace;
}

.text-success {
  color: #07c160;
}

.text-danger {
  color: #ee0a24;
}

.text-warning {
  color: #ff976a;
}

.text-muted {
  color: #969799;
}

.text-xs {
  font-size: 11px;
}
</style>
