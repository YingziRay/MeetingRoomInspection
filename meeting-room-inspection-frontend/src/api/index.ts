import axios from 'axios'
import type {
  MeetingRoom,
  InspectionTask,
  InspectionPhoto,
  InspectionResult,
  PhotoUploadResponse,
  InspectionIndicator,
  RoomIndicatorItem,
  StandardPhoto,
} from '../types'

const apiClient = axios.create({
  baseURL: '/api/v1',
  timeout: 60000, // 60s for AI inference
})

export const roomApi = {
  // 获取会议室列表
  list: (params?: { status?: string; inspection_enabled?: boolean }) =>
    apiClient.get<{ items: MeetingRoom[]; total: number }>('/rooms', { params }),
  // 创建会议室
  create: (data: Partial<MeetingRoom>) =>
    apiClient.post<MeetingRoom>('/rooms', data),
  // 获取指定会议室详情
  get: (roomId: number) => apiClient.get<MeetingRoom>(`/rooms/${roomId}`),
  // 更新会议室信息
  update: (roomId: number, data: Partial<MeetingRoom>) =>
    apiClient.patch<MeetingRoom>(`/rooms/${roomId}`, data),
  // 删除或停用会议室
  delete: (roomId: number) =>
    apiClient.delete<{ success: boolean; message: string }>(`/rooms/${roomId}`),
  // 获取会议室关联指标
  getIndicators: (roomId: number) =>
    apiClient.get<RoomIndicatorItem[]>(`/rooms/${roomId}/indicators`),
  // 批量配置会议室指标
  updateIndicators: (roomId: number, indicatorIds: number[]) =>
    apiClient.put<RoomIndicatorItem[]>(`/rooms/${roomId}/indicators`, {
      indicator_ids: indicatorIds,
    }),
  // 获取会议室基准照片
  getStandardPhotos: (roomId: number) =>
    apiClient.get<StandardPhoto[]>(`/rooms/${roomId}/standard-photos`),
  // 上传基准照片
  uploadStandardPhoto: (
    roomId: number,
    photoType: 'FRONT' | 'REAR' | 'AC_PANEL' | string,
    file: File,
    shootPosition?: string,
    cameraDirection?: string
  ) => {
    const formData = new FormData()
    formData.append('photo_type', photoType)
    formData.append('file', file)
    if (shootPosition) formData.append('shoot_position', shootPosition)
    if (cameraDirection) formData.append('camera_direction', cameraDirection)
    return apiClient.post<StandardPhoto>(`/rooms/${roomId}/standard-photos`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
}

export const indicatorApi = {
  // 获取系统所有可用巡检指标
  list: (params?: { category?: string; enabled_only?: boolean }) =>
    apiClient.get<InspectionIndicator[]>('/indicators', { params }),
  // 新建自定义巡检指标
  create: (data: Partial<InspectionIndicator>) =>
    apiClient.post<InspectionIndicator>('/indicators', data),
  // 编辑指标
  update: (id: number, data: Partial<InspectionIndicator>) =>
    apiClient.patch<InspectionIndicator>(`/indicators/${id}`, data),
  // 删除指标
  delete: (id: number) =>
    apiClient.delete<{ success: boolean; message: string }>(`/indicators/${id}`),
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
  upload: (taskId: number, photoType: 'FRONT' | 'REAR' | 'AC_PANEL' | string, file: File) => {
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

export const dashboardApi = {
  // 获取大盘统计数据
  getStats: (startDate?: string, endDate?: string) =>
    apiClient.get<any>('/dashboard/stats', {
      params: { start_date: startDate, end_date: endDate },
    }),
  // 查询巡检台账列表
  listTasks: (params?: {
    page?: number
    page_size?: number
    start_date?: string
    end_date?: string
    room_id?: number
    period?: string
    status?: string
    has_abnormal?: boolean
  }) => apiClient.get<{ items: any[]; total: number; page: number; page_size: number }>('/dashboard/tasks', { params }),
  // 获取单任务全量留档详情
  getTaskDetail: (taskId: number) =>
    apiClient.get<any>(`/inspection-tasks/${taskId}/detail`),
  // 获取导出 CSV 下载链接
  getExportUrl: (params?: {
    start_date?: string
    end_date?: string
    room_id?: number
    period?: string
    status?: string
  }) => {
    const searchParams = new URLSearchParams()
    if (params?.start_date) searchParams.append('start_date', params.start_date)
    if (params?.end_date) searchParams.append('end_date', params.end_date)
    if (params?.room_id) searchParams.append('room_id', params.room_id.toString())
    if (params?.period) searchParams.append('period', params.period)
    if (params?.status) searchParams.append('status', params.status)
    return `/api/v1/dashboard/export?${searchParams.toString()}`
  },
}

