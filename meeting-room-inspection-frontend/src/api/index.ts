import axios from 'axios'
import type {
  MeetingRoom,
  InspectionTask,
  InspectionPhoto,
  InspectionResult,
  PhotoUploadResponse,
} from '../types'

const apiClient = axios.create({
  baseURL: '/api/v1',
  timeout: 60000, // 60s for AI inference
})

export const roomApi = {
  // 获取会议室列表
  list: (params?: { status?: string; inspection_enabled?: boolean }) =>
    apiClient.get<{ items: MeetingRoom[]; total: number }>('/rooms', { params }),
  // 获取指定会议室详情
  get: (roomId: number) => apiClient.get<MeetingRoom>(`/rooms/${roomId}`),
}

export const taskApi = {
  // 生成任务
  generate: (inspectionDate: string, period: string) =>
    apiClient.post<InspectionTask[]>('/inspection-tasks/generate', {
      inspection_date: inspectionDate,
      period,
    }),
  // 获取任务详情
  get: (taskId: number) => apiClient.get<InspectionTask>(`/inspection-tasks/${taskId}`),
  // 开始任务
  start: (taskId: number) => apiClient.post(`/inspection-tasks/${taskId}/start`),
  // 触发 AI 分析
  analyze: (taskId: number) =>
    apiClient.post<InspectionResult[]>(`/inspection-tasks/${taskId}/analyze`),
  // 提交任务
  submit: (taskId: number, payload: {
    confirm_all?: boolean
    force_confirm_uncertain?: boolean
    inspector_id?: string
  }) => apiClient.post(`/inspection-tasks/${taskId}/submit`, payload),
}

export const photoApi = {
  // 上传照片（multipart/form-data）
  upload: (taskId: number, photoType: 'FRONT' | 'REAR', file: File) => {
    const formData = new FormData()
    formData.append('task_id', taskId.toString())
    formData.append('photo_type', photoType)
    formData.append('file', file)
    return apiClient.post<PhotoUploadResponse>('/photos/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  // 获取某任务的照片列表
  byTask: (taskId: number) =>
    apiClient.get<InspectionPhoto[]>(`/photos/by-task/${taskId}`),
}

export const resultApi = {
  // 获取任务巡检指标结果
  byTask: (taskId: number) =>
    apiClient.get<InspectionResult[]>(`/inspection-results/by-task/${taskId}`),
  // 单项确认
  confirm: (resultId: number, humanStatus: string, humanRemark?: string) =>
    apiClient.patch(`/inspection-results/${resultId}/confirm`, {
      human_status: humanStatus,
      human_remark: humanRemark,
    }),
  // 批量确认
  batchConfirm: (taskId: number, items: Array<{
    result_id: number
    human_status: string
    human_remark?: string
  }>, confirmAllAsAi: boolean = false) =>
    apiClient.post<InspectionResult[]>('/inspection-results/batch-confirm', {
      task_id: taskId,
      confirm_all_as_ai: confirmAllAsAi,
      items,
    }),
}

export const notificationApi = {
  test: () => apiClient.post<{ success: boolean; webhook_configured: boolean; target_url: string }>('/notifications/test'),
}

