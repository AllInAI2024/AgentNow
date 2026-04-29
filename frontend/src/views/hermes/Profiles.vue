<template>
  <MainLayout>
    <div class="hermes-page">
      <div class="page-header">
        <div class="header-left">
          <ApartmentOutlined class="page-icon" />
          <div class="header-title">
            <h1>Profiles 管理</h1>
            <p class="subtitle">Hermes 多实例管理与状态监控</p>
          </div>
        </div>
        <div class="header-right">
          <a-button type="primary" @click="handleRefresh">
            <ReloadOutlined /> 刷新
          </a-button>
        </div>
      </div>

      <div class="page-content">
        <a-card class="empty-card">
          <a-empty description="Profiles 管理功能开发中...">
            <template #image>
              <ApartmentOutlined class="empty-icon" />
            </template>
            <a-button type="primary">了解更多</a-button>
          </a-empty>
        </a-card>
      </div>
    </div>
  </MainLayout>
</template>

<script setup lang="ts">
import { message } from 'ant-design-vue'
import {
  ApartmentOutlined,
  ReloadOutlined,
} from '@ant-design/icons-vue'
import MainLayout from '@/components/MainLayout.vue'

const handleRefresh = () => {
  message.info('刷新功能开发中...')
}
</script>

<style scoped>
.hermes-page {
  min-height: 100%;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.page-icon {
  font-size: 32px;
  color: #165DFF;
}

.header-title h1 {
  font-size: 24px;
  font-weight: 600;
  color: #1d2129;
  margin: 0;
  line-height: 1.4;
}

.subtitle {
  font-size: 14px;
  color: #86909c;
  margin: 4px 0 0 0;
}

.empty-card {
  padding: 60px 24px;
}

.empty-icon {
  font-size: 72px;
  color: #c9cdd4;
}
</style>
