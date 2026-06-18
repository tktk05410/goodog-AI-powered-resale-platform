<template>
  <div class="product-detail-page">
    <header class="header">
      <div class="header-content">
        <h1 class="logo" @click="$router.push('/products')">goodog <span class="chinese-name">闲狗</span></h1>
        <div class="user-area">
          <template v-if="userStore.isLoggedIn">
            <span class="username">{{ userStore.userInfo?.username }}</span>
            <router-link to="/messages" v-if="!userStore.isAdmin">消息</router-link>
            <router-link to="/messages" v-if="userStore.isAdmin">管理</router-link>
          </template>
          <template v-else>
            <router-link to="/login">登录</router-link>
            <router-link to="/register">注册</router-link>
          </template>
        </div>
      </div>
    </header>

    <div class="main-content" v-loading="loading">
      <el-empty v-if="!product && !loading" description="商品不存在" />

      <div class="product-detail" v-if="product">
        <div class="product-images">
          <div class="main-image">
            <img v-if="product.image_path" :src="`/uploads/${product.image_path}`" alt="">
            <div v-else class="no-image">暂无图片</div>
          </div>
        </div>

        <div class="product-info-card">
          <h1 class="product-title">{{ product.title }}</h1>
          <div class="product-meta">
            <el-tag v-if="product.type === 'sell'" type="success">出售</el-tag>
            <el-tag v-else type="warning">求购</el-tag>
            <el-tag v-if="product.status === 'on'" type="info">上架中</el-tag>
            <el-tag v-else-if="product.status === 'sold'" type="danger">已售出</el-tag>
            <el-tag v-else type="info">已下架</el-tag>
          </div>
          <div class="product-price" v-if="product.price">
            <span class="price-symbol">¥</span>
            <span class="price-value">{{ product.price }}</span>
          </div>
          <div class="product-price" v-else>
            <span class="price-value">价格待议</span>
          </div>

          <div class="product-tags" v-if="product.tags && product.tags.length > 0">
            <h3>商品标签</h3>
            <div class="tags-container">
              <el-tag
                v-for="tag in product.tags"
                :key="tag.id"
                :color="tag.color"
                style="color: white; margin: 4px;"
              >
                {{ tag.name }}
                <el-tag v-if="tag.is_ai_generated" size="small" type="info" style="margin-left: 4px; font-size: 10px;">AI</el-tag>
              </el-tag>
            </div>
          </div>

          <div class="product-description">
            <h3>商品描述</h3>
            <p>{{ product.description }}</p>
          </div>

          <div class="product-seller">
            <span>发布者：{{ product.publisher }}</span>
            <span>发布时间：{{ product.create_time }}</span>
          </div>

          <div class="product-actions">
            <template v-if="userStore.isLoggedIn && userStore.userInfo?.id !== product.user_id && product.status === 'on'">
              <template v-if="product.type === 'sell'">
                <el-button type="primary" @click="handleBuy">立即购买</el-button>
                <el-button @click="handleContact">联系卖家</el-button>
              </template>
              <template v-if="product.type === 'buy'">
                <el-button type="primary" @click="handleContact">我有这个商品</el-button>
                <el-button @click="handleContact">联系买家</el-button>
              </template>
            </template>
            <template v-if="userStore.userInfo?.id === product.user_id || userStore.isAdmin">
              <el-button @click="handleEdit">编辑</el-button>
              <el-button type="danger" @click="handleDelete">删除</el-button>
            </template>
          </div>
        </div>
      </div>
    </div>

    <!-- 支付沙盒对话框 -->
    <el-dialog v-model="showPayDialog" title="支付沙盒" width="420px" :close-on-click-modal="false" :show-close="!paying">
      <div class="pay-sandbox">
        <div class="pay-product-info">
          <p class="pay-product-title">{{ product?.title }}</p>
          <p class="pay-product-price">
            <span class="pay-price-symbol">¥</span>
            <span class="pay-price-value">{{ product?.price || '0.00' }}</span>
          </p>
        </div>
        <div class="pay-method">
          <p class="pay-label">选择支付方式</p>
          <el-radio-group v-model="payForm.method" class="pay-method-group">
            <el-radio-button label="alipay">
              <el-icon><Wallet /></el-icon> 支付宝
            </el-radio-button>
            <el-radio-button label="wechat">
              <el-icon><ChatDotRound /></el-icon> 微信支付
            </el-radio-button>
            <el-radio-button label="balance">
              <el-icon><Coin /></el-icon> 余额
            </el-radio-button>
          </el-radio-group>
        </div>
        <div class="pay-password">
          <p class="pay-label">支付密码</p>
          <el-input
            v-model="payForm.password"
            type="password"
            maxlength="6"
            placeholder="请输入6位支付密码"
            show-password
          />
          <p class="pay-hint">沙盒环境，任意6位密码均可支付成功</p>
        </div>
        <div class="pay-actions">
          <el-button @click="showPayDialog = false" :disabled="paying">取消</el-button>
          <el-button type="primary" @click="handlePay" :loading="paying">确认支付</el-button>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Wallet, ChatDotRound, Coin } from '@element-plus/icons-vue'
import { useUserStore } from '@/store/user'
import { productAPI, transactionAPI, messageAPI } from '@/api/modules'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const product = ref(null)
const loading = ref(false)
const showPayDialog = ref(false)
const paying = ref(false)
const currentTransactionId = ref(null)
const payForm = reactive({
  method: 'alipay',
  password: ''
})

async function fetchProduct() {
  loading.value = true
  try {
    const res = await productAPI.getById(route.params.id)
    product.value = res.data.product
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

async function handleBuy() {
  try {
    await ElMessageBox.confirm('确定要购买此商品吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    const res = await transactionAPI.create({ product_id: product.value.id })
    currentTransactionId.value = res.data.transaction.id
    payForm.method = 'alipay'
    payForm.password = ''
    showPayDialog.value = true
  } catch (e) {
    if (e !== 'cancel') {
      console.error(e)
    }
  }
}

async function handlePay() {
  if (!payForm.password || payForm.password.length !== 6) {
    ElMessage.warning('请输入6位支付密码')
    return
  }
  if (!currentTransactionId.value) {
    ElMessage.error('交易信息异常')
    return
  }
  paying.value = true
  try {
    // 模拟支付网络延迟
    await new Promise(resolve => setTimeout(resolve, 1500))
    await transactionAPI.pay(currentTransactionId.value)
    ElMessage.success(`支付成功（${getPayMethodLabel(payForm.method)}）`)
    showPayDialog.value = false
    fetchProduct()
  } catch (e) {
    console.error(e)
    ElMessage.error('支付失败，请重试')
  } finally {
    paying.value = false
  }
}

function getPayMethodLabel(method) {
  const map = {
    alipay: '支付宝',
    wechat: '微信支付',
    balance: '余额支付'
  }
  return map[method] || method
}

function handleContact() {
  router.push({ name: 'Messages', query: { to_user: product.value.user_id } })
}

function handleEdit() {
  router.push({ name: 'EditProduct', params: { id: product.value.id } })
}

async function handleDelete() {
  try {
    await ElMessageBox.confirm('确定要删除此商品吗？', '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await productAPI.delete(product.value.id)
    ElMessage.success('删除成功')
    router.push('/')
  } catch (e) {
    if (e !== 'cancel') {
      console.error(e)
    }
  }
}

onMounted(() => {
  fetchProduct()
})
</script>

<style scoped>
.product-detail-page {
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

/* ===================================
   商品详情 - 左右分栏布局
   =================================== */
.product-detail {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing-xl);
  background: var(--color-background);
  border-radius: var(--radius-xl);
  padding: var(--spacing-xl);
  border: 1px solid var(--border-light);
}

/* 左侧图片区域 */
.product-images .main-image {
  width: 100%;
  height: 500px;
  background: var(--color-background-alt);
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.product-images img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.no-image {
  color: var(--text-tertiary);
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-medium);
}

/* 右侧信息卡片 */
.product-info-card {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.product-title {
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-bold);
  color: var(--text-primary);
  line-height: 1.2;
  letter-spacing: -0.5px;
  margin-bottom: var(--spacing-xs);
}

.product-meta {
  display: flex;
  gap: var(--spacing-sm);
  flex-wrap: wrap;
}

/* 价格展示 - NOMAD风格大字价格 */
.product-price {
  margin-bottom: var(--spacing-sm);
}

.price-symbol {
  font-size: var(--font-size-lg);
  color: var(--color-primary);
  font-weight: var(--font-weight-semibold);
}

.price-value {
  font-size: 48px;
  font-weight: var(--font-weight-extrabold);
  color: var(--color-primary);
  line-height: 1;
  letter-spacing: -1px;
}

/* 标签区域 */
.product-tags h3,
.product-description h3 {
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
  margin-bottom: var(--spacing-sm);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);
}

.tags-container {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-xs);
}

/* 描述文本 */
.product-description p {
  color: var(--text-secondary);
  line-height: 1.7;
  font-size: var(--font-size-base);
}

/* 卖家信息 */
.product-seller {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
  color: var(--text-tertiary);
  font-size: var(--font-size-sm);
  padding-top: var(--spacing-md);
  border-top: 1px solid var(--border-light);
}

/* 操作按钮组 */
.product-actions {
  display: flex;
  gap: var(--spacing-md);
  margin-top: auto;
  padding-top: var(--spacing-lg);
}

.product-actions :deep(.el-button) {
  flex: 1;
  padding: 16px !important;
  font-size: var(--font-size-base) !important;
  font-weight: var(--font-weight-semibold) !important;
  border-radius: var(--radius-lg) !important;
}

/* 支付对话框样式优化 */
.pay-sandbox {
  padding: var(--spacing-md);
}

.pay-product-info {
  text-align: center;
  margin-bottom: var(--spacing-xl);
  padding-bottom: var(--spacing-lg);
  border-bottom: 1px solid var(--border-light);
}

.pay-product-title {
  font-size: var(--font-size-md);
  color: var(--text-primary);
  margin-bottom: var(--spacing-sm);
  font-weight: var(--font-weight-medium);
}

.pay-product-price {
  color: var(--color-primary);
}

.pay-price-symbol {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
}

.pay-price-value {
  font-size: 42px;
  font-weight: var(--font-weight-extrabold);
  line-height: 1;
  letter-spacing: -1px;
}

.pay-label {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  margin-bottom: var(--spacing-sm);
  font-weight: var(--font-weight-medium);
}

.pay-method {
  margin-bottom: var(--spacing-lg);
}

.pay-method-group {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-sm);
}

.pay-password {
  margin-bottom: var(--spacing-lg);
}

.pay-hint {
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);
  margin-top: var(--spacing-xs);
}

.pay-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-md);
}
</style>
