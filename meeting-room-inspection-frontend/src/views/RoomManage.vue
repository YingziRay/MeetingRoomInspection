<template>
  <div class="room-manage-page">
    <van-nav-bar
      title="会议室档案与配置"
      left-text="返回"
      left-arrow
      fixed
      placeholder
      @click-left="goBack"
    >
      <template #right>
        <van-button type="primary" size="small" round icon="plus" @click="openAddDialog">
          添加会议室
        </van-button>
      </template>
    </van-nav-bar>

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
      <div class="stat-box">
        <span class="stat-num text-primary">{{ systemIndicators.length }}</span>
        <span class="stat-label">可用指标库</span>
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
                指标
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

    <!-- Dialog 2: Indicator Configuration -->
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
                  <van-tag :type="ind.category === 'DEVICE' ? 'primary' : 'warning'" size="medium" plain>
                    {{ ind.category === 'DEVICE' ? '设备类' : '环境类' }}
                  </van-tag>
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

    <!-- Dialog 3: Standard Photos Management -->
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

const rooms = ref<MeetingRoom[]>([])
const systemIndicators = ref<InspectionIndicator[]>([])
const roomIndicatorsMap = ref<Record<number, RoomIndicatorItem[]>>({})
const roomPhotosMap = ref<Record<number, StandardPhoto[]>>({})
const refreshing = ref(false)

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
        // ignore individual room sub-fetch error
      }
    }
  } catch (e: any) {
    showToast('加载会议室档案失败: ' + (e.message || '网络异常'))
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
  if (hasFront && hasRear) return '已齐备 (前/后)'
  if (hasFront) return '仅前视角'
  if (hasRear) return '仅后视角'
  return '未上传'
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

// Indicators Dialog
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
  // Common 7 indicators (I001 ~ I007)
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

// Photos Dialog
const openPhotosDialog = async (room: MeetingRoom) => {
  currentRoom.value = room
  currentRoomPhotos.value = roomPhotosMap.value[room.id] || []
  showPhotosDialog.value = true
}

const handleUploadStandard = async (photoType: 'FRONT' | 'REAR', fileObj: any) => {
  if (!currentRoom.value) return
  const file = fileObj.file || fileObj
  try {
    showToast({ message: '正在上传基准照片...', type: 'loading', duration: 0 })
    const res = await roomApi.uploadStandardPhoto(currentRoom.value.id, photoType, file)
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

/* Dialog Form */
.dialog-form {
  padding: 12px 0;
  max-height: 400px;
  overflow-y: auto;
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
