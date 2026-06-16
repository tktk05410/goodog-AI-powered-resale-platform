<template>
  <div class="messages-page">
    <header class="header">
      <div class="header-content">
        <h1 class="logo" @click="$router.push('/products')">goodog <span class="chinese-name">闲狗</span></h1>
        <nav class="nav">
          <router-link to="/products">商品</router-link>
          <router-link to="/messages" v-if="userStore.isLoggedIn && !userStore.isAdmin">消息</router-link>
          <router-link to="/messages" v-if="userStore.isLoggedIn && userStore.isAdmin">管理</router-link>
          <router-link to="/stats" v-if="userStore.isLoggedIn">统计</router-link>
        </nav>
        <div class="user-area">
          <span class="username">{{ userStore.userInfo?.username }}</span>
          <router-link to="/profile">个人中心</router-link>
        </div>
      </div>
    </header>

    <!-- 管理员后台 -->
    <template v-if="userStore.isAdmin">
      <div class="main-content admin-content">
        <div class="admin-sidebar">
          <div
            v-for="item in adminMenu"
            :key="item.key"
            class="admin-menu-item"
            :class="{ active: activeAdminTab === item.key }"
            @click="activeAdminTab = item.key"
          >
            {{ item.label }}
          </div>
        </div>

        <div class="admin-panel">
          <!-- 数据概览 -->
          <template v-if="activeAdminTab === 'overview'">
            <h2 class="panel-title">数据概览</h2>
            <div class="stats-cards">
              <div class="stat-card">
                <div class="stat-value">{{ adminStats.total_users }}</div>
                <div class="stat-label">注册用户</div>
              </div>
              <div class="stat-card">
                <div class="stat-value">{{ adminStats.total_products }}</div>
                <div class="stat-label">商品总数</div>
              </div>
              <div class="stat-card">
                <div class="stat-value">{{ adminStats.online_products }}</div>
                <div class="stat-label">在售商品</div>
              </div>
              <div class="stat-card">
                <div class="stat-value">{{ adminStats.sold_products }}</div>
                <div class="stat-label">已售商品</div>
              </div>
              <div class="stat-card">
                <div class="stat-value">{{ adminStats.total_messages }}</div>
                <div class="stat-label">消息总数</div>
              </div>
            </div>
          </template>

          <!-- 用户管理 -->
          <template v-if="activeAdminTab === 'users'">
            <h2 class="panel-title">用户管理</h2>
            <el-table :data="adminUsers" style="width: 100%" v-loading="loading">
              <el-table-column prop="id" label="ID" width="60" />
              <el-table-column prop="username" label="用户名" />
              <el-table-column prop="student_id" label="学号" />
              <el-table-column prop="credit_score" label="信用分" width="90" />
              <el-table-column prop="role" label="角色" width="90" />
              <el-table-column prop="create_time" label="注册时间" />
              <el-table-column label="操作" width="120">
                <template #default="scope">
                  <el-button
                    v-if="scope.row.role !== 'admin'"
                    type="danger"
                    size="small"
                    @click="handleDeleteUser(scope.row)"
                  >删除</el-button>
                </template>
              </el-table-column>
            </el-table>
          </template>

          <!-- 商品管理 -->
          <template v-if="activeAdminTab === 'products'">
            <h2 class="panel-title">商品管理</h2>
            <el-table :data="adminProducts" style="width: 100%" v-loading="loading">
              <el-table-column prop="id" label="ID" width="60" />
              <el-table-column prop="title" label="标题" show-overflow-tooltip />
              <el-table-column prop="publisher" label="发布者" />
              <el-table-column prop="type" label="类型" width="80">
                <template #default="scope">
                  <el-tag v-if="scope.row.type === 'sell'" type="success">出售</el-tag>
                  <el-tag v-else type="warning">求购</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="price" label="价格" width="100">
                <template #default="scope">{{ scope.row.price ? '¥' + scope.row.price : '-' }}</template>
              </el-table-column>
              <el-table-column prop="status" label="状态" width="90">
                <template #default="scope">
                  <el-tag v-if="scope.row.status === 'on'" type="success">上架中</el-tag>
                  <el-tag v-else-if="scope.row.status === 'sold'" type="info">已售</el-tag>
                  <el-tag v-else type="danger">下架</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="create_time" label="发布时间" />
              <el-table-column label="操作" width="180">
                <template #default="scope">
                  <el-button size="small" @click="$router.push(`/product/${scope.row.id}/edit`)">编辑</el-button>
                  <el-button type="danger" size="small" @click="handleDeleteProduct(scope.row)">删除</el-button>
                </template>
              </el-table-column>
            </el-table>
          </template>

          <!-- 系统日志 -->
          <template v-if="activeAdminTab === 'logs'">
            <h2 class="panel-title">系统日志</h2>
            <el-table :data="adminLogs" style="width: 100%" v-loading="loading">
              <el-table-column prop="log_id" label="ID" width="80" />
              <el-table-column prop="action" label="操作" width="180" />
              <el-table-column prop="user_id" label="用户ID" width="90" />
              <el-table-column prop="detail" label="详情" show-overflow-tooltip />
              <el-table-column prop="timestamp" label="时间" />
            </el-table>
          </template>

          <!-- 消息中心 -->
          <template v-if="activeAdminTab === 'messages'">
            <h2 class="panel-title">消息中心</h2>
            <div class="messages-container" style="height: calc(100vh - 240px);">
              <div class="conversations-list">
                <h3>会话列表</h3>
                <div
                  v-for="conv in conversations"
                  :key="conv.user_id"
                  class="conversation-item"
                  :class="{ active: currentChatUser === conv.user_id }"
                  @click="selectConversation(conv)"
                >
                  <div class="conversation-user">
                    <span>{{ conv.username }}</span>
                    <el-badge :value="conv.unread_count" :hidden="conv.unread_count === 0" />
                  </div>
                  <div class="last-message" v-if="conv.last_message">
                    {{ conv.last_message.content }}
                  </div>
                </div>
                <el-empty v-if="conversations.length === 0" description="暂无会话" />
              </div>

              <div class="chat-area">
                <template v-if="currentChatUser">
                  <div class="chat-header">
                    <span>与 {{ currentUsername }} 的对话</span>
                  </div>
                  <div class="chat-messages" ref="messagesContainer">
                    <template v-for="(msg, index) in messages" :key="msg.id">
                      <div v-if="shouldShowTime(msg, index, messages)" class="message-timestamp">
                        {{ formatMessageTime(msg.create_time) }}
                      </div>
                      <div
                        class="message-item"
                        :class="{ own: userStore.userInfo && Number(msg.from_user) === Number(userStore.userInfo.id) }"
                      >
                        <div class="message-content">{{ msg.content }}</div>
                      </div>
                    </template>
                  </div>
                  <div class="chat-input">
                    <el-input
                      v-model="newMessage"
                      placeholder="输入消息..."
                      @keyup.enter="sendMessage"
                    />
                    <el-button type="primary" @click="sendMessage">发送</el-button>
                  </div>
                </template>
                <el-empty v-else description="选择一个会话开始聊天" />
              </div>
            </div>
          </template>
        </div>
      </div>
    </template>

    <!-- 普通用户消息界面 -->
    <template v-else>
      <div class="main-content">
        <div class="messages-container">
          <div class="conversations-list">
            <h3>会话列表</h3>
            <div
              v-for="conv in conversations"
              :key="conv.user_id"
              class="conversation-item"
              :class="{ active: currentChatUser === conv.user_id }"
              @click="selectConversation(conv)"
            >
              <div class="conversation-user">
                <span>{{ conv.username }}</span>
                <el-badge :value="conv.unread_count" :hidden="conv.unread_count === 0" />
              </div>
              <div class="last-message" v-if="conv.last_message">
                {{ conv.last_message.content }}
              </div>
            </div>
            <el-empty v-if="conversations.length === 0" description="暂无会话" />
          </div>

          <div class="chat-area">
            <template v-if="currentChatUser">
              <div class="chat-header">
                <span>与 {{ currentUsername }} 的对话</span>
              </div>
              <div class="chat-messages" ref="messagesContainer">
                <template v-for="(msg, index) in messages" :key="msg.id">
                  <div v-if="shouldShowTime(msg, index, messages)" class="message-timestamp">
                    {{ formatMessageTime(msg.create_time) }}
                  </div>
                  <div
                    class="message-item"
                    :class="{ own: userStore.userInfo && Number(msg.from_user) === Number(userStore.userInfo.id) }"
                  >
                    <div class="message-content">{{ msg.content }}</div>
                  </div>
                </template>
              </div>
              <div class="chat-input">
                <el-input
                  v-model="newMessage"
                  placeholder="输入消息..."
                  @keyup.enter="sendMessage"
                />
                <el-button type="primary" @click="sendMessage">发送</el-button>
              </div>
            </template>
            <el-empty v-else description="选择一个会话开始聊天" />
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useUserStore } from '@/store/user'
import { messageAPI, adminAPI, productAPI } from '@/api/modules'

const route = useRoute()
const userStore = useUserStore()

// 普通用户消息数据
const conversations = ref([])
const messages = ref([])
const currentChatUser = ref(null)
const currentUsername = ref('')
const newMessage = ref('')
const messagesContainer = ref(null)

// 管理员数据
const activeAdminTab = ref('overview')
const loading = ref(false)
const adminStats = ref({})
const adminUsers = ref([])
const adminProducts = ref([])
const adminLogs = ref([])

const adminMenu = [
  { key: 'overview', label: '数据概览' },
  { key: 'users', label: '用户管理' },
  { key: 'products', label: '商品管理' },
  { key: 'logs', label: '系统日志' },
  { key: 'messages', label: '消息中心' }
]

function formatMessageTime(timeStr) {
  if (!timeStr) return ''
  const match = timeStr.match(/(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2}):\d{2}/)
  if (!match) return timeStr
  const msgDate = new Date(match[1], match[2] - 1, match[3])
  const now = new Date()
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  const yesterday = new Date(today.getTime() - 24 * 60 * 60 * 1000)
  const msgTime = `${match[4]}:${match[5]}`
  if (msgDate.getTime() === today.getTime()) {
    return msgTime
  } else if (msgDate.getTime() === yesterday.getTime()) {
    return `昨天 ${msgTime}`
  } else {
    return `${match[2]}-${match[3]} ${msgTime}`
  }
}

function shouldShowTime(msg, index, messages) {
  if (index === 0) return true
  const currentTime = new Date(msg.create_time.replace(/-/g, '/'))
  const prevTime = new Date(messages[index - 1].create_time.replace(/-/g, '/'))
  const diffMinutes = Math.abs((currentTime - prevTime) / (1000 * 60))
  return diffMinutes >= 15
}

async function fetchConversations() {
  try {
    const res = await messageAPI.getConversations()
    conversations.value = res.data.conversations
  } catch (e) {
    console.error(e)
  }
}

async function selectConversation(conv) {
  currentChatUser.value = conv.user_id
  currentUsername.value = conv.username
  try {
    await messageAPI.markAllAsRead(conv.user_id)
    conv.unread_count = 0
  } catch (e) {
    console.error(e)
  }
  await fetchMessages()
}

async function fetchMessages() {
  if (!currentChatUser.value) return
  try {
    const res = await messageAPI.getList({ with_user: currentChatUser.value })
    messages.value = res.data.messages.reverse()
    scrollToBottom()
  } catch (e) {
    console.error(e)
  }
}

async function sendMessage() {
  if (!newMessage.value.trim() || !currentChatUser.value) return
  try {
    const res = await messageAPI.send({
      to_user: currentChatUser.value,
      content: newMessage.value
    })
    messages.value.push(res.data.data)
    newMessage.value = ''
    scrollToBottom()
  } catch (e) {
    console.error(e)
  }
}

function scrollToBottom() {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

// 管理员功能
async function fetchAdminStats() {
  try {
    const res = await adminAPI.getStats()
    adminStats.value = res.data
  } catch (e) {
    console.error(e)
  }
}

async function fetchAdminUsers() {
  loading.value = true
  try {
    const res = await adminAPI.getUsers()
    adminUsers.value = res.data.users
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

async function fetchAdminProducts() {
  loading.value = true
  try {
    const res = await adminAPI.getAllProducts()
    adminProducts.value = res.data.products
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

async function fetchAdminLogs() {
  loading.value = true
  try {
    const res = await adminAPI.getLogs()
    adminLogs.value = res.data.logs
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

async function handleDeleteUser(row) {
  try {
    await ElMessageBox.confirm(`确定删除用户 "${row.username}" 吗？`, '警告', { type: 'warning' })
    await adminAPI.deleteUser(row.id)
    ElMessage.success('删除成功')
    await fetchAdminUsers()
  } catch (e) {
    if (e !== 'cancel') console.error(e)
  }
}

async function handleDeleteProduct(row) {
  try {
    await ElMessageBox.confirm(`确定删除商品 "${row.title}" 吗？`, '警告', { type: 'warning' })
    await productAPI.delete(row.id)
    ElMessage.success('删除成功')
    await fetchAdminProducts()
  } catch (e) {
    if (e !== 'cancel') console.error(e)
  }
}

onMounted(async () => {
  await userStore.fetchUserInfo()

  if (userStore.isAdmin) {
    await fetchAdminStats()
    await fetchAdminUsers()
    await fetchAdminProducts()
    await fetchAdminLogs()
  }

  // 所有用户都加载消息数据（管理员在消息中心也需要）
  await fetchConversations()
  if (route.query.to_user) {
    const toUserId = parseInt(route.query.to_user)
    currentChatUser.value = toUserId
    const conv = conversations.value.find(c => c.user_id === toUserId)
    if (conv) {
      currentUsername.value = conv.username
    } else {
      currentUsername.value = `用户${toUserId}`
    }
    await fetchMessages()
  }
})
</script>

<style scoped>
.messages-page {
  min-height: 100vh;
  background-color: var(--color-background-page);
}

/* 导航栏 */
.header {
  background: rgba(255, 255, 255, 0.95);
  border-bottom: 1px solid var(--border-light);
  backdrop-filter: blur(10px);
}

.header-content {
  max-width: var(--max-width);
  margin: 0 auto;
  padding: 0 var(--spacing-lg);
  height: var(--header-height);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.logo {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-extrabold);
  color: var(--color-primary);
  cursor: pointer;
  letter-spacing: -0.5px;
}

.nav {
  display: flex;
  gap: var(--spacing-lg);
}

.nav a {
  color: var(--text-secondary);
  text-decoration: none;
  font-weight: var(--font-weight-medium);
  position: relative;
  padding: var(--spacing-xs) 0;
}

.nav a:hover {
  color: var(--color-primary);
}

.nav a:hover::after {
  width: 100%;
}

.nav a.router-link-active {
  background: var(--color-primary);
  color: var(--text-inverse);
  border-radius: var(--radius-lg);
  padding: 6px 16px;
}

.nav a.router-link-active::after {
  display: none;
}

.user-area {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

/* 主内容区 */
.main-content {
  max-width: var(--max-width);
  margin: 0 auto;
  padding: var(--spacing-xl) var(--spacing-lg);
}

/* 管理员后台布局 */
.admin-content {
  display: grid;
  grid-template-columns: 200px 1fr;
  gap: var(--spacing-lg);
}

.admin-sidebar {
  background: var(--color-background);
  border-radius: var(--radius-xl);
  padding: var(--spacing-md);
  border: 1px solid var(--border-light);
  height: fit-content;
}

.admin-menu-item {
  padding: var(--spacing-sm) var(--spacing-md);
  border-radius: var(--radius-md);
  cursor: pointer;
  margin-bottom: var(--spacing-xs);
  font-weight: var(--font-weight-medium);
  color: var(--text-secondary);
  transition: all 0.2s ease;
}

.admin-menu-item:hover {
  background: var(--color-background-alt);
  color: var(--text-primary);
}

.admin-menu-item.active {
  background: var(--color-primary);
  color: var(--text-inverse);
}

.admin-panel {
  background: var(--color-background);
  border-radius: var(--radius-xl);
  padding: var(--spacing-xl);
  border: 1px solid var(--border-light);
  min-height: 600px;
}

.panel-title {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-bold);
  margin-bottom: var(--spacing-lg);
  color: var(--text-primary);
}

/* 统计卡片 */
.stats-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: var(--spacing-lg);
}

.stat-card {
  background: var(--color-background-alt);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  text-align: center;
  border: 1px solid var(--border-light);
}

.stat-value {
  font-size: 32px;
  font-weight: var(--font-weight-extrabold);
  color: var(--color-primary);
  margin-bottom: var(--spacing-xs);
}

.stat-label {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  font-weight: var(--font-weight-medium);
}

/* 消息容器布局 */
.messages-container {
  display: grid;
  grid-template-columns: 320px 1fr;
  gap: var(--spacing-lg);
  height: calc(100vh - var(--header-height) - var(--spacing-2xl));
}

/* 左侧会话列表 */
.conversations-list {
  background: var(--color-background);
  border-radius: var(--radius-xl);
  padding: var(--spacing-lg);
  overflow-y: auto;
  border: 1px solid var(--border-light);
}

.conversations-list h3 {
  margin-bottom: var(--spacing-lg);
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-bold);
  color: var(--text-primary);
  letter-spacing: -0.3px;
}

.conversation-item {
  padding: var(--spacing-md);
  border-radius: var(--radius-md);
  cursor: pointer;
  margin-bottom: var(--spacing-sm);
  transition: all 0.25s ease;
  border: 1px solid transparent;
}

.conversation-item:hover {
  background: var(--color-background-alt);
  border-color: var(--border-light);
}

.conversation-item.active {
  background: #F5F5F5;
  border-color: var(--border-color);
}

.conversation-user {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-xs);
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
}

.last-message {
  font-size: var(--font-size-sm);
  color: var(--text-tertiary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 右侧聊天区域 */
.chat-area {
  background: var(--color-background);
  border-radius: var(--radius-xl);
  display: flex;
  flex-direction: column;
  border: 1px solid var(--border-light);
  overflow: hidden;
}

.chat-header {
  padding: var(--spacing-md) var(--spacing-lg);
  border-bottom: 1px solid var(--border-light);
  font-weight: var(--font-weight-semibold);
  font-size: var(--font-size-base);
  color: var(--text-primary);
  background: var(--color-background-alt);
}

.chat-messages {
  flex: 1;
  padding: var(--spacing-lg);
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

/* 消息气泡 */
.message-item {
  margin-bottom: var(--spacing-md);
  max-width: 70%;
  align-self: flex-start;
}

.message-item.own {
  align-self: flex-end;
  margin-right: 0;
}

.message-item.own .message-content {
  background: var(--color-primary);
  color: var(--text-inverse);
  border-radius: var(--radius-lg) var(--radius-lg) var(--radius-sm) var(--radius-lg);
}

.message-content {
  background: #F5F5F5;
  padding: var(--spacing-sm) var(--spacing-md);
  border-radius: var(--radius-lg) var(--radius-lg) var(--radius-lg) var(--radius-sm);
  word-break: break-word;
  display: inline-block;
  line-height: 1.6;
  font-size: var(--font-size-base);
  color: var(--text-primary);
}

/* 时间戳 */
.message-timestamp {
  text-align: center;
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);
  margin: var(--spacing-md) 0;
  font-weight: var(--font-weight-medium);
}

/* 输入框区域 */
.chat-input {
  padding: var(--spacing-md) var(--spacing-lg);
  border-top: 1px solid var(--border-light);
  display: flex;
  gap: var(--spacing-md);
  background: var(--color-background-alt);
}

.chat-input :deep(.el-input__wrapper) {
  border-radius: var(--radius-lg) !important;
}
</style>
