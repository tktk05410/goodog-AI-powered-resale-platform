<template>
  <div class="register-page">
    <div class="register-card">
      <h2>注册</h2>
      <el-form :model="form" :rules="rules" ref="formRef" @submit.prevent="handleSubmit">
        <el-form-item prop="username">
          <el-input v-model="form.username" placeholder="用户名" />
        </el-form-item>
        <el-form-item prop="password">
          <el-input v-model="form.password" type="password" placeholder="密码" />
        </el-form-item>
        <el-form-item prop="confirmPassword">
          <el-input v-model="form.confirmPassword" type="password" placeholder="确认密码" />
        </el-form-item>
        <el-form-item prop="student_id">
          <el-input v-model="form.student_id" placeholder="学号（可选）" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" native-type="submit" :loading="loading" style="width: 100%">
            注册
          </el-button>
        </el-form-item>
      </el-form>
      <div class="register-footer">
        已有账号？<router-link to="/login">立即登录</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/store/user'

const router = useRouter()
const userStore = useUserStore()

const formRef = ref(null)
const loading = ref(false)

const form = reactive({
  username: '',
  password: '',
  confirmPassword: '',
  student_id: ''
})

const validateConfirmPassword = (rule, value, callback) => {
  if (value !== form.password) {
    callback(new Error('两次输入密码不一致'))
  } else {
    callback()
  }
}

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度在 3 到 20 个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少 6 个字符', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

async function handleSubmit() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    await userStore.register(form.username, form.password, form.student_id)
    ElMessage.success('注册成功')
    router.push('/')
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.register-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--color-background-page);
  padding: var(--spacing-lg);
}

.register-card {
  background: var(--color-background);
  padding: var(--spacing-xl);
  border-radius: var(--radius-xl);
  width: 440px;
  max-width: 100%;
  border: 1px solid var(--border-light);
  box-shadow: var(--shadow-lg);
}

.register-card h2 {
  text-align: center;
  margin-bottom: var(--spacing-xl);
  color: var(--text-primary);
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-extrabold);
  letter-spacing: -0.5px;
}

.register-footer {
  text-align: center;
  color: var(--text-tertiary);
  margin-top: var(--spacing-md);
  font-size: var(--font-size-sm);
}

.register-footer a {
  color: var(--color-primary);
  font-weight: var(--font-weight-semibold);
}
</style>