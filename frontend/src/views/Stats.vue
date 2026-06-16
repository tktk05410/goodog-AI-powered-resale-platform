<template>
  <div class="stats-page">
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

    <div class="main-content" v-loading="loading">
      <h2>数据统计</h2>

      <div class="overview-cards">
        <div class="overview-card">
          <div class="card-value">{{ overview.total_users }}</div>
          <div class="card-label">总用户数</div>
        </div>
        <div class="overview-card">
          <div class="card-value">{{ overview.total_products }}</div>
          <div class="card-label">商品总数</div>
        </div>
        <div class="overview-card">
          <div class="card-value">{{ overview.active_products }}</div>
          <div class="card-label">在售商品</div>
        </div>
        <div class="overview-card">
          <div class="card-value">{{ overview.completed_transactions }}</div>
          <div class="card-label">完成交易</div>
        </div>
      </div>

      <div class="charts-grid">
        <div class="chart-card">
          <h3>商品类别分布</h3>
          <div ref="categoryChartRef" class="chart"></div>
        </div>
        <div class="chart-card">
          <h3>商品状态分布</h3>
          <div ref="statusChartRef" class="chart"></div>
        </div>
        <div class="chart-card">
          <h3>交易状态分布</h3>
          <div ref="transactionChartRef" class="chart"></div>
        </div>
        <div class="chart-card">
          <h3>每日交易量</h3>
          <div ref="dailyChartRef" class="chart"></div>
        </div>
        <div class="chart-card full-width">
          <h3>用户活跃时段</h3>
          <div ref="hourlyChartRef" class="chart"></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import { useUserStore } from '@/store/user'
import { statsAPI } from '@/api/modules'

const userStore = useUserStore()

const loading = ref(false)
const overview = reactive({
  total_users: 0,
  total_products: 0,
  active_products: 0,
  completed_transactions: 0
})

const categoryChartRef = ref(null)
const statusChartRef = ref(null)
const transactionChartRef = ref(null)
const dailyChartRef = ref(null)
const hourlyChartRef = ref(null)

let categoryChart = null
let statusChart = null
let transactionChart = null
let dailyChart = null
let hourlyChart = null

async function fetchOverview() {
  try {
    const res = await statsAPI.getOverview()
    Object.assign(overview, res.data)
  } catch (e) {
    console.error(e)
  }
}

async function initCharts() {
  categoryChart = echarts.init(categoryChartRef.value)
  statusChart = echarts.init(statusChartRef.value)
  transactionChart = echarts.init(transactionChartRef.value)
  dailyChart = echarts.init(dailyChartRef.value)
  hourlyChart = echarts.init(hourlyChartRef.value)

  try {
    const categoryRes = await statsAPI.getCategoryDistribution()
    categoryChart.setOption({
      tooltip: { trigger: 'item' },
      legend: { bottom: 0 },
      series: [{
        type: 'pie',
        radius: '60%',
        data: categoryRes.data.distribution.map(item => ({
          name: item.name,
          value: item.value
        }))
      }]
    })

    const statusRes = await statsAPI.getProductStatus()
    statusChart.setOption({
      tooltip: { trigger: 'item' },
      legend: { bottom: 0 },
      series: [{
        type: 'pie',
        radius: '60%',
        data: statusRes.data.distribution.map(item => ({
          name: item.name,
          value: item.value
        }))
      }]
    })

    const txRes = await statsAPI.getTransactionStates()
    transactionChart.setOption({
      tooltip: { trigger: 'item' },
      legend: { bottom: 0 },
      series: [{
        type: 'pie',
        radius: '60%',
        data: txRes.data.distribution.map(item => ({
          name: item.name,
          value: item.value
        }))
      }]
    })

    const dailyRes = await statsAPI.getDailyTransactions({ days: 7 })
    dailyChart.setOption({
      tooltip: { trigger: 'axis' },
      xAxis: {
        type: 'category',
        data: dailyRes.data.data.map(item => item.date)
      },
      yAxis: { type: 'value' },
      series: [{
        type: 'bar',
        data: dailyRes.data.data.map(item => item.count)
      }]
    })

    const hourlyRes = await statsAPI.getHourlyActivity()
    hourlyChart.setOption({
      tooltip: { trigger: 'axis' },
      xAxis: {
        type: 'category',
        data: hourlyRes.data.data.map(item => `${item.hour}:00`)
      },
      yAxis: { type: 'value' },
      series: [{
        type: 'line',
        smooth: true,
        data: hourlyRes.data.data.map(item => item.count)
      }]
    })
  } catch (e) {
    console.error(e)
  }
}

function handleResize() {
  categoryChart?.resize()
  statusChart?.resize()
  transactionChart?.resize()
  dailyChart?.resize()
  hourlyChart?.resize()
}

onMounted(() => {
  if (!userStore.isLoggedIn) {
    userStore.fetchUserInfo()
  }
  loading.value = true
  fetchOverview().finally(() => {
    loading.value = false
    initCharts()
  })
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.stats-page {
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

.main-content h2 {
  margin-bottom: var(--spacing-xl);
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-extrabold);
  color: var(--text-primary);
  letter-spacing: -0.5px;
}

/* ===================================
   概览卡片网格
   =================================== */
.overview-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--spacing-lg);
  margin-bottom: var(--spacing-xl);
}

.overview-card {
  background: var(--color-background);
  padding: var(--spacing-lg);
  border-radius: var(--radius-xl);
  text-align: center;
  border: 1px solid var(--border-light);
  transition: all 0.25s ease;
}

.overview-card:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
}

.card-value {
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-extrabold);
  color: var(--color-primary);
  margin-bottom: var(--spacing-sm);
  line-height: 1;
  letter-spacing: -1px;
}

.card-label {
  color: var(--text-secondary);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* ===================================
   图表网格
   =================================== */
.charts-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--spacing-lg);
}

.chart-card {
  background: var(--color-background);
  padding: var(--spacing-lg);
  border-radius: var(--radius-xl);
  border: 1px solid var(--border-light);
  transition: all 0.25s ease;
}

.chart-card:hover {
  box-shadow: var(--shadow-sm);
}

.chart-card.full-width {
  grid-column: 1 / -1;
}

.chart-card h3 {
  margin-bottom: var(--spacing-md);
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);
}

.chart {
  height: 320px;
}
</style>