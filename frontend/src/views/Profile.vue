<template>
  <div class="profile-page">
    <header class="header">
      <div class="header-content">
        <h1 class="logo" @click="$router.push('/products')">goodog <span class="chinese-name">闲狗</span></h1>
      </div>
    </header>

    <div class="main-content" v-loading="loading">
      <div class="profile-card" v-if="user">
        <div class="profile-header">
          <div class="avatar">{{ user.username?.charAt(0).toUpperCase() }}</div>
          <div class="user-info">
            <h2>{{ user.username }}</h2>
            <p>学号：{{ user.student_id || '未绑定' }}</p>
            <p>注册时间：{{ user.create_time }}</p>
          </div>
        </div>

        <div class="profile-stats">
          <div class="stat-item">
            <span class="stat-value">{{ user.credit_score }}</span>
            <span class="stat-label">信用分</span>
          </div>
          <div class="stat-item">
            <span class="stat-value">{{ stats.total_products }}</span>
            <span class="stat-label">发布商品</span>
          </div>
          <div class="stat-item">
            <span class="stat-value">{{ stats.completed_deals }}</span>
            <span class="stat-label">完成交易</span>
          </div>
        </div>

        <div class="profile-actions">
          <el-button @click="showEditDialog = true">编辑资料</el-button>
          <el-button @click="showPasswordDialog = true">修改密码</el-button>
          <el-button type="danger" plain @click="handleLogout">退出登录</el-button>
        </div>
      </div>

      <div class="my-products">
        <h3>我的商品</h3>
        <el-tabs v-model="activeTab">
          <el-tab-pane label="在售" name="on">
            <div class="product-list" v-if="onSaleProducts.length > 0">
              <div
                v-for="product in onSaleProducts"
                :key="product.id"
                class="product-item"
                @click="$router.push(`/product/${product.id}`)"
              >
                <div class="product-image">
                  <img v-if="product.image_path" :src="`/uploads/${product.image_path}`" alt="">
                  <div v-else class="no-image">暂无</div>
                </div>
                <div class="product-info">
                  <h4>{{ product.title }}</h4>
                  <p>{{ product.description }}</p>
                  <span class="product-price" v-if="product.price">¥{{ product.price }}</span>
                </div>
              </div>
            </div>
            <el-empty v-else description="暂无在售商品" />
          </el-tab-pane>
          <el-tab-pane label="已售出" name="sold">
            <div class="product-list" v-if="soldProducts.length > 0">
              <div
                v-for="product in soldProducts"
                :key="product.id"
                class="product-item"
                @click="$router.push(`/product/${product.id}`)"
              >
                <div class="product-image">
                  <img v-if="product.image_path" :src="`/uploads/${product.image_path}`" alt="">
                  <div v-else class="no-image">暂无</div>
                </div>
                <div class="product-info">
                  <h4>{{ product.title }}</h4>
                  <p>{{ product.description }}</p>
                  <span class="product-price" v-if="product.price">¥{{ product.price }}</span>
                </div>
              </div>
            </div>
            <el-empty v-else description="暂无已售商品" />
          </el-tab-pane>
        </el-tabs>
      </div>

      <div class="my-transactions">
        <h3>我的交易</h3>
        <el-tabs v-model="transactionTab">
          <el-tab-pane label="买入" name="buyer">
            <div class="transaction-list" v-if="buyerTransactions.length > 0">
              <div v-for="tx in buyerTransactions" :key="tx.id" class="transaction-item">
                <div class="tx-info">
                  <span class="tx-title">{{ tx.product?.title }}</span>
                  <span class="tx-price" v-if="tx.product?.price">¥{{ tx.product.price }}</span>
                </div>
                <div class="tx-actions">
                  <el-tag :type="getStateType(tx.state)">{{ getStateLabel(tx.state) }}</el-tag>
                  <el-button v-if="tx.state === 'pending'" type="primary" size="small" @click.stop="openPayDialog(tx)">去支付</el-button>
                  <el-button v-if="tx.state === 'pending'" size="small" @click.stop="handleCancelTx(tx.id)">取消</el-button>
                </div>
              </div>
            </div>
            <el-empty v-else description="暂无买入记录" />
          </el-tab-pane>
          <el-tab-pane label="卖出" name="seller">
            <div class="transaction-list" v-if="sellerTransactions.length > 0">
              <div v-for="tx in sellerTransactions" :key="tx.id" class="transaction-item">
                <div class="tx-info">
                  <span class="tx-title">{{ tx.product?.title }}</span>
                  <span class="tx-price" v-if="tx.product?.price">¥{{ tx.product.price }}</span>
                </div>
                <div class="tx-actions">
                  <el-tag :type="getStateType(tx.state)">{{ getStateLabel(tx.state) }}</el-tag>
                  <el-button v-if="tx.state === 'paid'" type="success" size="small" @click.stop="handleConfirmTx(tx.id)">确认收款</el-button>
                </div>
              </div>
            </div>
            <el-empty v-else description="暂无卖出记录" />
          </el-tab-pane>
        </el-tabs>
      </div>
    </div>

    <el-dialog v-model="showEditDialog" title="编辑资料" width="400px">
      <el-form :model="editForm" label-width="80px">
        <el-form-item label="学号">
          <el-input v-model="editForm.student_id" placeholder="请输入学号" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" @click="handleEditProfile">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showPasswordDialog" title="修改密码" width="400px">
      <el-form :model="passwordForm" label-width="80px">
        <el-form-item label="旧密码">
          <el-input v-model="passwordForm.old_password" type="password" />
        </el-form-item>
        <el-form-item label="新密码">
          <el-input v-model="passwordForm.new_password" type="password" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showPasswordDialog = false">取消</el-button>
        <el-button type="primary" @click="handleChangePassword">保存</el-button>
      </template>
    </el-dialog>

    <!-- 支付沙盒对话框 -->
    <el-dialog v-model="showPayDialog" title="支付沙盒" width="420px" :close-on-click-modal="false" :show-close="!paying">
      <div class="pay-sandbox">
        <div class="pay-product-info">
          <p class="pay-product-title">{{ currentTx?.product?.title }}</p>
          <p class="pay-product-price">
            <span class="pay-price-symbol">¥</span>
            <span class="pay-price-value">{{ currentTx?.product?.price || '0.00' }}</span>
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
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Wallet, ChatDotRound, Coin } from '@element-plus/icons-vue'
import { useUserStore } from '@/store/user'
import { userAPI, productAPI, transactionAPI, authAPI } from '@/api/modules'

const router = useRouter()
const userStore = useUserStore()

const loading = ref(false)
const showEditDialog = ref(false)
const showPasswordDialog = ref(false)
const showPayDialog = ref(false)
const paying = ref(false)
const activeTab = ref('on')
const transactionTab = ref('buyer')
const currentTx = ref(null)
const payForm = reactive({
  method: 'alipay',
  password: ''
})

const user = ref(null)
const myProducts = ref([])
const buyerTransactions = ref([])
const sellerTransactions = ref([])
const stats = reactive({
  total_products: 0,
  completed_deals: 0
})

const editForm = reactive({
  student_id: ''
})

const passwordForm = reactive({
  old_password: '',
  new_password: ''
})

async function fetchProfile() {
  try {
    const res = await userAPI.getProfile()
    user.value = res.data.user
    editForm.student_id = user.value.student_id || ''
  } catch (e) {
    console.error(e)
  }
}

async function fetchMyProducts() {
  try {
    const res = await productAPI.getMyProducts({ per_page: 100 })
    myProducts.value = res.data.products
    stats.total_products = res.data.total
  } catch (e) {
    console.error(e)
  }
}

const onSaleProducts = computed(() => myProducts.value.filter(p => p.status === 'on'))
const soldProducts = computed(() => myProducts.value.filter(p => p.status === 'sold'))

async function fetchTransactions() {
  try {
    const res = await transactionAPI.getList({ role: 'buyer', per_page: 100 })
    buyerTransactions.value = res.data.transactions
  } catch (e) {
    console.error(e)
  }

  try {
    const res = await transactionAPI.getList({ role: 'seller', per_page: 100 })
    sellerTransactions.value = res.data.transactions
    stats.completed_deals = res.data.transactions.filter(t => t.state === 'done').length
  } catch (e) {
    console.error(e)
  }
}

async function handleEditProfile() {
  try {
    await userAPI.updateProfile({ student_id: editForm.student_id })
    ElMessage.success('修改成功')
    showEditDialog.value = false
    fetchProfile()
  } catch (e) {
    console.error(e)
  }
}

async function handleChangePassword() {
  try {
    await authAPI.changePassword(passwordForm)
    ElMessage.success('密码修改成功')
    showPasswordDialog.value = false
    passwordForm.old_password = ''
    passwordForm.new_password = ''
  } catch (e) {
    console.error(e)
  }
}

function handleLogout() {
  userStore.logout()
  ElMessage.success('已退出登录')
  router.push('/products')
}

function getStateType(state) {
  const map = {
    pending: 'warning',
    paid: 'primary',
    done: 'success',
    canceled: 'info'
  }
  return map[state] || 'info'
}

function getStateLabel(state) {
  const map = {
    pending: '待付款',
    paid: '已付款',
    done: '已完成',
    canceled: '已取消'
  }
  return map[state] || state
}

function openPayDialog(tx) {
  currentTx.value = tx
  payForm.method = 'alipay'
  payForm.password = ''
  showPayDialog.value = true
}

async function handlePay() {
  if (!payForm.password || payForm.password.length !== 6) {
    ElMessage.warning('请输入6位支付密码')
    return
  }
  if (!currentTx.value) {
    ElMessage.error('交易信息异常')
    return
  }
  paying.value = true
  try {
    await new Promise(resolve => setTimeout(resolve, 1500))
    await transactionAPI.pay(currentTx.value.id)
    ElMessage.success('支付成功')
    showPayDialog.value = false
    fetchTransactions()
  } catch (e) {
    console.error(e)
    ElMessage.error('支付失败')
  } finally {
    paying.value = false
  }
}

async function handleCancelTx(id) {
  try {
    await ElMessageBox.confirm('确定取消该交易吗？', '提示', { type: 'warning' })
    await transactionAPI.cancel(id)
    ElMessage.success('交易已取消')
    fetchTransactions()
  } catch (e) {
    if (e !== 'cancel') console.error(e)
  }
}

async function handleConfirmTx(id) {
  try {
    await ElMessageBox.confirm('确认已收到款项吗？', '提示', { type: 'success' })
    await transactionAPI.confirm(id)
    ElMessage.success('交易已完成')
    fetchTransactions()
  } catch (e) {
    if (e !== 'cancel') console.error(e)
  }
}

function getPayMethodLabel(method) {
  const map = { alipay: '支付宝', wechat: '微信支付', balance: '余额支付' }
  return map[method] || method
}

onMounted(() => {
  if (!userStore.isLoggedIn) {
    userStore.fetchUserInfo()
  }
  fetchProfile()
  fetchMyProducts()
  fetchTransactions()
})
</script>

<style scoped>
.profile-page {
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
}

.logo {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-extrabold);
  color: var(--color-primary);
  cursor: pointer;
  letter-spacing: -0.5px;
}

/* 主内容区 */
.main-content {
  max-width: 960px;
  margin: 0 auto;
  padding: var(--spacing-xl) var(--spacing-lg);
}

/* ===================================
   个人资料卡片
   =================================== */
.profile-card {
  background: var(--color-background);
  border-radius: var(--radius-xl);
  padding: var(--spacing-xl);
  margin-bottom: var(--spacing-xl);
  border: 1px solid var(--border-light);
}

.profile-header {
  display: flex;
  gap: var(--spacing-lg);
  margin-bottom: var(--spacing-xl);
  align-items: center;
}

.avatar {
  width: 96px;
  height: 96px;
  background: var(--color-primary);
  color: var(--text-inverse);
  border-radius: var(--radius-full);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 36px;
  font-weight: var(--font-weight-bold);
  flex-shrink: 0;
}

.user-info h2 {
  margin-bottom: var(--spacing-xs);
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-bold);
  color: var(--text-primary);
  letter-spacing: -0.3px;
}

.user-info p {
  color: var(--text-tertiary);
  margin-bottom: 4px;
  font-size: var(--font-size-sm);
}

/* 统计数据 */
.profile-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-xl);
  padding: var(--spacing-lg) 0;
  border-top: 1px solid var(--border-light);
  border-bottom: 1px solid var(--border-light);
}

.stat-item {
  text-align: center;
  padding: var(--spacing-sm);
}

.stat-value {
  display: block;
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-extrabold);
  color: var(--color-primary);
  line-height: 1;
  margin-bottom: var(--spacing-xs);
  letter-spacing: -1px;
}

.stat-label {
  color: var(--text-tertiary);
  font-size: var(--font-size-xs);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-weight: var(--font-weight-medium);
}

/* 操作按钮 */
.profile-actions {
  display: flex;
  gap: var(--spacing-md);
}

/* ===================================
   内容区块（商品、交易）
   =================================== */
.my-products,
.my-transactions {
  background: var(--color-background);
  border-radius: var(--radius-xl);
  padding: var(--spacing-xl);
  margin-bottom: var(--spacing-xl);
  border: 1px solid var(--border-light);
}

.my-products h3,
.my-transactions h3 {
  margin-bottom: var(--spacing-lg);
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-bold);
  color: var(--text-primary);
  letter-spacing: -0.3px;
}

/* 商品网格 */
.product-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: var(--spacing-md);
}

.product-item {
  border: 1px solid var(--border-light);
  border-radius: var(--radius-lg);
  padding: var(--spacing-md);
  cursor: pointer;
  transition: all 0.25s ease;
  background: var(--color-background);
}

.product-item:hover {
  border-color: var(--border-color);
  box-shadow: var(--shadow-sm);
  transform: translateY(-2px);
}

.product-image {
  height: 140px;
  background: var(--color-background-alt);
  border-radius: var(--radius-md);
  margin-bottom: var(--spacing-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.product-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.no-image {
  color: var(--text-tertiary);
  font-size: var(--font-size-xs);
}

.product-info h4 {
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-semibold);
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--text-primary);
}

.product-info p {
  font-size: var(--font-size-sm);
  color: var(--text-tertiary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-bottom: var(--spacing-xs);
}

.product-price {
  color: var(--color-primary);
  font-weight: var(--font-weight-bold);
  font-size: var(--font-size-md);
}

/* 交易列表 */
.transaction-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.transaction-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-md);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-lg);
  transition: all 0.25s ease;
  background: var(--color-background);
}

.transaction-item:hover {
  border-color: var(--border-color);
  box-shadow: var(--shadow-sm);
}

.tx-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.tx-title {
  font-size: var(--font-size-base);
  color: var(--text-primary);
  font-weight: var(--font-weight-medium);
}

.tx-price {
  font-size: var(--font-size-sm);
  color: var(--color-primary);
  font-weight: var(--font-weight-semibold);
}

.tx-actions {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
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