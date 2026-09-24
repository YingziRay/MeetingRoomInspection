<template>
  <div class="inspection-flow-page">
    <van-nav-bar
      title="会议室巡检"
      left-text="返回"
      left-arrow
      @click-left="goBack"
      fixed
      placeholder
    />

    <!-- Step Bar -->
    <van-steps :active="currentStep" active-color="#1989fa">
      <van-step>规范拍照</van-step>
      <van-step>AI研判</van-step>
      <van-step>人工核对</van-step>
      <van-step>完成归档</van-step>
    </van-steps>

    <!-- Room Info Card -->
    <div class="room-banner">
      <div class="room-main">
        <span class="room-name">{{ roomInfo?.room_name || '301会议室' }}</span>
        <span class="room-loc">{{ roomInfo?.building }} {{ roomInfo?.floor }}</span>
      </div>
      <van-tag type="primary" size="medium">{{ taskInfo?.period }}巡检</van-tag>
    </div>

    <!-- ================= STAGE 1: Photo Taking ================= -->
    <div v-if="currentStep === 0" class="step-container">
      <div class="guide-tip">
        <van-icon name="info-o" color="#1989fa" />
        <span>请站在地面标记机位，分别拍摄【前视角】与【后视角】照片</span>
      </div>

      <!-- FRONT Photo Card -->
      <div class="photo-capture-card">
        <div class="card-head">
          <span class="title">1. 前视角 (正门入口 → 会议桌/幕布)</span>
          <van-tag v-if="frontPhoto?.quality_status === 'PASS'" type="success">质检合格</van-tag>
          <van-tag v-else-if="frontPhoto" type="danger">{{ frontPhoto.quality_status }}</van-tag>
          <van-tag v-else type="default">待拍摄</van-tag>
        </div>

        <!-- Reference Overlay / Live Preview -->
        <div class="photo-preview-box">
          <img
            v-if="frontPreviewUrl"
            :src="frontPreviewUrl"
            class="preview-img"
            alt="前视图现场实拍"
          />
          <div v-else class="placeholder-box">
            <img
              :src="'/uploads/standards/RM301_FRONT.JPG'"
              class="standard-overlay"
              alt="基准参考"
            />
            <div class="overlay-mask">
              <van-icon name="photograph" size="40" />
              <span>参考基准机位 (点击下方拍照)</span>
            </div>
          </div>
        </div>

        <div class="card-actions">
          <input
            type="file"
            accept="image/*"
            capture="environment"
            ref="frontInput"
            class="hidden-file-input"
            @change="handleFileUpload($event, 'FRONT')"
          />
          <van-button
            type="primary"
            round
            block
            size="small"
            :loading="uploadingFront"
            @click="triggerPhotoInput('FRONT')"
          >
            {{ frontPhoto ? '重新拍摄前视图' : '拍摄前视图照片' }}
          </van-button>
        </div>

        <div v-if="frontPhoto?.quality_reason" class="quality-reason-alert">
          {{ frontPhoto.quality_reason }}
        </div>
      </div>

      <!-- REAR Photo Card -->
      <div class="photo-capture-card">
        <div class="card-head">
          <span class="title">2. 后视角 (发言席 → 后排座椅/大门)</span>
          <van-tag v-if="rearPhoto?.quality_status === 'PASS'" type="success">质检合格</van-tag>
          <van-tag v-else-if="rearPhoto" type="danger">{{ rearPhoto.quality_status }}</van-tag>
          <van-tag v-else type="default">待拍摄</van-tag>
        </div>

        <!-- Reference Overlay / Live Preview -->
        <div class="photo-preview-box">
          <img
            v-if="rearPreviewUrl"
            :src="rearPreviewUrl"
            class="preview-img"
            alt="后视图现场实拍"
          />
          <div v-else class="placeholder-box">
            <img
              :src="'/uploads/standards/RM301_REAR.JPG'"
              class="standard-overlay"
              alt="基准参考"
            />
            <div class="overlay-mask">
              <van-icon name="photograph" size="40" />
              <span>参考基准机位 (点击下方拍照)</span>
            </div>
          </div>
        </div>


        <div class="card-actions">
          <input
            type="file"
            accept="image/*"
            capture="environment"
            ref="rearInput"
            class="hidden-file-input"
            @change="handleFileUpload($event, 'REAR')"
          />
          <van-button
            type="primary"
            round
            block
            size="small"
            :loading="uploadingRear"
            @click="triggerPhotoInput('REAR')"
          >
            {{ rearPhoto ? '重新拍摄后视图' : '拍摄后视图照片' }}
          </van-button>
        </div>

        <div v-if="rearPhoto?.quality_reason" class="quality-reason-alert">
          {{ rearPhoto.quality_reason }}
        </div>
      </div>

      <!-- Start AI Analysis Bar -->
      <div class="bottom-action-fixed">
        <van-button
          type="primary"
          round
          block
          size="large"
          :disabled="!canStartAi"
          :loading="analyzing"
          @click="startAiAnalysis"
        >
          {{ canStartAi ? '两张照片已就绪，开始AI智能识别' : '请先完成两张合规照片拍摄' }}
        </van-button>
      </div>
    </div>

    <!-- ================= STAGE 2: AI Loading ================= -->
    <div v-else-if="currentStep === 1" class="step-container ai-loading-box">
      <van-loading type="spinner" color="#1989fa" size="48px" vertical>
        <span class="loading-main-text">多模态大模型正在逐项分析巡检指标...</span>
      </van-loading>
      <div class="loading-sub-text">
        正在比对现场照片与基准标准图差异（约需 8~10 秒，请稍候）
      </div>
    </div>

    <!-- ================= STAGE 3: Human Verification ================= -->
    <div v-else-if="currentStep === 2" class="step-container results-step">
      <div class="results-header-bar">
        <div class="summary-text">
          AI 初判发现 <b style="color: #ee0a24">{{ abnormalCount }}</b> 项异常
        </div>
        <van-button size="small" type="primary" plain round @click="oneKeyConfirmAll">
          一键确认全部正常
        </van-button>
      </div>

      <!-- 7 Indicator Cards -->
      <div class="indicator-list">
        <div
          v-for="item in results"
          :key="item.id"
          class="indicator-card"
          :class="{ 'card-abnormal': item.final_status === 'ABNORMAL' }"
        >
          <div class="ind-head">
            <span class="ind-name">{{ item.indicator_name || getIndicatorName(item.indicator_id) }}</span>
            <div class="status-selector">
              <van-button
                size="mini"
                :type="item.final_status === 'NORMAL' ? 'success' : 'default'"
                @click="setItemStatus(item, 'NORMAL')"
              >
                正常
              </van-button>
              <van-button
                size="mini"
                :type="item.final_status === 'ABNORMAL' ? 'danger' : 'default'"
                @click="setItemStatus(item, 'ABNORMAL')"
              >
                异常
              </van-button>
            </div>
          </div>

          <div class="ind-body">
            <div class="reason-row">
              <span class="label">AI研判依据:</span>
              <span class="val">{{ item.ai_reason || '正常' }}</span>
            </div>
            <div class="confidence-row">
              <span class="label">置信度:</span>
              <span class="val">{{ Math.round((item.ai_confidence || 0.8) * 100) }}%</span>
            </div>
          </div>

          <!-- Remark input when modified -->
          <div class="ind-remark-box">
            <van-field
              v-model="item.human_remark"
              placeholder="添加人工确认备注（可选）"
              input-align="left"
            />
          </div>

        </div>
      </div>

      <!-- Bottom Submit Bar -->
      <div class="bottom-action-fixed">
        <van-button
          type="primary"
          round
          block
          size="large"
          :loading="submitting"
          @click="submitInspection"
        >
          确认无误，提交巡检记录
        </van-button>
      </div>
    </div>

    <!-- ================= STAGE 4: Completed ================= -->
    <div v-else-if="currentStep === 3" class="step-container completed-box">
      <van-icon name="checked" color="#07c160" size="64px" />
      <h3 class="success-title">巡检完成并已归档</h3>
      <p class="success-subtitle">
        {{ taskInfo?.inspection_date }} {{ roomInfo?.room_name }} 巡检记录已成功保存
      </p>

      <div class="stats-card">
        <div class="stat-col">
          <span class="num text-success">{{ submitResult?.normal || 0 }}</span>
          <span class="label">正常项</span>
        </div>
        <div class="stat-col">
          <span class="num text-danger">{{ submitResult?.abnormal || 0 }}</span>
          <span class="label">异常项</span>
        </div>
      </div>

      <div class="back-btn-box">
        <van-button type="primary" block round @click="goBack">返回任务列表</van-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showToast, showSuccessToast, showDialog } from 'vant'
import { taskApi, photoApi, resultApi, roomApi } from '../api'
import type { InspectionTask, MeetingRoom, InspectionPhoto, InspectionResult } from '../types'

const route = useRoute()
const router = useRouter()
const taskId = Number(route.query.taskId)

const currentStep = ref(0)
const taskInfo = ref<InspectionTask | null>(null)
const roomInfo = ref<MeetingRoom | null>(null)
const frontPhoto = ref<InspectionPhoto | null>(null)
const rearPhoto = ref<InspectionPhoto | null>(null)
const results = ref<InspectionResult[]>([])

const uploadingFront = ref(false)
const uploadingRear = ref(false)
const analyzing = ref(false)
const submitting = ref(false)
const submitResult = ref<any>(null)

const frontInput = ref<HTMLInputElement | null>(null)
const rearInput = ref<HTMLInputElement | null>(null)

const frontPreviewUrl = computed(() => frontPhoto.value?.photo_url)
const rearPreviewUrl = computed(() => rearPhoto.value?.photo_url)

const canStartAi = computed(() => {
  return (
    frontPhoto.value?.quality_status === 'PASS' &&
    rearPhoto.value?.quality_status === 'PASS'
  )
})

const abnormalCount = computed(() => {
  return results.value.filter((r) => r.final_status === 'ABNORMAL').length
})

const indicatorNames: Record<number, string> = {
  1: '灯',
  2: '空调',
  3: '电脑显示器',
  4: '投影仪',
  5: '桌面',
  6: '椅子',
  7: '白板',
}

const getIndicatorName = (indicatorId: number) => {
  return indicatorNames[indicatorId] || `巡检项 #${indicatorId}`
}

const loadTaskState = async () => {
  if (!taskId) {
    showToast('缺少任务ID')
    router.replace('/')
    return
  }
  try {
    const tRes = await taskApi.get(taskId)
    taskInfo.value = tRes.data

    const rRes = await roomApi.get(taskInfo.value.room_id)
    roomInfo.value = rRes.data

    // Load existing photos
    const pRes = await photoApi.byTask(taskId)
    frontPhoto.value = pRes.data.find((p) => p.photo_type === 'FRONT') || null
    rearPhoto.value = pRes.data.find((p) => p.photo_type === 'REAR') || null

    // Determine current step based on task status
    if (taskInfo.value.status === 'COMPLETED') {
      currentStep.value = 3
    } else if (taskInfo.value.status === 'WAITING_CONFIRM') {
      currentStep.value = 2
      await loadResults()
    } else if (taskInfo.value.status === 'AI_ANALYZING') {
      currentStep.value = 1
    } else {
      currentStep.value = 0
    }
  } catch (e: any) {
    showToast('加载失败: ' + (e.message || '网络错误'))
  }
}

const loadResults = async () => {
  const res = await resultApi.byTask(taskId)
  results.value = res.data.map((r) => ({
    ...r,
    final_status: r.final_status || r.ai_status || 'NORMAL',
  }))
}

const triggerPhotoInput = (type: 'FRONT' | 'REAR') => {
  if (type === 'FRONT') {
    frontInput.value?.click()
  } else {
    rearInput.value?.click()
  }
}

const handleFileUpload = async (event: Event, type: 'FRONT' | 'REAR') => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return

  if (type === 'FRONT') uploadingFront.value = true
  else uploadingRear.value = true

  try {
    const res = await photoApi.upload(taskId, type, file)
    const uploaded = res.data

    if (type === 'FRONT') {
      frontPhoto.value = uploaded as any
    } else {
      rearPhoto.value = uploaded as any
    }

    if (!uploaded.quality_passed) {
      showDialog({
        title: '照片质量未通过',
        message: uploaded.quality_reason || '照片清晰度或光线不足，请重新拍摄',
        theme: 'round-button',
      })
    } else {
      showSuccessToast('拍摄合格')
    }
  } catch (err: any) {
    showToast('上传失败: ' + (err.message || '网络异常'))
  } finally {
    if (type === 'FRONT') uploadingFront.value = false
    else uploadingRear.value = false
    target.value = ''
  }
}

const startAiAnalysis = async () => {
  currentStep.value = 1
  analyzing.value = true
  try {
    const res = await taskApi.analyze(taskId)
    results.value = res.data.map((r) => ({
      ...r,
      final_status: r.final_status || r.ai_status || 'NORMAL',
    }))
    currentStep.value = 2
    showSuccessToast('AI研判完成')
  } catch (e: any) {
    showToast('AI识别失败: ' + (e.message || '请重试'))
    currentStep.value = 0
  } finally {
    analyzing.value = false
  }
}

const setItemStatus = (item: InspectionResult, status: 'NORMAL' | 'ABNORMAL') => {
  item.final_status = status
}

const oneKeyConfirmAll = () => {
  results.value.forEach((r) => {
    r.final_status = 'NORMAL'
    r.human_remark = '巡检员现场复核确认正常'
  })
  showSuccessToast('已将全部指标标记为正常')
}

const submitInspection = async () => {
  submitting.value = true
  try {
    // 1. Batch Confirm
    const itemsToSave = results.value.map((r) => ({
      result_id: r.id,
      human_status: r.final_status || 'NORMAL',
      human_remark: r.human_remark || '',
    }))
    await resultApi.batchConfirm(taskId, itemsToSave)

    // 2. Submit Task
    const res = await taskApi.submit(taskId, {
      confirm_all: true,
      force_confirm_uncertain: true,
      inspector_id: '现场巡检员',
    })

    submitResult.value = res.data
    currentStep.value = 3
    showSuccessToast('巡检提交成功')
  } catch (e: any) {
    showToast('提交失败: ' + (e.message || '校验未通过'))
  } finally {
    submitting.value = false
  }
}

const goBack = () => {
  router.push('/')
}

onMounted(() => {
  loadTaskState()
})
</script>

<style scoped>
.inspection-flow-page {
  padding-bottom: 90px;
}

.room-banner {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background-color: #f7f8fa;
  border-bottom: 1px solid #ebedf0;
}

.room-main .room-name {
  font-size: 16px;
  font-weight: 600;
  color: #323233;
  margin-right: 8px;
}

.room-main .room-loc {
  font-size: 12px;
  color: #969799;
}

.step-container {
  padding: 16px;
}

.guide-tip {
  display: flex;
  align-items: center;
  gap: 8px;
  background-color: #ecf9ff;
  color: #1989fa;
  padding: 10px 14px;
  border-radius: 8px;
  font-size: 13px;
  margin-bottom: 16px;
}

.photo-capture-card {
  background: #ffffff;
  border: 1px solid #ebedf0;
  border-radius: 12px;
  padding: 14px;
  margin-bottom: 16px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.03);
}

.card-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.card-head .title {
  font-size: 14px;
  font-weight: 600;
  color: #323233;
}

.photo-preview-box {
  position: relative;
  width: 100%;
  height: 180px;
  background-color: #000;
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.preview-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.placeholder-box {
  position: relative;
  width: 100%;
  height: 100%;
}

.standard-overlay {
  width: 100%;
  height: 100%;
  object-fit: cover;
  opacity: 0.35;
}

.overlay-mask {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #ffffff;
  font-size: 13px;
  gap: 8px;
  background: rgba(0, 0, 0, 0.2);
}

.hidden-file-input {
  display: none;
}

.quality-reason-alert {
  margin-top: 8px;
  font-size: 12px;
  color: #ee0a24;
  background-color: #fff2f0;
  padding: 6px 10px;
  border-radius: 4px;
}

.bottom-action-fixed {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  max-width: 600px;
  margin: 0 auto;
  padding: 12px 16px;
  background-color: #ffffff;
  border-top: 1px solid #ebedf0;
  z-index: 99;
}

.ai-loading-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding-top: 80px;
}

.loading-main-text {
  margin-top: 16px;
  font-size: 15px;
  font-weight: 500;
  color: #323233;
}

.loading-sub-text {
  margin-top: 8px;
  font-size: 12px;
  color: #969799;
  text-align: center;
}

.results-header-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
}

.summary-text {
  font-size: 14px;
  font-weight: 500;
  color: #323233;
}

.indicator-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.indicator-card {
  background: #ffffff;
  border: 1px solid #ebedf0;
  border-radius: 10px;
  padding: 12px 14px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.02);
}

.card-abnormal {
  border-left: 4px solid #ee0a24;
}

.ind-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.ind-name {
  font-size: 15px;
  font-weight: 600;
  color: #323233;
}

.status-selector {
  display: flex;
  gap: 6px;
}

.ind-body {
  font-size: 13px;
  color: #646566;
  margin-bottom: 8px;
}

.reason-row,
.confidence-row {
  display: flex;
  gap: 6px;
  margin-bottom: 4px;
}

.reason-row .label,
.confidence-row .label {
  color: #969799;
  flex-shrink: 0;
}

.reason-row .val {
  color: #323233;
}

.ind-remark-box {
  background-color: #f7f8fa;
  border-radius: 6px;
  overflow: hidden;
}

.completed-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding-top: 60px;
  text-align: center;
}

.success-title {
  margin-top: 16px;
  font-size: 18px;
  font-weight: 600;
  color: #323233;
}

.success-subtitle {
  margin-top: 6px;
  font-size: 13px;
  color: #969799;
  margin-bottom: 24px;
}

.stats-card {
  display: flex;
  width: 100%;
  max-width: 280px;
  background: #f7f8fa;
  border-radius: 12px;
  padding: 16px;
  justify-content: space-around;
  margin-bottom: 30px;
}

.stat-col {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stat-col .num {
  font-size: 24px;
  font-weight: bold;
}

.text-success {
  color: #07c160;
}

.text-danger {
  color: #ee0a24;
}

.stat-col .label {
  font-size: 12px;
  color: #646566;
  margin-top: 4px;
}

.back-btn-box {
  width: 100%;
  max-width: 280px;
}
</style>
