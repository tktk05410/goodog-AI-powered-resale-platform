<template>
  <div class="home-page">
    <header class="header">
      <div class="header-content">
        <h1 class="logo" @click="$router.push('/')">goodog <span class="chinese-name">闲狗</span></h1>
        <nav class="nav">
          <router-link to="/products">商品</router-link>
          <router-link to="/messages" v-if="userStore.isLoggedIn">消息</router-link>
          <router-link to="/stats" v-if="userStore.isLoggedIn">统计</router-link>
        </nav>
        <div class="user-area">
          <template v-if="userStore.isLoggedIn">
            <span class="username">{{ userStore.userInfo?.username }}</span>
            <router-link to="/profile">个人中心</router-link>
            <button @click="handleLogout">退出</button>
          </template>
          <template v-else>
            <router-link to="/login">登录</router-link>
            <router-link to="/register">注册</router-link>
          </template>
        </div>
      </div>
    </header>

    <div class="main-content">
      <!-- 搜索栏 - 独立圆角搜索框 -->
      <div class="search-bar">
        <el-input
          v-model="keyword"
          placeholder="搜索商品..."
          @keyup.enter="handleSearch"
          clearable
          class="search-input"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
      </div>

      <!-- 筛选器 + 发布商品按钮 同行 -->
      <div class="toolbar">
        <div class="categories">
          <el-radio-group v-model="typeFilter" @change="handleFilterChange">
            <el-radio-button label="">全部</el-radio-button>
            <el-radio-button label="sell">出售</el-radio-button>
            <el-radio-button label="buy">求购</el-radio-button>
          </el-radio-group>
        </div>
        <el-button type="primary" class="publish-btn" @click="$router.push('/publish')" v-if="userStore.isLoggedIn">
          发布商品
        </el-button>
      </div>

      <div class="product-list" v-loading="loading">
        <el-empty v-if="products.length === 0 && !loading" description="暂无商品" />
        <div class="product-grid">
          <div
            v-for="product in products"
            :key="product.id"
            class="product-card"
            @click="$router.push(`/product/${product.id}`)"
          >
            <div class="product-image">
              <img v-if="product.image_path" :src="`/uploads/${product.image_path}`" alt="">
              <div v-else class="no-image">暂无图片</div>
            </div>
            <div class="product-info">
              <h3 class="product-title">{{ product.title }}</h3>
              <p class="product-desc">{{ product.description }}</p>
              <div class="product-meta">
                <span class="product-price" v-if="product.price">¥{{ product.price }}</span>
                <span class="product-type" :class="product.type">
                  {{ product.type === 'sell' ? '出售' : '求购' }}
                </span>
                <span class="product-user">{{ product.publisher }}</span>
              </div>
            </div>
          </div>
        </div>
        <el-pagination
          v-if="total > 0"
          class="pagination"
          :current-page="page"
          :page-size="perPage"
          :total="total"
          @current-change="handlePageChange"
          layout="prev, pager, next"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import { useUserStore } from '@/store/user'
import { productAPI } from '@/api/modules'

const router = useRouter()
const userStore = useUserStore()

const keyword = ref('')
const typeFilter = ref('')
const products = ref([])
const loading = ref(false)
const page = ref(1)
const perPage = ref(12)
const total = ref(0)

async function fetchProducts() {
  loading.value = true
  try {
    const res = await productAPI.getList({
      page: page.value,
      per_page: perPage.value,
      type: typeFilter.value,
      keyword: keyword.value
    })
    products.value = res.data.products
    total.value = res.data.total
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  page.value = 1
  fetchProducts()
}

function handleFilterChange() {
  page.value = 1
  fetchProducts()
}

function handlePageChange(newPage) {
  page.value = newPage
  fetchProducts()
}

async function handleLogout() {
  userStore.logout()
  ElMessage.success('已退出登录')
  router.push('/')
}

onMounted(() => {
  fetchProducts()
  if (userStore.isLoggedIn && !userStore.userInfo) {
    userStore.fetchUserInfo()
  }
})
</script>

<style scoped>
.home-page {
  min-height: 100vh;
  background-color: var(--color-background-page);
}

/* ===================================
   导航栏 - NOMAD极简风格
   =================================== */
.header {
  background: var(--color-background);
  border-bottom: 1px solid var(--border-light);
  position: sticky;
  top: 0;
  z-index: 100;
  backdrop-filter: blur(10px);
  background: rgba(255, 255, 255, 0.95);
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
  transition: opacity 0.25s ease;
}

.logo:hover {
  opacity: 0.7;
}

.nav {
  display: flex;
  gap: var(--spacing-lg);
}

.nav a {
  color: var(--text-secondary);
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-medium);
  padding: 8px 0;
  position: relative;
  transition: color 0.25s ease;
}

.nav a::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  width: 0;
  height: 2px;
  background: var(--color-primary);
  transition: width 0.25s ease;
}

.nav a:hover,
.nav a.router-link-active {
  color: var(--color-primary);
}

.nav a:hover::after,
.nav a.router-link-active::after {
  width: 100%;
}

.user-area {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.username {
  color: var(--text-primary);
  font-weight: var(--font-weight-semibold);
  font-size: var(--font-size-sm);
}

/* ===================================
   主内容区域
   =================================== */
.main-content {
  max-width: var(--max-width);
  margin: 0 auto;
  padding: var(--spacing-xl) var(--spacing-lg);
}

/* ===================================
   搜索栏 - 独立圆角矩形
   =================================== */
.search-bar {
  margin-bottom: var(--spacing-lg);
}

.search-input :deep(.el-input__wrapper) {
  background: var(--color-background);
  border-radius: var(--radius-xl) !important;
  padding: 16px 24px !important;
  box-shadow: var(--shadow-sm) !important;
  border: 1.5px solid var(--border-color) !important;
  transition: all 0.3s ease !important;
}

.search-input :deep(.el-input__wrapper:hover) {
  border-color: var(--text-tertiary) !important;
}

.search-input :deep(.el-input__wrapper.is-focus) {
  border-color: var(--color-primary) !important;
  box-shadow: var(--shadow-md), 0 0 0 4px rgba(0, 0, 0, 0.05) !important;
}

.search-input :deep(.el-input__inner) {
  font-size: var(--font-size-base);
  color: var(--text-primary);
}

.search-input :deep(.el-input__prefix .el-icon) {
  font-size: 18px;
  color: var(--text-tertiary);
}

/* ===================================
   工具栏 - 筛选器 + 发布按钮同行
   =================================== */
.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--spacing-xl);
}

.publish-btn {
  border-radius: var(--radius-lg) !important;
  padding: 12px 28px !important;
  font-weight: var(--font-weight-semibold) !important;
}

/* 分类筛选器 */
.categories {
  margin-bottom: 0;
}

.categories :deep(.el-radio-group) {
  display: flex;
  gap: var(--spacing-sm);
}

.categories :deep(.el-radio-button__inner) {
  border: 1.5px solid var(--border-color) !important;
  border-radius: var(--radius-md) !important;
  padding: 10px 24px !important;
  font-weight: var(--font-weight-medium) !important;
  color: var(--text-secondary) !important;
  background: transparent !important;
  box-shadow: none !important;
  transition: all 0.25s ease !important;
}

.categories :deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
  background: var(--color-primary) !important;
  border-color: var(--color-primary) !important;
  color: var(--text-inverse) !important;
  box-shadow: var(--shadow-sm) !important;
}

/* ===================================
   商品网格系统 - NOMAD卡片风格
   =================================== */
.product-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: var(--spacing-lg);
}

.product-card {
  background: var(--color-background);
  border-radius: var(--radius-lg);
  overflow: hidden;
  border: 1px solid var(--border-light);
  cursor: pointer;
  transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
}

.product-card:hover {
  transform: translateY(-6px);
  box-shadow: var(--shadow-lg);
  border-color: var(--border-color);
}

.product-image {
  height: 240px;
  background: var(--color-background-alt);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  position: relative;
}

.product-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.45s ease;
}

.product-card:hover .product-image img {
  transform: scale(1.05);
}

.no-image {
  color: var(--text-tertiary);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
}

.product-info {
  padding: var(--spacing-md);
}

.product-title {
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
  margin-bottom: var(--spacing-xs);
  line-height: 1.3;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.product-desc {
  font-size: var(--font-size-sm);
  color: var(--text-tertiary);
  margin-bottom: var(--spacing-sm);
  line-height: 1.5;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.product-meta {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  font-size: var(--font-size-sm);
}

.product-price {
  color: var(--color-primary);
  font-weight: var(--font-weight-bold);
  font-size: var(--font-size-md);
}

.product-type {
  padding: 4px 12px;
  border-radius: var(--radius-sm);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  letter-spacing: 0.3px;
}

.product-type.sell {
  background: #F5F5F5;
  color: var(--text-primary);
}

.product-type.buy {
  background: #FFF9E6;
  color: #B8860B;
}

.product-user {
  color: var(--text-tertiary);
  margin-left: auto;
}

/* 分页器 */
.pagination {
  margin-top: var(--spacing-xl);
  justify-content: center;
}

.pagination :deep(.el-pager li) {
  border-radius: var(--radius-sm);
  font-weight: var(--font-weight-medium);
}

.pagination :deep(.el-pager li.is-active) {
  background: var(--color-primary) !important;
}
</style>