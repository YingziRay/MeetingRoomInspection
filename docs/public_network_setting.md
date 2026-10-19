# 外网（5G/公网）环境访问与钉钉推送跳转配置指南

## 1. 核心原理与网络拓扑

### 1.1 无法访问的原因
手机在 5G/移动蜂窝网络下，处于运营商公网环境。本地电脑的 IP（如 `192.168.31.17`）属于 RFC 1918 定义的私有局域网网段，公网路由器无法解析或路由该 IP，因此手机在离开内网 WiFi 后无法直连。

### 1.2 本系统的反代架构优势
本系统在前端容器内置了 Nginx 反向代理（监听宿主机 `5173` 端口，容器内部 `80` 端口）：
* 静态页面资源由 Nginx 直接提供；
* `/api/` 路由自动反向代理至后端 `backend:8000`；
* `/uploads/` 抓拍图片静态服务自动反向代理至 `backend:8000`。

> **核心结论**：无需单独暴露或映射后端 8000 端口，**只需将前端 5173 端口映射/穿透至公网，前端界面、AI 识别接口、巡检图片加载即可全功能跑通**。

---

## 2. 方案 A：Cloudflare Tunnel（实测推荐・免费・自带官方 HTTPS）

无需公网 IP、无需路由器管理员权限，自动分配由权威 CA 机构签发的 HTTPS 域名（钉钉内置浏览器无安全拦截，体验最优）。

### 2.1 启动与配置步骤

1. **安装 cloudflared CLI**（首次需要）：
   ```bash
   brew install cloudflared
   ```

2. **启动稳定穿透隧道（关键参数：--protocol http2）**：
   > ⚠️ **避坑提示**：国内运营商（尤其移动 5G）对境外 UDP 流量存在严重 QoS 限制。务必追加 `--protocol http2` 强制走稳定 TCP 协议，避免隧道假死断连。
   ```bash
   cloudflared tunnel --protocol http2 --url http://127.0.0.1:5173
   ```

3. **获取分配的公网临时域名**：
   终端会输出类似于以下的公网临时域名：
   ```text
   +--------------------------------------------------------------------------------------------+
   |  Your quick Tunnel has been created! Visit it at (it may take some time to be reachable):  |
   |  https://sample-random-subdomain.trycloudflare.com                                         |
   +--------------------------------------------------------------------------------------------+
   ```

4. **同步更新后端配置**：
   编辑 `meeting-room-inspection-backend/.env`，将 `FRONTEND_URL` 更新为当前终端最新打印的域名：
   ```ini
   FRONTEND_URL=https://sample-random-subdomain.trycloudflare.com
   ```

5. **热重载后端服务生效**：
   ```bash
   docker compose up -d backend
   ```

6. **触发一条全新测试消息**：
   在巡检系统电脑端网页点击「测试群推送」，或在终端执行：
   ```bash
   curl -s -X POST http://127.0.0.1:8000/api/v1/notifications/test
   ```
   > ⚠️ **重要**：手机 5G 打开钉钉时，**请务必点击最新推送的一条卡片**，旧历史卡片的域名已随历史隧道关闭而失效。

---

### 2.2 方案 A 的安全停用与回收操作

`cloudflared` 临时隧道仅在本地建立向外的加密连接，本地不需要对外开放任何防火墙端口。测试完毕后按以下步骤安全下线：

1. **终止穿透进程（公网入口立刻销毁）**：
   * 在运行 `cloudflared` 的终端按 `Ctrl + C`，或在后台执行：
     ```bash
     pkill -f cloudflared
     ```
   * *进程退出后，Cloudflare 边缘节点连接立刻切断，原临时域名彻底失效，外部访问直接报 HTTP 530/1033，无法触达内网。*

2. **回滚后端配置为局域网 IP**：
   修改 `meeting-room-inspection-backend/.env`：
   ```ini
   FRONTEND_URL=http://192.168.31.17:5173
   ```
   *(若局域网 IP 发生变更，可在 Mac 终端使用 `ipconfig getifaddr en0` 查看最新 IP)*

3. **热重载后端服务**：
   ```bash
   docker compose up -d backend
   ```

4. **彻底卸载（可选，不再需要时）**：
   ```bash
   brew uninstall cloudflared
   rm -rf ~/.cloudflared
   ```

---

### 2.3 方案 A 常见问题与排查（Troubleshooting）

| 异常现象 | 核心原因 | 解决方案 |
| :--- | :--- | :--- |
| **Error 1033 (Argo Tunnel error)** | 1. 手机点击了历史旧消息（旧临时域名已废弃）<br>2. 本地 `cloudflared` 进程退出或电脑锁屏休眠<br>3. 默认 UDP 协议被运营商 QoS 丢包 | 1. 杀死进程后使用 `--protocol http2` 重新启动<br>2. 重新更新 `.env` 并重启 backend<br>3. **重新发送测试消息，手机只点击最后一条** |
| **页面白屏或加载缓慢** | 首次访问需要加载前端 JS/CSS 静态资源 | 保持 5G 信号良好，加载完成后后续交互走本地缓存秒开 |
| **提示跨域 CORS 错误** | 跨域未放行临时域名 | 后端 `.env` 中已配置 `CORS_ORIGINS=*`，若修改过请恢复为通配允许 |

---

## 3. 方案 B：cpolar 内网穿透（国内网络首选方案）

若由于地域原因访问 Cloudflare 节点延迟较高或存在丢包，建议使用国内主流的 cpolar 穿透工具（机房位于国内腾讯云/阿里云 BGP 机房，延迟 20ms 左右，网络极稳）。

### 3.1 跨平台安装与认证

* **macOS 环境**：
  ```bash
  brew install cpolar/cpolar/cpolar
  ```
* **Linux (Ubuntu / Debian / CentOS) 环境**：
  ```bash
  curl -L https://www.cpolar.com/static/downloads/install-release-cpolar.sh | sudo bash
  ```
* **绑定用户 Token（首次需要）**：
  前往 [cpolar 官网](https://www.cpolar.com/) 注册并获取 Authtoken：
  ```bash
  cpolar authtoken <your-auth-token>
  ```

---

### 3.2 运行模式

#### 模式 1：前台临时调试（终端关闭即失效）
```bash
cpolar http 5173
```
*控制台会实时打印公网 HTTPS 域名，按 `Ctrl + C` 退出。*

#### 模式 2：后台常驻系统服务（Linux 生产首选，开机自启 / SSH 退出不中断）
```bash
sudo systemctl enable cpolar
sudo systemctl start cpolar
sudo systemctl status cpolar
```

---

### 3.3 关键避坑与配置要点（Troubleshooting）

#### 坑点 1：默认端口是 8080 而不是本系统的 5173
* **现象**：通过 systemctl 启动后，生成的公网链接打不开页面。
* **原因**：cpolar 安装后，默认配置文件中自带了一个名为 `website` 的示例隧道，默认监听本地 `8080` 端口。
* **一键解决（修改配置文件并重启）**：
  ```bash
  # 1. 一键将配置文件中的 8080 端口替换为前端的 5173 端口
  sudo sed -i 's/8080/5173/g' /usr/local/etc/cpolar/cpolar.yml

  # 2. 重启 cpolar 服务生效
  sudo systemctl restart cpolar
  ```
  *(注：也可以访问本地 Web 界面 `http://<服务器IP>:9200`，在「隧道管理」->「隧道列表」中编辑 `website` 隧道，将本地地址改为 `5173` 并保存)*

#### 坑点 2：systemd 后台模式下，在哪里查看生成的 FRONTEND_URL？
在无终端界面的后台服务模式下，可通过以下 **3 种方式** 获取公网地址：

1. **本地 9200 Web 控制台（最直观）**：
   浏览器访问 `http://<服务器IP>:9200`（本机为 `http://localhost:9200`），登录后点击左侧 **「状态」 -> 「在线隧道列表」**，复制对应的公网 HTTPS 地址。
2. **命令行一键提取（最快速）**：
   在终端执行以下命令直接输出当前公网 URL：
   ```bash
   curl -s http://127.0.0.1:9200/api/v1/tunnels | grep -oE 'https://[a-zA-Z0-9.-]+\.cpolar\.(top|cn)' | head -n 1
   ```
3. **cpolar 官网仪表盘远程查看**：
   登录 [cpolar 官网在线状态页](https://dashboard.cpolar.com/status)，远程查看已上线的节点公网地址。

---

### 3.4 配置同步与热重载

获取到公网 URL（例如 `https://xxxxxx.cpolar.top`）后，更新后端配置：
```bash
# 1. 写入后端配置
sed -i 's|^FRONTEND_URL=.*|FRONTEND_URL=https://xxxxxx.cpolar.top|' meeting-room-inspection-backend/.env

# 2. 重载后端服务生效
docker compose up -d backend
```

---

### 3.5 方案 B 的安全停用与合规清理

在公司内网运行穿透服务时，测试完成后务必及时切断外网通道，杜绝内网暴露风险。根据实际安全要求选择以下处理级别：

#### 级别 1：标准停用（保留环境，关闭隧道并禁止自启）
切断公网连接，但保留二进制与配置，后续需要时随时可再次启动：
```bash
# 1. 立即停止穿透服务（公网域名瞬间失效，外部再无法访问）
sudo systemctl stop cpolar

# 2. 禁用开机自启（防止服务器重启后自动拉起公网隧道）
sudo systemctl disable cpolar

# 3. 确认服务状态 (应显示 inactive / dead)
sudo systemctl status cpolar
```

#### 级别 2：回滚后端配置为内网局域网 IP
避免钉钉后续推送的消息继续携带失效的公网域名：
```bash
# 1. 还原 FRONTEND_URL 为公司内网 IP
sed -i 's|^FRONTEND_URL=.*|FRONTEND_URL=http://192.168.31.17:5173|' meeting-room-inspection-backend/.env

# 2. 重载后端生效
docker compose up -d backend
```

#### 级别 3：彻底清除下线（最安全・企业合规审计推荐）
测试周期结束后彻底抹除 cpolar 软件本体、授权 Token 与 systemd 注册项，杜绝合规扫描告警：
```bash
# 一键彻底卸载（停止服务 -> 禁用自启 -> 移除可执行文件与配置 -> 移除服务定义 -> 重载 systemd）
sudo systemctl stop cpolar
sudo systemctl disable cpolar
sudo rm -rf /usr/local/bin/cpolar /usr/local/etc/cpolar ~/.cpolar /etc/systemd/system/cpolar.service
sudo systemctl daemon-reload
```

---

## 4. 方案 C：自建 frp 反向代理（拥有一台轻量云服务器）

适合拥有固定公网 IP 的阿里云/腾讯云 ECS，延迟最低且能绑定自有合规域名。

### 4.1 服务端（云服务器）配置 `frps.ini`
```ini
[common]
bind_port = 7000
vhost_http_port = 8080
subdomain_host = inspection.yourdomain.com
```
启动服务端：
```bash
./frps -c ./frps.ini
```

### 4.2 本地 Mac 配置 `frpc.ini`
```ini
[common]
server_addr = <云服务器公网IP>
server_port = 7000

[web]
type = http
local_ip = 127.0.0.1
local_port = 5173
custom_domains = inspection.yourdomain.com
```
启动客户端：
```bash
./frpc -c ./frpc.ini
```

### 4.3 更新配置
将 `meeting-room-inspection-backend/.env` 中的 `FRONTEND_URL` 设为 `http://inspection.yourdomain.com:8080`（或配置好 Nginx 443 SSL 证书后设为 HTTPS 地址）。

---

## 5. 方案 D：整套系统云端直接部署（生产终极方案）

将代码直接运行于云服务器，本地电脑关机不影响系统运转。

1. **打包/上传代码**：将项目源码同步至云服务器。
2. **配置云主机环境**：安装 Docker 与 Docker Compose 插件。
3. **修改云端 `.env`**：将 `FRONTEND_URL` 设为云服务器的公网 IP 或域名。
4. **一键启动**：
   ```bash
   docker compose up -d --build
   ```

---

## 6. 验证清单

- [ ] 手机切换为 5G 移动数据，关闭本地 WiFi。
- [ ] 在钉钉群点击最新推送的「👉 点击测试进入巡检系统」卡片。
- [ ] 页面正常渲染巡检任务列表、巡检报告大盘。
- [ ] 拍摄并上传照片，AI 视觉推理（`/api/v1/inspections/...`）正常返回判定结果。
