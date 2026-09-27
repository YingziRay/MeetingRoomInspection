export interface MeetingRoom {
  id: number
  room_code: string
  room_name: string
  building?: string
  floor?: string
  location_desc?: string
  status: string
  inspection_enabled: boolean
}

export interface InspectionTask {
  id: number
  task_no: string
  room_id: number
  inspection_date: string
  period: string
  inspector_id?: string
  status: 'PENDING' | 'IN_PROGRESS' | 'AI_ANALYZING' | 'WAITING_CONFIRM' | 'COMPLETED'
  due_at?: string
  started_at?: string
  completed_at?: string
}

export interface InspectionPhoto {
  id: number
  task_id: number
  photo_type: 'FRONT' | 'REAR'
  photo_url: string
  original_filename?: string
  width?: number
  height?: number
  quality_status?: 'PASS' | 'BLURRY' | 'TOO_DARK' | 'OVEREXPOSED' | 'LOW_RESOLUTION'
  quality_reason?: string
}

export interface InspectionResult {
  id: number
  task_id: number
  indicator_id: number
  ai_status?: 'NORMAL' | 'ABNORMAL' | 'UNCERTAIN'
  ai_confidence?: number
  ai_reason?: string
  ai_bbox?: { x: number; y: number; w: number; h: number }
  human_status?: 'NORMAL' | 'ABNORMAL' | 'UNCERTAIN'
  human_remark?: string
  final_status?: 'NORMAL' | 'ABNORMAL' | 'UNCERTAIN'
  confirmed_by?: string
  confirmed_at?: string
  indicator_name?: string
  indicator_code?: string
}

export interface PhotoUploadResponse {
  photo_id: number
  task_id: number
  photo_type: string
  photo_url: string
  quality_passed: boolean
  quality_status: string
  quality_reason?: string
  width: number
  height: number
  blur_score?: number
  brightness?: number
}

export interface InspectionIndicator {
  id: number
  indicator_code: string
  indicator_name: string
  category?: string
  description?: string
  normal_condition?: string
  abnormal_condition?: string
  ai_supported: boolean
  enabled: boolean
  sort_order: number
}

export interface RoomIndicatorItem {
  id: number
  room_id: number
  indicator_id: number
  indicator_code: string
  indicator_name: string
  category?: string
  enabled: boolean
  sort_order: number
}

export interface StandardPhoto {
  id: number
  room_id: number
  photo_type: 'FRONT' | 'REAR' | string
  photo_url: string
  shoot_position?: string
  camera_direction?: string
  version: number
  status: string
  created_at?: string
}

