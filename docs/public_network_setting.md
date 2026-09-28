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

若由于地域原因访问 Cloudflare 节点延迟较高，可选用国内主流的 cpolar 穿透工具（机房位于国内腾讯云/阿里云，网络极稳）。

### 操作步骤
1. **安装 cpolar**：
   ```bash
   brew install cpolar/cpolar/cpolar
   ```
2. **注册登录并启动穿透**：
   前往 [cpolar 官网](https://www.cpolar.com/) 注册账号并获取 Authtoken：
   ```bash
   cpolar authtoken <your-auth-token>
   cpolar http 5173
   ```
3. **更新配置与重启**：
   复制终端输出的公网地址（形如 `https://xxxxxx.cpolar.top`），修改 `meeting-room-inspection-backend/.env` 中的 `FRONTEND_URL`，并重启后端：
   ```bash
   docker compose up -d backend
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
