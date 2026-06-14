<template>
  <div class="login-page">
    <div class="login-card">
      <h2>登录</h2>
      <el-form :model="form" :rules="rules" ref="formRef" @submit.prevent="handleSubmit">
        <el-form-item prop="username">
          <el-input v-model="form.username" placeholder="用户名" />
        </el-form-item>
        <el-form-item prop="password">
          <el-input v-model="form.password" type="password" placeholder="密码" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" native-type="submit" :loading="loading" style="width: 100%">
            登录
          </el-button>
        </el-form-item>
      </el-form>
      <div class="login-footer">
        还没有账号？<router-link to="/register">立即注册</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/store/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const formRef = ref(null)
const loading = ref(false)

const form = reactive({
  username: '',
  password: ''
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

async function handleSubmit() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    await userStore.login(form.username, form.password)
    ElMessage.success('登录成功')
    const redirect = route.query.redirect || '/'
    router.push(redirect)
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--color-background-page);
  padding: var(--spacing-lg);
}

.login-card {
  background: var(--color-background);
  padding: var(--spacing-xl);
  border-radius: var(--radius-xl);
  width: 440px;
  max-width: 100%;
  border: 1px solid var(--border-light);
  box-shadow: var(--shadow-lg);
}

.login-card h2 {
  text-align: center;
  margin-bottom: var(--spacing-xl);
  color: var(--text-primary);
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-extrabold);
  letter-spacing: -0.5px;
}

.login-footer {
  text-align: center;
  color: var(--text-tertiary);
  margin-top: var(--spacing-md);
  font-size: var(--font-size-sm);
}

.login-footer a {
  color: var(--color-primary);
  font-weight: var(--font-weight-semibold);
}
</style>