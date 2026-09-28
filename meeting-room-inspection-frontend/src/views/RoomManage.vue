<template>
  <div class="room-manage-page">
    <van-nav-bar
      :title="activeMainTab === 'rooms' ? '会议室档案管理' : '巡检指标库维护'"
      left-text="返回"
      left-arrow
      fixed
      placeholder
      @click-left="goBack"
    >
      <template #right>
        <van-button
          v-if="activeMainTab === 'rooms'"
          type="primary"
          size="small"
          round
          icon="plus"
          @click="openAddDialog"
        >
          添加会议室
        </van-button>
        <van-button
          v-else
          type="primary"
          size="small"
          round
          icon="plus"
          @click="openAddIndicatorModal"
        >
          新增自定义指标
        </van-button>
      </template>
    </van-nav-bar>

    <!-- Top Main Tabs -->
    <van-tabs v-model:active="activeMainTab" color="#1989fa" line-width="40px" sticky>
      <van-tab :title="`会议室档案 (${rooms.length})`" name="rooms" />
      <van-tab :title="`巡检指标库 (${systemIndicators.length})`" name="indicators" />
    </van-tabs>

    <!-- ================= TAB 1: ROOMS ================= -->
    <div v-if="activeMainTab === 'rooms'" class="tab-content-wrap">
      <!-- Stats Bar -->
      <div class="stats-overview">
        <div class="stat-box">
          <span class="stat-num">{{ rooms.length }}</span>
          <span class="stat-label">总会议室数</span>
        </div>
        <div class="stat-box">
          <span class="stat-num text-success">{{ activeRoomsCount }}</span>
          <span class="stat-label">参与巡检中</span>
        </div>
        <div class="stat-box" @click="activeMainTab = 'indicators'">
          <span class="stat-num text-primary">{{ systemIndicators.length }}</span>
          <span class="stat-label">可用指标项 ⚙️</span>
        </div>
      </div>

      <!-- Room Cards -->
      <van-pull-refresh v-model="refreshing" @refresh="loadData">
        <div v-if="rooms.length > 0" class="room-list-container">
          <div v-for="room in rooms" :key="room.id" class="room-card">
            <div class="card-header">
              <div class="title-wrap">
                <span class="room-title">{{ room.room_name }}</span>
                <van-tag type="primary" plain class="code-tag">{{ room.room_code }}</van-tag>
              </div>
              <van-tag :type="room.inspection_enabled ? 'success' : 'default'">
                {{ room.inspection_enabled ? '巡检中' : '已暂停' }}
              </van-tag>
            </div>

            <div class="location-desc">
              <van-icon name="location-o" />
              <span>{{ room.building || '总部大楼' }} · {{ room.floor || '1F' }}</span>
              <span v-if="room.location_desc" class="desc-text">（{{ room.location_desc }}）</span>
            </div>

            <!-- Configuration Status Badges -->
            <div class="config-badges">
              <div class="badge-item" @click="openIndicatorsDialog(room)">
                <van-icon name="todo-list-o" />
                <span>已绑定 {{ roomIndicatorsMap[room.id]?.length || 0 }} 项指标</span>
                <van-icon name="arrow" class="arrow-right" />
              </div>
              <div class="badge-item" @click="openPhotosDialog(room)">
                <van-icon name="photograph" />
                <span>基准图: {{ getPhotosStatusText(room.id) }}</span>
                <van-icon name="arrow" class="arrow-right" />
              </div>
            </div>

            <!-- Card Actions -->
            <div class="card-footer">
              <div class="switch-wrap">
                <span class="switch-label">开启巡检</span>
                <van-switch
                  :model-value="room.inspection_enabled"
                  size="18px"
                  @update:model-value="(val: boolean) => toggleRoomInspection(room, val)"
                />
              </div>
              <div class="btn-group">
                <van-button size="small" plain type="primary" icon="setting-o" @click="openIndicatorsDialog(room)">
                  配置指标
                </van-button>
                <van-button size="small" plain type="success" icon="photo-o" @click="openPhotosDialog(room)">
                  基准图
                </van-button>
                <van-button size="small" plain icon="edit" @click="openEditDialog(room)">
                  编辑
                </van-button>
                <van-button size="small" plain type="danger" icon="delete-o" @click="confirmDeleteRoom(room)">
                  删除
                </van-button>
              </div>
            </div>
          </div>
        </div>
        <van-empty v-else description="暂无会议室档案，请点击右上角添加" />
      </van-pull-refresh>
    </div>

    <!-- ================= TAB 2: INDICATORS MANAGEMENT ================= -->
    <div v-else class="tab-content-wrap">
      <!-- Tip Bar -->
      <van-notice-bar
        left-icon="info-o"
        text="系统默认项（灯、空调、桌椅等）受底层保护不可删除。支持自由添加自定义指标，AI将根据填写的判定标准进行多模态研判。"
      />

      <!-- Quick Action Header -->
      <div class="indicators-tool-bar">
        <div class="filter-chips-row">
          <button
            class="chip-btn"
            :class="{ active: indicatorCategoryFilter === 'ALL' }"
            @click="indicatorCategoryFilter = 'ALL'"
          >
            全部 ({{ systemIndicators.length }})
          </button>
          <button
            class="chip-btn"
            :class="{ active: indicatorCategoryFilter === 'DEVICE' }"
            @click="indicatorCategoryFilter = 'DEVICE'"
          >
            设备类
          </button>
          <button
            class="chip-btn"
            :class="{ active: indicatorCategoryFilter === 'ENVIRONMENT' }"
            @click="indicatorCategoryFilter = 'ENVIRONMENT'"
          >
            环境类
          </button>
          <button
            class="chip-btn"
            :class="{ active: indicatorCategoryFilter === 'CUSTOM' }"
            @click="indicatorCategoryFilter = 'CUSTOM'"
          >
            自定义项 ({{ customIndicatorsCount }})
          </button>
        </div>
      </div>

      <!-- Indicators List -->
      <div class="indicators-card-list">
        <div
          v-for="ind in filteredIndicators"
          :key="ind.id"
          class="indicator-item-card"
        >
          <div class="ind-head">
            <div class="ind-left">
              <span class="ind-title">{{ ind.indicator_name }}</span>
              <van-tag :type="ind.category === 'DEVICE' ? 'primary' : 'warning'" plain>
                {{ ind.category === 'DEVICE' ? '设备设施' : '环境卫生' }}
              </van-tag>
              <van-tag type="default" plain>
                {{ ind.photo_perspective === 'REAR' ? '后视角核验' : (ind.photo_perspective === 'AC_PANEL' ? '空调面板核验' : '前视角核验') }}
              </van-tag>
              <van-tag v-if="!ind.is_custom" color="#7232dd" plain>
                <van-icon name="lock" /> 默认标准
              </van-tag>
              <van-tag v-else color="#07c160" plain>
                自定义
              </van-tag>
            </div>
            <div class="ind-right-actions">
              <template v-if="ind.is_custom">
                <van-button size="mini" plain icon="edit" @click="openEditIndicatorModal(ind)">编辑</van-button>
                <van-button size="mini" plain type="danger" icon="delete-o" @click="handleDeleteIndicator(ind)">删除</van-button>
              </template>
              <span v-else class="system-locked-text">基准保留</span>
            </div>
          </div>

          <div class="ind-criteria-box">
            <div class="criteria-row">
              <span class="c-tag green">✅ 正常：</span>
              <span class="c-desc">{{ ind.normal_condition || '无异常，符合标准规范' }}</span>
            </div>
            <div class="criteria-row">
              <span class="c-tag red">❌ 异常：</span>
              <span class="c-desc">{{ ind.abnormal_condition || '存在违规或未按要求整理' }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ================= DIALOGS ================= -->

    <!-- Dialog 1: Add / Edit Room -->
    <van-dialog
      v-model:show="showRoomDialog"
      :title="isEditing ? '编辑会议室档案' : '新建会议室'"
      show-cancel-button
      :before-close="handleSaveRoom"
    >
      <div class="dialog-form">
        <van-cell-group inset>
          <van-field
            v-model="roomForm.room_code"
            label="编号"
            placeholder="例: RM-303 / RM-VIP"
            :disabled="isEditing"
            required
          />
          <van-field
            v-model="roomForm.room_name"
            label="名称"
            placeholder="例: 303研讨室 / 董事会议室"
            required
          />
          <van-field
            v-model="roomForm.building"
            label="楼栋"
            placeholder="例: 总部研发大楼"
          />
          <van-field
            v-model="roomForm.floor"
            label="楼层"
            placeholder="例: 3F"
          />
          <van-field
            v-model="roomForm.location_desc"
            label="位置描述"
            type="textarea"
            rows="2"
            placeholder="例: 3楼西侧中型会议室，靠窗侧"
          />
          <van-cell center title="参与每日定时巡检">
            <template #right-icon>
              <van-switch v-model="roomForm.inspection_enabled" size="20" />
            </template>
          </van-cell>
        </van-cell-group>
      </div>
    </van-dialog>

    <!-- Dialog 2: Add / Edit Custom Indicator -->
    <van-dialog
      v-model:show="showIndicatorFormDialog"
      :title="isEditingIndicator ? '编辑自定义指标' : '新增自定义巡检指标'"
      show-cancel-button
      :confirm-button-text="isEditingIndicator ? '保存更新' : '立即创建'"
      :before-close="handleSaveIndicatorForm"
    >
      <div class="dialog-form">
        <van-cell-group inset>
          <van-field
            v-model="indicatorForm.indicator_name"
            label="指标名称"
            placeholder="例: 绿植盆栽 / 垃圾桶 / 门锁闭合"
            required
          />
          <van-cell center title="指标分类">
            <template #right-icon>
              <select v-model="indicatorForm.category" class="inline-select">
                <option value="ENVIRONMENT">环境卫生类</option>
                <option value="DEVICE">设备设施类</option>
              </select>
            </template>
          </van-cell>
          <van-cell center title="拍照核验机位">
            <template #right-icon>
              <select v-model="indicatorForm.photo_perspective" class="inline-select">
                <option value="FRONT">前视角 (主讲台/幕布)</option>
                <option value="REAR">后视角 (入户门/后墙)</option>
                <option value="AC_PANEL">空调开关界面 (墙面面板特写)</option>
              </select>
            </template>
          </van-cell>
          <van-field
            v-model="indicatorForm.normal_condition"
            label="正常标准"
            type="textarea"
            rows="2"
            placeholder="例: 绿植枝叶翠绿茂盛，无枯黄或掉落杂叶"
          />
          <van-field
            v-model="indicatorForm.abnormal_condition"
            label="异常标准"
            type="textarea"
            rows="2"
            placeholder="例: 绿植枯萎发黄，花盆或地面散落枯叶杂物"
          />
          <van-field
            v-model="indicatorForm.description"
            label="补充说明"
            placeholder="可选填检查注意事项"
          />
        </van-cell-group>
      </div>
    </van-dialog>

    <!-- Dialog 3: Room Indicator Configuration -->
    <van-dialog
      v-model:show="showIndicatorsDialog"
      :title="`配置指标 - ${currentRoom?.room_name}`"
      show-cancel-button
      confirm-button-text="保存配置"
      :before-close="handleSaveIndicators"
    >
      <div class="dialog-indicators-wrap">
        <div class="quick-select-bar">
          <van-button size="mini" plain type="primary" @click="selectAllIndicators">全选</van-button>
          <van-button size="mini" plain @click="selectCommonIndicators">常用 7 项</van-button>
          <van-button size="mini" plain type="danger" @click="clearIndicators">清空</van-button>
        </div>

        <van-checkbox-group v-model="selectedIndicatorIds">
          <van-cell-group inset class="indicator-group">
            <van-cell
              v-for="ind in systemIndicators"
              :key="ind.id"
              clickable
              :title="ind.indicator_name"
              :label="ind.description"
              @click="toggleIndicator(ind.id)"
            >
              <template #title>
                <div class="indicator-cell-title">
                  <span class="ind-name">{{ ind.indicator_name }}</span>
                  <van-tag :type="ind.category === 'DEVICE' ? 'primary' : 'warning'" plain>
                    {{ ind.category === 'DEVICE' ? '设备类' : '环境类' }}
                  </van-tag>
                  <van-tag v-if="ind.is_custom" color="#07c160" plain>自定义</van-tag>
                </div>
              </template>
              <template #right-icon>
                <van-checkbox :name="ind.id" @click.stop />
              </template>
            </van-cell>
          </van-cell-group>
        </van-checkbox-group>
      </div>
    </van-dialog>

    <!-- Dialog 4: Standard Photos Management -->
    <van-popup
      v-model:show="showPhotosDialog"
      position="bottom"
      round
      closeable
      :style="{ maxHeight: '85%' }"
    >
      <div class="photos-popup-content">
        <div class="popup-title">
          <h3>{{ currentRoom?.room_name }} - 基准标准照片</h3>
          <p class="subtitle">AI 巡检对比依据与巡检员半透明拍照对齐基准</p>
        </div>

        <div class="standards-grid">
          <!-- FRONT Standard -->
          <div class="standard-upload-card">
            <div class="card-head">
              <span class="perspective-tag front">前视角 (FRONT)</span>
              <span class="guide-tip">站正门口向内拍摄</span>
            </div>
            <div class="preview-box">
              <van-image
                v-if="frontStandardPhoto"
                :src="frontStandardPhoto.photo_url"
                fit="cover"
                class="photo-img"
              />
              <div v-else class="empty-photo">
                <van-icon name="photograph" size="36" color="#c8c9cc" />
                <span>暂未上传前基准图</span>
              </div>
            </div>
            <div class="upload-btn-wrap">
              <van-uploader :after-read="(file: any) => handleUploadStandard('FRONT', file)">
                <van-button size="small" type="primary" plain round icon="upgrade">
                  {{ frontStandardPhoto ? '更换前视角图' : '上传前基准照' }}
                </van-button>
              </van-uploader>
            </div>
          </div>

          <!-- REAR Standard -->
          <div class="standard-upload-card">
            <div class="card-head">
              <span class="perspective-tag rear">后视角 (REAR)</span>
              <span class="guide-tip">从发言席向门口拍摄</span>
            </div>
            <div class="preview-box">
              <van-image
                v-if="rearStandardPhoto"
                :src="rearStandardPhoto.photo_url"
                fit="cover"
                class="photo-img"
              />
              <div v-else class="empty-photo">
                <van-icon name="photograph" size="36" color="#c8c9cc" />
                <span>暂未上传后基准图</span>
              </div>
            </div>
            <div class="upload-btn-wrap">
              <van-uploader :after-read="(file: any) => handleUploadStandard('REAR', file)">
                <van-button size="small" type="primary" plain round icon="upgrade">
                  {{ rearStandardPhoto ? '更换后视角图' : '上传后基准照' }}
                </van-button>
              </van-uploader>
            </div>
          </div>

          <!-- AC_PANEL Standard -->
          <div class="standard-upload-card">
            <div class="card-head">
              <span class="perspective-tag ac">空调面板 (AC_PANEL)</span>
              <span class="guide-tip">墙面温控面板平视特写</span>
            </div>
            <div class="preview-box">
              <van-image
                v-if="acPanelStandardPhoto"
                :src="acPanelStandardPhoto.photo_url"
                fit="cover"
                class="photo-img"
              />
              <div v-else class="empty-photo">
                <van-icon name="photograph" size="36" color="#c8c9cc" />
                <span>暂未上传空调开关图</span>
              </div>
            </div>
            <div class="upload-btn-wrap">
              <van-uploader :after-read="(file: any) => handleUploadStandard('AC_PANEL', file)">
                <van-button size="small" type="primary" plain round icon="upgrade">
                  {{ acPanelStandardPhoto ? '更换空调面板图' : '上传空调面板照' }}
                </van-button>
              </van-uploader>
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
import { showToast, showSuccessToast, showDialog } from 'vant'
import { roomApi, indicatorApi } from '../api'
import type {
  MeetingRoom,
  InspectionIndicator,
  RoomIndicatorItem,
  StandardPhoto,
} from '../types'

const router = useRouter()
const activeMainTab = ref('rooms')

const rooms = ref<MeetingRoom[]>([])
const systemIndicators = ref<InspectionIndicator[]>([])
const roomIndicatorsMap = ref<Record<number, RoomIndicatorItem[]>>({})
const roomPhotosMap = ref<Record<number, StandardPhoto[]>>({})
const refreshing = ref(false)

// Indicators tab filters
const indicatorCategoryFilter = ref('ALL')

const customIndicatorsCount = computed(() => {
  return systemIndicators.value.filter((i) => i.is_custom).length
})

const filteredIndicators = computed(() => {
  if (indicatorCategoryFilter.value === 'ALL') return systemIndicators.value
  if (indicatorCategoryFilter.value === 'CUSTOM') return systemIndicators.value.filter((i) => i.is_custom)
  return systemIndicators.value.filter((i) => i.category === indicatorCategoryFilter.value)
})

// Active count
const activeRoomsCount = computed(() => {
  return rooms.value.filter((r) => r.inspection_enabled).length
})

// Room Form
const showRoomDialog = ref(false)
const isEditing = ref(false)
const roomForm = ref<Partial<MeetingRoom>>({
  room_code: '',
  room_name: '',
  building: '总部研发大楼',
  floor: '3F',
  location_desc: '',
  inspection_enabled: true,
})

// Indicator Form Modal
const showIndicatorFormDialog = ref(false)
const isEditingIndicator = ref(false)
const indicatorForm = ref<Partial<InspectionIndicator>>({
  indicator_name: '',
  category: 'ENVIRONMENT',
  photo_perspective: 'FRONT',
  normal_condition: '',
  abnormal_condition: '',
  description: '',
})

// Indicator Dialog
const showIndicatorsDialog = ref(false)
const currentRoom = ref<MeetingRoom | null>(null)
const selectedIndicatorIds = ref<number[]>([])

// Photos Dialog
const showPhotosDialog = ref(false)
const currentRoomPhotos = ref<StandardPhoto[]>([])

const frontStandardPhoto = computed(() => {
  return currentRoomPhotos.value.find((p) => p.photo_type === 'FRONT')
})
const rearStandardPhoto = computed(() => {
  return currentRoomPhotos.value.find((p) => p.photo_type === 'REAR')
})
const acPanelStandardPhoto = computed(() => {
  return currentRoomPhotos.value.find((p) => p.photo_type === 'AC_PANEL')
})

const goBack = () => {
  router.push('/')
}

const loadData = async () => {
  try {
    const [roomsRes, indicatorsRes] = await Promise.all([
      roomApi.list({}),
      indicatorApi.list({}),
    ])
    rooms.value = roomsRes.data.items || []
    systemIndicators.value = indicatorsRes.data || []

    // Load indicators & photos for each room
    for (const r of rooms.value) {
      try {
        const indRes = await roomApi.getIndicators(r.id)
        roomIndicatorsMap.value[r.id] = indRes.data || []

        const photoRes = await roomApi.getStandardPhotos(r.id)
        roomPhotosMap.value[r.id] = photoRes.data || []
      } catch (e) {
        // ignore
      }
    }
  } catch (e: any) {
    showToast('加载失败: ' + (e.message || '网络异常'))
  } finally {
    refreshing.value = false
  }
}

onMounted(() => {
  loadData()
})

const getPhotosStatusText = (roomId: number) => {
  const photos = roomPhotosMap.value[roomId] || []
  const hasFront = photos.some((p) => p.photo_type === 'FRONT')
  const hasRear = photos.some((p) => p.photo_type === 'REAR')
  const hasAc = photos.some((p) => p.photo_type === 'AC_PANEL')
  if (hasFront && hasRear && hasAc) return '已齐备 (前/后/空调)'
  if (hasFront && hasRear) return '已齐备 (前/后)'
  const list = []
  if (hasFront) list.push('前')
  if (hasRear) list.push('后')
  if (hasAc) list.push('空调')
  return list.length ? `已传(${list.join('/')})` : '未上传'
}

// Add Room
const openAddDialog = () => {
  isEditing.value = false
  roomForm.value = {
    room_code: '',
    room_name: '',
    building: '总部研发大楼',
    floor: '3F',
    location_desc: '',
    inspection_enabled: true,
  }
  showRoomDialog.value = true
}

// Edit Room
const openEditDialog = (room: MeetingRoom) => {
  isEditing.value = true
  roomForm.value = { ...room }
  showRoomDialog.value = true
}

const handleSaveRoom = async (action: string) => {
  if (action !== 'confirm') return true

  if (!roomForm.value.room_code?.trim()) {
    showToast('请输入会议室编号')
    return false
  }
  if (!roomForm.value.room_name?.trim()) {
    showToast('请输入会议室名称')
    return false
  }

  try {
    if (isEditing.value && roomForm.value.id) {
      await roomApi.update(roomForm.value.id, roomForm.value)
      showSuccessToast('会议室信息已更新')
    } else {
      await roomApi.create(roomForm.value)
      showSuccessToast('新建会议室成功，已自动关联默认指标')
    }
    await loadData()
    return true
  } catch (e: any) {
    showToast('保存失败: ' + (e.response?.data?.detail || e.message))
    return false
  }
}

const toggleRoomInspection = async (room: MeetingRoom, enabled: boolean) => {
  try {
    await roomApi.update(room.id, { inspection_enabled: enabled })
    room.inspection_enabled = enabled
    showSuccessToast(enabled ? '已开启每日巡检' : '已暂停巡检')
  } catch (e: any) {
    showToast('更新状态失败: ' + e.message)
  }
}

const confirmDeleteRoom = (room: MeetingRoom) => {
  showDialog({
    title: '确认删除会议室？',
    message: `删除会议室「${room.room_name} (${room.room_code})」？若该会议室已有巡检记录，系统将安全转为停用存档。`,
    showCancelButton: true,
    confirmButtonColor: '#ee0a24',
  }).then(async () => {
    try {
      const res = await roomApi.delete(room.id)
      showSuccessToast(res.data?.message || '操作成功')
      await loadData()
    } catch (e: any) {
      showToast('删除失败: ' + e.message)
    }
  })
}

// ================= Indicator CRUD =================

const openAddIndicatorModal = () => {
  isEditingIndicator.value = false
  indicatorForm.value = {
    indicator_name: '',
    category: 'ENVIRONMENT',
    photo_perspective: 'FRONT',
    normal_condition: '',
    abnormal_condition: '',
    description: '',
  }
  showIndicatorFormDialog.value = true
}

const openEditIndicatorModal = (ind: InspectionIndicator) => {
  isEditingIndicator.value = true
  indicatorForm.value = { ...ind }
  showIndicatorFormDialog.value = true
}

const handleSaveIndicatorForm = async (action: string) => {
  if (action !== 'confirm') return true
  if (!indicatorForm.value.indicator_name?.trim()) {
    showToast('请输入指标名称')
    return false
  }

  try {
    if (isEditingIndicator.value && indicatorForm.value.id) {
      await indicatorApi.update(indicatorForm.value.id, indicatorForm.value)
      showSuccessToast('指标已更新')
    } else {
      await indicatorApi.create(indicatorForm.value)
      showSuccessToast('新增自定义指标成功！')
    }
    await loadData()
    return true
  } catch (e: any) {
    showToast('保存指标失败: ' + (e.response?.data?.detail || e.message))
    return false
  }
}

const handleDeleteIndicator = (ind: InspectionIndicator) => {
  showDialog({
    title: '确认删除指标？',
    message: `确定删除自定义指标「${ind.indicator_name}」？系统将智能保护已有的历史巡检数据。`,
    showCancelButton: true,
    confirmButtonColor: '#ee0a24',
  }).then(async () => {
    try {
      const res = await indicatorApi.delete(ind.id)
      showSuccessToast(res.data?.message || '已成功删除')
      await loadData()
    } catch (e: any) {
      showToast('删除失败: ' + (e.response?.data?.detail || e.message))
    }
  })
}

// ================= Room Indicator Config =================

const openIndicatorsDialog = async (room: MeetingRoom) => {
  currentRoom.value = room
  const list = roomIndicatorsMap.value[room.id] || []
  selectedIndicatorIds.value = list.map((i) => i.indicator_id)
  showIndicatorsDialog.value = true
}

const toggleIndicator = (id: number) => {
  const index = selectedIndicatorIds.value.indexOf(id)
  if (index > -1) {
    selectedIndicatorIds.value.splice(index, 1)
  } else {
    selectedIndicatorIds.value.push(id)
  }
}

const selectAllIndicators = () => {
  selectedIndicatorIds.value = systemIndicators.value.map((i) => i.id)
}

const selectCommonIndicators = () => {
  selectedIndicatorIds.value = systemIndicators.value
    .filter((i) => ['I001', 'I002', 'I003', 'I004', 'I005', 'I006', 'I007'].includes(i.indicator_code))
    .map((i) => i.id)
}

const clearIndicators = () => {
  selectedIndicatorIds.value = []
}

const handleSaveIndicators = async (action: string) => {
  if (action !== 'confirm') return true
  if (!currentRoom.value) return true

  try {
    await roomApi.updateIndicators(currentRoom.value.id, selectedIndicatorIds.value)
    showSuccessToast('指标配置已保存')
    await loadData()
    return true
  } catch (e: any) {
    showToast('保存指标失败: ' + e.message)
    return false
  }
}

// ================= Photos Dialog =================

const openPhotosDialog = async (room: MeetingRoom) => {
  currentRoom.value = room
  currentRoomPhotos.value = roomPhotosMap.value[room.id] || []
  showPhotosDialog.value = true
}

const handleUploadStandard = async (photoType: 'FRONT' | 'REAR' | 'AC_PANEL', fileObj: any) => {
  if (!currentRoom.value) return
  const file = fileObj.file || fileObj
  try {
    showToast({ message: '正在上传基准照片...', type: 'loading', duration: 0 })
    await roomApi.uploadStandardPhoto(currentRoom.value.id, photoType, file)
    showSuccessToast('基准照上传成功')
    
    // Refresh photos
    const refreshRes = await roomApi.getStandardPhotos(currentRoom.value.id)
    currentRoomPhotos.value = refreshRes.data || []
    roomPhotosMap.value[currentRoom.value.id] = refreshRes.data || []
  } catch (e: any) {
    showToast('上传失败: ' + (e.response?.data?.detail || e.message))
  }
}
</script>

<style scoped>
.room-manage-page {
  padding-bottom: 30px;
  background-color: #f7f8fa;
  min-height: 100vh;
}

.tab-content-wrap {
  padding-top: 6px;
}

.stats-overview {
  display: flex;
  background: #ffffff;
  padding: 16px 12px;
  margin-bottom: 12px;
  border-bottom: 1px solid #ebedf0;
}

.stat-box {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  cursor: pointer;
}

.stat-num {
  font-size: 22px;
  font-weight: 700;
  color: #323233;
}

.stat-label {
  font-size: 12px;
  color: #969799;
  margin-top: 4px;
}

.text-success {
  color: #07c160;
}

.text-primary {
  color: #1989fa;
}

.room-list-container {
  padding: 0 12px;
}

.room-card {
  background: #ffffff;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
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

.location-desc {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #646566;
  margin-top: 8px;
}

.desc-text {
  color: #969799;
}

.config-badges {
  margin-top: 12px;
  background: #f7f8fa;
  border-radius: 8px;
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.badge-item {
  display: flex;
  align-items: center;
  font-size: 13px;
  color: #323233;
  cursor: pointer;
}

.badge-item span {
  flex: 1;
  margin-left: 8px;
}

.arrow-right {
  color: #c8c9cc;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 14px;
  padding-top: 12px;
  border-top: 1px solid #f2f3f5;
}

.switch-wrap {
  display: flex;
  align-items: center;
  gap: 6px;
}

.switch-label {
  font-size: 12px;
  color: #646566;
}

.btn-group {
  display: flex;
  gap: 6px;
}

/* Indicators Tab Styles */
.indicators-tool-bar {
  padding: 12px 14px;
  background: #ffffff;
  margin-bottom: 10px;
}

.filter-chips-row {
  display: flex;
  gap: 8px;
  overflow-x: auto;
}

.chip-btn {
  border: none;
  background: #f2f3f5;
  color: #646566;
  padding: 5px 12px;
  border-radius: 14px;
  font-size: 12px;
  cursor: pointer;
  white-space: nowrap;
}

.chip-btn.active {
  background: #e8f4ff;
  color: #1989fa;
  font-weight: 600;
}

.indicators-card-list {
  padding: 0 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.indicator-item-card {
  background: #ffffff;
  border-radius: 10px;
  padding: 14px;
  box-shadow: 0 1px 6px rgba(0, 0, 0, 0.03);
}

.ind-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.ind-left {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.ind-title {
  font-size: 15px;
  font-weight: 600;
  color: #323233;
}

.ind-right-actions {
  display: flex;
  gap: 4px;
  align-items: center;
}

.system-locked-text {
  font-size: 11px;
  color: #969799;
}

.ind-criteria-box {
  background: #f7f8fa;
  border-radius: 6px;
  padding: 8px 10px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 12px;
}

.criteria-row {
  display: flex;
  line-height: 1.4;
}

.c-tag {
  font-weight: 600;
  flex-shrink: 0;
}

.c-tag.green {
  color: #07c160;
}

.c-tag.red {
  color: #ee0a24;
}

.c-desc {
  color: #646566;
}

/* Dialog Form */
.dialog-form {
  padding: 12px 0;
  max-height: 420px;
  overflow-y: auto;
}

.inline-select {
  border: 1px solid #dcdee0;
  border-radius: 4px;
  padding: 4px 8px;
  font-size: 13px;
  background: #ffffff;
  outline: none;
}

/* Indicators Dialog */
.dialog-indicators-wrap {
  max-height: 420px;
  overflow-y: auto;
  padding: 8px 0;
}

.quick-select-bar {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 0 16px 10px;
}

.indicator-cell-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.ind-name {
  font-weight: 500;
  font-size: 14px;
}

/* Photos Popup */
.photos-popup-content {
  padding: 20px 16px 30px;
}

.popup-title h3 {
  font-size: 18px;
  font-weight: 600;
  color: #323233;
}

.subtitle {
  font-size: 12px;
  color: #969799;
  margin-top: 4px;
  margin-bottom: 16px;
}

.standards-grid {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.standard-upload-card {
  border: 1px solid #ebedf0;
  border-radius: 10px;
  padding: 12px;
  background: #fafafa;
}

.card-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.perspective-tag {
  font-size: 12px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 4px;
}

.perspective-tag.front {
  background: #e8f4ff;
  color: #1989fa;
}

.perspective-tag.rear {
  background: #f6edff;
  color: #7232dd;
}

.perspective-tag.ac {
  background: #e6f7ff;
  color: #0070cc;
}

.guide-tip {
  font-size: 11px;
  color: #969799;
}

.preview-box {
  width: 100%;
  height: 160px;
  border-radius: 8px;
  overflow: hidden;
  background: #f2f3f5;
  display: flex;
  align-items: center;
  justify-content: center;
}

.photo-img {
  width: 100%;
  height: 100%;
}

.empty-photo {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #969799;
}

.upload-btn-wrap {
  display: flex;
  justify-content: center;
  margin-top: 10px;
}
</style>
