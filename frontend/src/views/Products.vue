<template>
  <div class="products-page">
    <header class="header">
      <div class="header-content">
        <h1 class="logo" @click="$router.push('/')">goodog <span class="chinese-name">闲狗</span></h1>
        <div class="user-area">
          <template v-if="userStore.isLoggedIn">
            <span class="username">{{ userStore.userInfo?.username }}</span>
            <router-link to="/profile">个人中心</router-link>
          </template>
          <template v-else>
            <router-link to="/login">登录</router-link>
            <router-link to="/register">注册</router-link>
          </template>
        </div>
      </div>
    </header>

    <div class="main-content">
      <div class="search-bar">
        <el-input
          v-model="keyword"
          placeholder="搜索商品..."
          @keyup.enter="handleSearch"
          clearable
          style="width: 400px"
        >
          <template #append>
            <el-button @click="handleSearch">搜索</el-button>
          </template>
        </el-input>
      </div>

      <div class="filter-bar">
        <el-radio-group v-model="typeFilter" @change="handleFilterChange">
          <el-radio-button label="">全部</el-radio-button>
          <el-radio-button label="sell">出售</el-radio-button>
          <el-radio-button label="buy">求购</el-radio-button>
        </el-radio-group>
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
              <div class="product-tags" v-if="product.tags && product.tags.length > 0">
                <el-tag
                  v-for="tag in product.tags.slice(0, 3)"
                  :key="tag.id"
                  :color="tag.color"
                  size="small"
                  style="color: white; margin-right: 4px;"
                >
                  {{ tag.name }}
                </el-tag>
              </div>
              <p class="product-desc">{{ product.description }}</p>
              <div class="product-meta">
                <span class="product-price" v-if="product.price">¥{{ product.price }}</span>
                <span class="product-type" :class="product.type">
                  {{ product.type === 'sell' ? '出售' : '求购' }}
                </span>
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

onMounted(() => {
  fetchProducts()
})
</script>

<style scoped>
.products-page {
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

/* 搜索栏 */
.search-bar {
  margin-bottom: var(--spacing-xl);
}

.search-bar :deep(.el-input__wrapper) {
  background: var(--color-background);
  border-radius: var(--radius-lg) !important;
  padding: 14px 20px !important;
}

/* 搜索按钮 - 黑色实心风格 */
.search-bar :deep(.el-input-group__append) {
  background-color: var(--color-primary) !important;
  border-color: var(--color-primary) !important;
  border-radius: 0 var(--radius-lg) var(--radius-lg) 0 !important;
  padding: 0 !important;
  box-shadow: none !important;
}

.search-bar :deep(.el-input-group__append .el-button) {
  background: transparent !important;
  border: none !important;
  color: var(--text-inverse) !important;
  font-weight: var(--font-weight-semibold) !important;
  font-size: var(--font-size-base) !important;
  padding: 14px 32px !important;
  height: auto !important;
}

.search-bar :deep(.el-input-group__append:hover) {
  background-color: var(--color-primary-hover) !important;
  border-color: var(--color-primary-hover) !important;
}

/* 筛选栏 */
.filter-bar {
  margin-bottom: var(--spacing-xl);
}

.filter-bar :deep(.el-radio-group) {
  display: flex;
  gap: var(--spacing-sm);
}

.filter-bar :deep(.el-radio-button__inner) {
  border: 1.5px solid var(--border-color) !important;
  border-radius: var(--radius-md) !important;
  padding: 10px 24px !important;
  font-weight: var(--font-weight-medium) !important;
  color: var(--text-secondary) !important;
  background: transparent !important;
  box-shadow: none !important;
}

.filter-bar :deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
  background: var(--color-primary) !important;
  border-color: var(--color-primary) !important;
  color: var(--text-inverse) !important;
}

/* 商品网格 */
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

.product-tags {
  margin-bottom: var(--spacing-sm);
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
}

.product-type.sell {
  background: #F5F5F5;
  color: var(--text-primary);
}

.product-type.buy {
  background: #FFF9E6;
  color: #B8860B;
}

/* 分页器 */
.pagination {
  margin-top: var(--spacing-xl);
  justify-content: center;
}
</style>