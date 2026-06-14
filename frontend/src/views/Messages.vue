<template>
  <div class="messages-page">
    <header class="header">
      <div class="header-content">
        <h1 class="logo" @click="$router.push('/')">goodog <span class="chinese-name">闲狗</span></h1>
        <div class="user-area">
          <span class="username">{{ userStore.userInfo?.username }}</span>
          <router-link to="/profile">个人中心</router-link>
        </div>
      </div>
    </header>

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
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/store/user'
import { messageAPI } from '@/api/modules'

const route = useRoute()
const userStore = useUserStore()

const conversations = ref([])
const messages = ref([])
const currentChatUser = ref(null)
const currentUsername = ref('')
const newMessage = ref('')
const messagesContainer = ref(null)

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

onMounted(async () => {
  await userStore.fetchUserInfo()
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

.message-time {
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);
  margin-top: var(--spacing-xs);
}

.message-item.own .message-time {
  text-align: right;
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