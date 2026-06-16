import api from './index'

export const authAPI = {
  login: (data) => api.post('/auth/login', data),
  register: (data) => api.post('/auth/register', data),
  getCurrentUser: () => api.get('/auth/me'),
  changePassword: (data) => api.post('/auth/change-password', data)
}

export const productAPI = {
  getList: (params) => api.get('/products/', { params }),
  getById: (id) => api.get(`/products/${id}`),
  create: (formData) => api.post('/products/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  update: (id, formData) => api.put(`/products/${id}`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  delete: (id) => api.delete(`/products/${id}`),
  getMyProducts: (params) => api.get('/products/my', { params })
}

export const transactionAPI = {
  getList: (params) => api.get('/transactions/', { params }),
  getById: (id) => api.get(`/transactions/${id}`),
  create: (data) => api.post('/transactions/', data),
  pay: (id) => api.post(`/transactions/${id}/pay`),
  confirm: (id) => api.post(`/transactions/${id}/confirm`),
  cancel: (id) => api.post(`/transactions/${id}/cancel`)
}

export const messageAPI = {
  getList: (params) => api.get('/messages/', { params }),
  getConversations: () => api.get('/messages/conversations'),
  send: (data) => api.post('/messages/', data),
  markAsRead: (id) => api.put(`/messages/${id}/read`),
  markAllAsRead: (userId) => api.put(`/messages/read-all/${userId}`),
  getUnreadCount: () => api.get('/messages/unread-count')
}

export const userAPI = {
  getById: (id) => api.get(`/users/${id}`),
  getProfile: () => api.get('/users/profile'),
  updateProfile: (data) => api.put('/users/profile', data),
  getCreditScore: (id) => api.get(`/users/credit-score/${id}`),
  getLeaderboard: (params) => api.get('/users/leaderboard', { params })
}

export const aiAPI = {
  classifyText: (data) => api.post('/ai/classify-text', data),
  preprocessImage: (formData) => api.post('/ai/preprocess-image', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  extractFeatures: (formData) => api.post('/ai/extract-features', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  searchByImage: (formData) => api.post('/ai/search-by-image', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  estimatePrice: (data) => api.post('/ai/estimate-price', data),
  generateCopywriting: (data) => api.post('/ai/generate-copywriting', data),
  generateTags: (data) => api.post('/ai/generate-tags', data)
}

export const statsAPI = {
  getOverview: () => api.get('/stats/overview'),
  getCategoryDistribution: () => api.get('/stats/category-distribution'),
  getProductStatus: () => api.get('/stats/product-status'),
  getTransactionStates: () => api.get('/stats/transaction-states'),
  getDailyTransactions: (params) => api.get('/stats/daily-transactions', { params }),
  getHourlyActivity: () => api.get('/stats/hourly-activity'),
  getTopProducts: (params) => api.get('/stats/top-products', { params }),
  getActiveUsers: (params) => api.get('/stats/active-users', { params })
}

export const logAPI = {
  getList: (params) => api.get('/logs/', { params }),
  getDistinctActions: () => api.get('/logs/actions'),
  getUserLogs: (userId, params) => api.get(`/logs/user/${userId}`, { params })
}

export const adminAPI = {
  getStats: () => api.get('/admin/stats'),
  getUsers: (params) => api.get('/admin/users', { params }),
  deleteUser: (id) => api.delete(`/admin/users/${id}`),
  getAllProducts: (params) => api.get('/admin/products', { params }),
  getLogs: (params) => api.get('/admin/logs', { params })
}

export const tagAPI = {
  getList: (params) => api.get('/tags/', { params }),
  getById: (id) => api.get(`/tags/${id}`),
  create: (data) => api.post('/tags/', data),
  update: (id, data) => api.put(`/tags/${id}`, data),
  delete: (id) => api.delete(`/tags/${id}`),
  getProductTags: (productId) => api.get(`/tags/products/${productId}`),
  addProductTag: (productId, data) => api.post(`/tags/products/${productId}`, data),
  removeProductTag: (productId, tagId) => api.delete(`/tags/products/${productId}/tags/${tagId}`),
  updateProductTags: (productId, data) => api.put(`/tags/products/${productId}/tags`, data)
}