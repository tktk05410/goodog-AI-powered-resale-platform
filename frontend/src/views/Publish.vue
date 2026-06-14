<template>
  <div class="publish-page">
    <header class="header">
      <div class="header-content">
        <h1 class="logo" @click="$router.push('/')">goodog <span class="chinese-name">闲狗</span></h1>
      </div>
    </header>

    <div class="main-content">
      <h2>发布商品</h2>
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="商品类型" prop="type">
          <el-radio-group v-model="form.type">
            <el-radio label="sell">出售</el-radio>
            <el-radio label="buy">求购</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="商品标题" prop="title">
          <el-input v-model="form.title" placeholder="请输入商品标题" maxlength="100" show-word-limit @input="triggerPriceEstimate" />
        </el-form-item>

        <el-form-item label="商品描述" prop="description">
          <div class="description-area">
            <el-input
              v-model="form.description"
              type="textarea"
              placeholder="请详细描述商品信息"
              :rows="6"
              maxlength="1000"
              show-word-limit
              @input="triggerPriceEstimate"
            />
            <el-button
              type="warning"
              size="small"
              :loading="copywritingGenerating"
              @click="generateCopywriting"
              class="ai-copywriting-btn"
            >
              {{ copywritingGenerating ? '生成中...' : '✨ AI文案' }}
            </el-button>
          </div>
        </el-form-item>

        <el-form-item label="成色" v-if="form.type === 'sell'" class="condition-item">
          <el-radio-group v-model="form.condition" @change="handleConditionChange">
            <el-radio-button value="全新未拆封">全新未拆封</el-radio-button>
            <el-radio-button value="几乎全新">几乎全新</el-radio-button>
            <el-radio-button value="轻微使用痕迹">轻微使用痕迹</el-radio-button>
            <el-radio-button value="中度使用痕迹">中度使用痕迹</el-radio-button>
            <el-radio-button value="严重使用痕迹">严重使用痕迹</el-radio-button>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="商品图片">
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :limit="1"
            :on-change="handleFileChange"
            :file-list="fileList"
            list-type="picture-card"
            accept="image/*"
          >
            <el-icon><Plus /></el-icon>
          </el-upload>
        </el-form-item>

        <el-form-item label="商品价格" prop="price" v-if="form.type === 'sell'">
          <div class="price-area">
            <el-input-number v-model="form.price" :min="0" :precision="2" placeholder="请输入价格" />
            <div v-if="estimatedPrice" class="estimated-price">
              <span class="price-label">AI参考价格：</span>
              <span class="price-range">¥{{ estimatedPrice.min_price }} - ¥{{ estimatedPrice.max_price }}</span>
              <el-button size="small" type="primary" link @click="useEstimatedPrice">使用</el-button>
            </div>
          </div>
        </el-form-item>

        <el-form-item label="商品标签">
          <div class="tags-input-area">
            <div class="selected-tags">
              <el-tag
                v-for="tag in form.tags"
                :key="tag.id || tag.name"
                :color="tag.color || '#409eff'"
                style="color: white; margin: 4px;"
                closable
                @close="removeTag(tag)"
              >
                {{ tag.name }}
                <el-tag v-if="tag.is_ai_generated" size="small" type="info" style="margin-left: 4px; font-size: 10px;">AI</el-tag>
              </el-tag>
              <el-button size="small" @click="showTagDialog = true">+ 添加标签</el-button>
              <el-tag v-if="tagsGenerating" type="info" effect="plain" style="margin: 4px;">
                AI生成中...
              </el-tag>
            </div>
            <p class="tag-hint">AI将自动识别商品并生成标签，您也可以手动添加或删除</p>
          </div>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleSubmit" :loading="loading">发布</el-button>
          <el-button @click="$router.back()">取消</el-button>
        </el-form-item>
      </el-form>
    </div>

    <el-dialog v-model="showTagDialog" title="选择或创建标签" width="500px">
      <el-input
        v-model="newTagName"
        placeholder="输入新标签名称，按回车创建"
        @keyup.enter="createNewTag"
      >
        <template #append>
          <el-button @click="createNewTag">创建</el-button>
        </template>
      </el-input>
      <div class="existing-tags" v-if="availableTags.length > 0">
        <p>已有标签（点击选择）：</p>
        <div class="tags-container">
          <el-tag
            v-for="tag in availableTags"
            :key="tag.id"
            :color="tag.color"
            style="color: white; margin: 4px; cursor: pointer;"
            :type="isTagSelected(tag) ? 'primary' : 'info'"
            @click="selectTag(tag)"
          >
            {{ tag.name }}
          </el-tag>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { productAPI, aiAPI, tagAPI } from '@/api/modules'

const router = useRouter()

const formRef = ref(null)
const uploadRef = ref(null)
const loading = ref(false)
const fileList = ref([])
const showTagDialog = ref(false)
const newTagName = ref('')
const availableTags = ref([])
const estimatedPrice = ref(null)
const priceEstimating = ref(false)
const copywritingGenerating = ref(false)
const tagsGenerating = ref(false)
let priceEstimateTimer = null
const tagsGenerated = ref(false)

const form = reactive({
  type: 'sell',
  title: '',
  description: '',
  price: null,
  condition: '',
  tags: []
})

const rules = {
  type: [{ required: true, message: '请选择商品类型', trigger: 'change' }],
  title: [{ required: true, message: '请输入商品标题', trigger: 'blur' }],
  description: [{ required: true, message: '请输入商品描述', trigger: 'blur' }]
}

async function fetchAvailableTags() {
  try {
    const res = await tagAPI.getList({ per_page: 100 })
    availableTags.value = res.data.tags || []
  } catch (e) {
    console.error(e)
  }
}

async function handleFileChange(file) {
  fileList.value = [file]
  // 上传图片后自动调用 AI 标签生成，只生成一次
  if (!tagsGenerated.value) {
    await autoGenerateTags()
  }
}

async function autoGenerateTags() {
  if (!form.title || !form.description || tagsGenerated.value) {
    return
  }
  tagsGenerating.value = true
  try {
    const res = await aiAPI.generateTags({
      title: form.title,
      description: form.description
    })
    if (res.data.tags && res.data.tags.length > 0) {
      // 保留已有标签，添加新生成的标签（去重）
      const existingNames = new Set(form.tags.map(t => t.name))
      for (const tagName of res.data.tags) {
        if (!existingNames.has(tagName)) {
          form.tags.push({ name: tagName, color: '#409eff', is_ai_generated: true })
          existingNames.add(tagName)
        }
      }
      tagsGenerated.value = true
      ElMessage.success('AI标签已生成')
    }
  } catch (e) {
    console.error('Tag generation failed:', e)
  } finally {
    tagsGenerating.value = false
  }
}

function handleConditionChange(val) {
  // Remove existing condition tag
  const conditionTags = ['全新未拆封', '几乎全新', '轻微使用痕迹', '中度使用痕迹', '严重使用痕迹']
  form.tags = form.tags.filter(t => !conditionTags.includes(t.name))

  // Add new condition tag if selected
  if (val) {
    form.tags.push({ name: val, color: '#67c23a' })
  }

  // Trigger price estimation when condition changes
  triggerPriceEstimate()
}

function isTagSelected(tag) {
  return form.tags.some(t => t.id === tag.id || t.name === tag.name)
}

function selectTag(tag) {
  if (isTagSelected(tag)) {
    form.tags = form.tags.filter(t => t.id !== tag.id && t.name !== tag.name)
  } else {
    form.tags.push({ ...tag })
  }
}

function removeTag(tag) {
  form.tags = form.tags.filter(t => t.id !== tag.id && t.name !== tag.name)
}

async function createNewTag() {
  if (!newTagName.value.trim()) {
    ElMessage.warning('请输入标签名称')
    return
  }

  const tagName = newTagName.value.trim()
  if (form.tags.some(t => t.name === tagName)) {
    ElMessage.warning('标签已存在')
    return
  }

  form.tags.push({ name: tagName, color: '#409eff' })
  newTagName.value = ''
  ElMessage.success('标签已添加')
}

function triggerPriceEstimate() {
  if (priceEstimateTimer) {
    clearTimeout(priceEstimateTimer)
  }
  priceEstimateTimer = setTimeout(() => {
    if (form.title && form.description && form.condition) {
      estimatePrice()
    }
  }, 1000)
}

async function estimatePrice() {
  if (!form.title || !form.description || !form.condition) {
    return
  }
  priceEstimating.value = true
  try {
    const res = await aiAPI.estimatePrice({
      title: form.title,
      description: form.description,
      condition: form.condition
    })
    if (res.data.min_price && res.data.max_price) {
      estimatedPrice.value = res.data
    }
  } catch (e) {
    console.error('Price estimation failed:', e)
  } finally {
    priceEstimating.value = false
  }
}

function useEstimatedPrice() {
  if (estimatedPrice.value) {
    form.price = Math.round((estimatedPrice.value.min_price + estimatedPrice.value.max_price) / 2 * 100) / 100
    ElMessage.success('已使用AI参考价格')
  }
}

async function generateCopywriting() {
  if (!form.title || !form.description) {
    ElMessage.warning('请先填写商品标题和描述')
    return
  }

  copywritingGenerating.value = true
  try {
    const res = await aiAPI.generateCopywriting({
      title: form.title,
      description: form.description,
      condition: form.condition || ''
    })

    if (res.data.copywriting) {
      form.description = res.data.copywriting
      ElMessage.success('AI文案已生成')
    } else {
      ElMessage.error('文案生成失败，请重试')
    }
  } catch (e) {
    console.error('Copywriting generation failed:', e)
    ElMessage.error('文案生成失败，请检查网络后重试')
  } finally {
    copywritingGenerating.value = false
  }
}

async function handleSubmit() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    const formData = new FormData()
    formData.append('title', form.title)
    formData.append('description', form.description)
    formData.append('type', form.type)
    if (form.condition) {
      formData.append('condition', form.condition)
    }
    if (form.price) {
      formData.append('price', form.price)
    }
    if (fileList.value.length > 0) {
      formData.append('image', fileList.value[0].raw)
    }
    if (form.tags.length > 0) {
      formData.append('tags', JSON.stringify(form.tags.map(t => ({
        id: t.id || null,
        name: t.name,
        is_ai_generated: t.is_ai_generated || false
      }))))
    }

    const res = await productAPI.create(formData)
    const productId = res.data.product.id

    ElMessage.success('发布成功')
    router.push(`/product/${productId}`)
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchAvailableTags()
})
</script>

<style scoped>
.publish-page {
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

/* 主内容区 - 表单容器 */
.main-content {
  max-width: 860px;
  margin: var(--spacing-xl) auto;
  padding: var(--spacing-xl);
  background: var(--color-background);
  border-radius: var(--radius-xl);
  border: 1px solid var(--border-light);
  box-shadow: var(--shadow-sm);
}

.main-content h2 {
  margin-bottom: var(--spacing-xl);
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-extrabold);
  color: var(--text-primary);
  letter-spacing: -0.5px;
}

/* 成色选择器 */
.condition-item :deep(.el-form-item__content) {
  width: auto;
}

.condition-item :deep(.el-radio-group) {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-sm);
}

.condition-item :deep(.el-radio-button__inner) {
  padding: 10px 18px;
  border-radius: var(--radius-md) !important;
  border: 1.5px solid var(--border-color) !important;
  font-weight: var(--font-weight-medium) !important;
  box-shadow: none !important;
}

/* 价格区域 */
.price-area {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.estimated-price {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-md);
  background-color: #FAFAFA;
  border-radius: var(--radius-lg);
  font-size: var(--font-size-sm);
  border: 1px dashed var(--border-color);
}

.price-label {
  color: var(--text-secondary);
  font-weight: var(--font-weight-medium);
}

.price-range {
  color: var(--color-primary);
  font-weight: var(--font-weight-bold);
  font-size: var(--font-size-base);
}

/* 标签输入区域 */
.tags-input-area {
  width: 100%;
}

.selected-tags {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-xs);
  align-items: center;
}

.tag-hint {
  margin-top: var(--spacing-sm);
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);
}

.existing-tags {
  margin-top: var(--spacing-lg);
}

.existing-tags p {
  margin-bottom: var(--spacing-sm);
  color: var(--text-secondary);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
}

.tags-container {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-xs);
}

/* 描述区域 */
.description-area {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.ai-copywriting-btn {
  align-self: flex-end;
}
</style>
