-- 1. Inspection Periods
INSERT INTO inspection_period_config (period_code, period_name, start_time, deadline_time, enabled, reminder_enabled, reminder_minutes, sort_order, created_at, updated_at)
VALUES
('MORNING', '上午巡检', '09:00:00', '10:30:00', true, true, 15, 1, NOW(), NOW()),
('NOON', '中午巡检', '13:00:00', '14:30:00', true, true, 15, 2, NOW(), NOW()),
('EVENING', '晚间巡检', '18:00:00', '19:30:00', true, true, 15, 3, NOW(), NOW())
ON CONFLICT (period_code) DO NOTHING;

-- 2. Meeting Room 301
INSERT INTO meeting_room (room_code, room_name, building, floor, location_desc, status, inspection_enabled, created_at, updated_at)
VALUES
('RM-301', '301会议室', '总部研发大楼', '3F', '3楼东侧多功能会议室', 'ACTIVE', true, NOW(), NOW())
ON CONFLICT (room_code) DO NOTHING;

-- 3. 7 Core Indicators
INSERT INTO inspection_indicator (indicator_code, indicator_name, category, description, normal_condition, abnormal_condition, ai_supported, enabled, sort_order, created_at, updated_at)
VALUES
('I001', '灯', 'DEVICE', '检查会议室所有照明灯具是否关闭', '所有照明灯光处于熄灭关闭状态', '存在未关闭的照明灯具，灯具处于亮起发光状态', true, true, 1, NOW(), NOW()),
('I002', '空调', 'DEVICE', '检查空调设备是否已完全关闭', '空调面板指示灯熄灭，出风口摆叶闭合，无送风或运行噪音', '空调指示灯亮起，出风口打开或有气流吹出', true, true, 2, NOW(), NOW()),
('I003', '电脑显示器', 'DEVICE', '检查会议终端显示器是否处于熄屏/关机状态', '电脑显示屏黑屏熄灭，无画面投显', '显示器亮屏，显示桌面、屏保或输入信号画面', true, true, 3, NOW(), NOW()),
('I004', '投影仪', 'DEVICE', '检查投影仪设备及电动幕布状态', '投影仪镜头无光束，处于待机/关机状态，幕布已收起', '投影仪处于开启投射状态，幕布展开且有投射光线', true, true, 4, NOW(), NOW()),
('I005', '桌面', 'ENVIRONMENT', '检查会议桌台面是否收拾整洁无遗留物', '台面干净整洁，无水杯、水瓶、纸屑、外卖盒及私人杂物', '台面散落杂物、未带走的饮料瓶、废纸或私人物品', true, true, 5, NOW(), NOW()),
('I006', '椅子', 'ENVIRONMENT', '检查参会座椅是否摆放归位', '所有会议椅整齐推进会议桌下方，摆放排列规范有序', '座椅随意拉出、倾斜扭转或阻挡走道未归位', true, true, 6, NOW(), NOW()),
('I007', '白板', 'ENVIRONMENT', '检查白板表面书写内容是否已擦拭干净', '白板板面擦拭干净无大面积笔迹残留，笔擦摆放于托槽内', '白板留有会议板书笔迹、污渍未清理，或板擦乱扔', true, true, 7, NOW(), NOW())
ON CONFLICT (indicator_code) DO NOTHING;

-- 4. Standard Photos (FRONT & REAR)
INSERT INTO standard_photo (room_id, photo_type, photo_url, shoot_position, camera_direction, version, status, created_at, updated_at)
SELECT id, 'FRONT', '/static/standards/RM301_FRONT.jpg', '正门入口处地面定位标识A', '正向对准主会议桌及前方幕布', 1, 'ACTIVE', NOW(), NOW()
FROM meeting_room WHERE room_code = 'RM-301'
ON CONFLICT (room_id, photo_type, version) DO NOTHING;

INSERT INTO standard_photo (room_id, photo_type, photo_url, shoot_position, camera_direction, version, status, created_at, updated_at)
SELECT id, 'REAR', '/static/standards/RM301_REAR.jpg', '主讲台发言席地面定位标识B', '反向对准后排座席与入户门', 1, 'ACTIVE', NOW(), NOW()
FROM meeting_room WHERE room_code = 'RM-301'
ON CONFLICT (room_id, photo_type, version) DO NOTHING;

-- 5. Photo Regions
INSERT INTO photo_region (standard_photo_id, region_code, region_name, x, y, width, height, description, created_at)
SELECT sp.id, 'FRONT_LIGHT', '顶灯照明区域', 0.100000, 0.000000, 0.800000, 0.250000, '会议室天花板吊顶照明灯管组', NOW()
FROM standard_photo sp JOIN meeting_room mr ON sp.room_id = mr.id
WHERE mr.room_code = 'RM-301' AND sp.photo_type = 'FRONT'
ON CONFLICT DO NOTHING;

INSERT INTO photo_region (standard_photo_id, region_code, region_name, x, y, width, height, description, created_at)
SELECT sp.id, 'FRONT_PROJECTOR', '投影仪与幕布区域', 0.250000, 0.100000, 0.500000, 0.350000, '正前方主投影幕布及天花板投影镜头', NOW()
FROM standard_photo sp JOIN meeting_room mr ON sp.room_id = mr.id
WHERE mr.room_code = 'RM-301' AND sp.photo_type = 'FRONT'
ON CONFLICT DO NOTHING;

INSERT INTO photo_region (standard_photo_id, region_code, region_name, x, y, width, height, description, created_at)
SELECT sp.id, 'FRONT_DESK', '会议主桌面区域', 0.150000, 0.450000, 0.700000, 0.350000, '中央大长条会议桌面，检查清洁与杂物', NOW()
FROM standard_photo sp JOIN meeting_room mr ON sp.room_id = mr.id
WHERE mr.room_code = 'RM-301' AND sp.photo_type = 'FRONT'
ON CONFLICT DO NOTHING;

INSERT INTO photo_region (standard_photo_id, region_code, region_name, x, y, width, height, description, created_at)
SELECT sp.id, 'FRONT_CHAIRS', '前排会议椅区域', 0.050000, 0.550000, 0.900000, 0.400000, '主桌两侧座椅摆放归位', NOW()
FROM standard_photo sp JOIN meeting_room mr ON sp.room_id = mr.id
WHERE mr.room_code = 'RM-301' AND sp.photo_type = 'FRONT'
ON CONFLICT DO NOTHING;

INSERT INTO photo_region (standard_photo_id, region_code, region_name, x, y, width, height, description, created_at)
SELECT sp.id, 'FRONT_WHITEBOARD', '侧墙白板区域', 0.020000, 0.250000, 0.200000, 0.450000, '左侧墙壁白板书写及清洁状态', NOW()
FROM standard_photo sp JOIN meeting_room mr ON sp.room_id = mr.id
WHERE mr.room_code = 'RM-301' AND sp.photo_type = 'FRONT'
ON CONFLICT DO NOTHING;

INSERT INTO photo_region (standard_photo_id, region_code, region_name, x, y, width, height, description, created_at)
SELECT sp.id, 'REAR_AC', '后墙空调区域', 0.700000, 0.100000, 0.250000, 0.250000, '后部壁挂/吸顶空调面板指示灯与摆叶', NOW()
FROM standard_photo sp JOIN meeting_room mr ON sp.room_id = mr.id
WHERE mr.room_code = 'RM-301' AND sp.photo_type = 'REAR'
ON CONFLICT DO NOTHING;

INSERT INTO photo_region (standard_photo_id, region_code, region_name, x, y, width, height, description, created_at)
SELECT sp.id, 'REAR_MONITOR', '控制电脑显示器', 0.350000, 0.450000, 0.300000, 0.350000, '发言台电脑显示屏亮灭状态', NOW()
FROM standard_photo sp JOIN meeting_room mr ON sp.room_id = mr.id
WHERE mr.room_code = 'RM-301' AND sp.photo_type = 'REAR'
ON CONFLICT DO NOTHING;

-- 6. Room Indicator Mapping
INSERT INTO room_indicator (room_id, indicator_id, region_id, standard_value, enabled, sort_order, created_at)
SELECT mr.id, ind.id, pr.id, mapping.std_val, true, ind.sort_order, NOW()
FROM (
    VALUES
    ('I001', 'FRONT_LIGHT', '关闭'),
    ('I002', 'REAR_AC', '关闭'),
    ('I003', 'REAR_MONITOR', '黑屏关闭'),
    ('I004', 'FRONT_PROJECTOR', '关闭待机'),
    ('I005', 'FRONT_DESK', '整洁无杂物'),
    ('I006', 'FRONT_CHAIRS', '整齐推入归位'),
    ('I007', 'FRONT_WHITEBOARD', '擦拭干净')
) AS mapping(ind_code, reg_code, std_val)
JOIN meeting_room mr ON mr.room_code = 'RM-301'
JOIN inspection_indicator ind ON ind.indicator_code = mapping.ind_code
JOIN photo_region pr ON pr.region_code = mapping.reg_code
ON CONFLICT (room_id, indicator_id) DO NOTHING;
