<template>
  <MainLayout>
    <div class="hermes-page">
      <div class="page-header">
        <div class="header-left">
          <ToolOutlined class="page-icon" />
          <div class="header-title">
            <h1>技能管理</h1>
            <p class="subtitle">Hermes 技能列表与详情管理</p>
          </div>
        </div>
        <div class="header-right">
          <a-button type="primary" @click="handleCreateSkill">
            <PlusOutlined /> 创建技能
          </a-button>
          <a-button @click="handleRefresh" :loading="loading">
            <ReloadOutlined /> 刷新
          </a-button>
        </div>
      </div>

      <div class="page-content">
        <div class="content-layout">
          <div class="sidebar">
            <a-card :bordered="false" class="sidebar-card">
              <div class="section-title">
                <AppstoreOutlined class="section-icon" />
                技能分类
              </div>
              <div class="category-list">
                <div 
                  :class="['category-item', { active: selectedCategory === '' }]"
                  @click="selectedCategory = ''"
                >
                  <span class="category-name">全部技能</span>
                  <span class="category-count">{{ totalSkillsCount }}</span>
                </div>
                <div 
                  v-for="cat in skillList?.categories || []" 
                  :key="cat.name"
                  :class="['category-item', { active: selectedCategory === cat.name }]"
                  @click="selectedCategory = cat.name"
                >
                  <span class="category-name">{{ cat.display_name }}</span>
                  <span class="category-count">{{ cat.skill_count }}</span>
                </div>
              </div>
            </a-card>

            <a-card :bordered="false" class="sidebar-card">
              <div class="section-title">
                <InfoCircleOutlined class="section-icon" />
                快捷操作
              </div>
              <div class="action-list">
                <a-button type="text" block @click="handleBrowseAvailable">
                  <CloudDownloadOutlined /> 浏览可用技能
                </a-button>
              </div>
            </a-card>
          </div>

          <div class="main-area">
            <a-card :bordered="false" class="content-card">
              <template #title>
                <div class="card-header">
                  <div class="card-title-left">
                    <ThunderboltOutlined class="card-icon" />
                    <span>技能列表</span>
                    <span class="skill-stats">
                      (共 {{ filteredSkills.length }} 个，已安装 {{ installedCount }} 个)
                    </span>
                  </div>
                  <div class="card-title-right">
                    <a-input-search 
                      v-model:value="searchKeyword" 
                      placeholder="搜索技能名称、描述、标签..." 
                      style="width: 280px;"
                      @search="handleSearch"
                      allow-clear
                    />
                  </div>
                </div>
              </template>

              <div v-if="loading" class="loading-container">
                <a-spin size="large" />
              </div>

              <div v-else-if="filteredSkills.length === 0" class="empty-container">
                <a-empty description="暂无技能">
                  <a-button type="primary" @click="handleCreateSkill">创建新技能</a-button>
                </a-empty>
              </div>

              <div v-else class="skills-grid">
                <div 
                  v-for="skill in filteredSkills" 
                  :key="skill.name"
                  :class="['skill-card', { selected: selectedSkill?.name === skill.name, 'skill-installed': skill.is_installed }]"
                  @click="handleSelectSkill(skill)"
                >
                  <div class="skill-header">
                    <div class="skill-icon-wrapper">
                      <ToolOutlined class="skill-icon" />
                    </div>
                    <div class="skill-title">
                      <div class="skill-name">{{ skill.name }}</div>
                      <div class="skill-meta">
                        <span class="skill-version">v{{ skill.version }}</span>
                        <span class="skill-divider">•</span>
                        <span class="skill-author">{{ skill.author || 'Unknown' }}</span>
                      </div>
                    </div>
                    <div class="skill-badges">
                      <a-tag v-if="skill.is_bundled" color="blue">内置</a-tag>
                      <a-tag v-else-if="skill.is_installed" color="green">已安装</a-tag>
                      <a-tag v-else color="orange">未安装</a-tag>
                    </div>
                  </div>
                  <div class="skill-description">
                    {{ skill.description || '暂无描述' }}
                  </div>
                  <div class="skill-tags" v-if="skill.metadata?.hermes?.tags?.length">
                    <a-tag 
                      v-for="tag in skill.metadata.hermes.tags.slice(0, 3)" 
                      :key="tag"
                      color="default"
                    >
                      {{ tag }}
                    </a-tag>
                    <span v-if="skill.metadata.hermes.tags.length > 3" class="more-tags">
                      +{{ skill.metadata.hermes.tags.length - 3 }}
                    </span>
                  </div>
                  <div class="skill-footer">
                    <div class="skill-category">
                      <FolderOutlined /> {{ skill.category_name || skill.category }}
                    </div>
                    <div class="skill-actions">
                      <a-button 
                        v-if="skill.is_installed && !skill.is_bundled"
                        type="text" 
                        size="small"
                        @click.stop="handleUninstallSkill(skill)"
                      >
                        <DeleteOutlined /> 卸载
                      </a-button>
                      <a-button 
                        v-else-if="!skill.is_installed"
                        type="text" 
                        size="small"
                        @click.stop="handleInstallSkill(skill)"
                      >
                        <CloudDownloadOutlined /> 安装
                      </a-button>
                    </div>
                  </div>
                </div>
              </div>
            </a-card>
          </div>

          <div class="detail-panel" :class="{ expanded: selectedSkill }">
            <div v-if="selectedSkill" class="detail-content">
              <div class="detail-header">
                <div class="detail-icon-wrapper">
                  <ToolOutlined class="detail-icon" />
                </div>
                <div class="detail-header-info">
                  <div class="detail-name">{{ selectedSkill.name }}</div>
                  <div class="detail-meta">
                    <a-tag v-if="selectedSkill.is_bundled" color="blue">内置技能</a-tag>
                    <a-tag v-else-if="selectedSkill.is_installed" color="green">已安装</a-tag>
                    <a-tag v-else color="orange">未安装</a-tag>
                    <span class="detail-version">v{{ selectedSkill.version }}</span>
                  </div>
                </div>
                <a-button type="text" class="detail-close" @click="selectedSkill = null">
                  <CloseOutlined />
                </a-button>
              </div>

              <div class="detail-body">
                <div class="detail-section">
                  <div class="section-label">描述</div>
                  <div class="section-value">
                    {{ selectedSkill.description || '暂无描述' }}
                  </div>
                </div>

                <div class="detail-section">
                  <div class="section-label">分类</div>
                  <div class="section-value">
                    <a-tag>{{ selectedSkill.category_name || selectedSkill.category }}</a-tag>
                  </div>
                </div>

                <div class="detail-section">
                  <div class="section-label">作者</div>
                  <div class="section-value">
                    {{ selectedSkill.author || 'Unknown' }}
                  </div>
                </div>

                <div class="detail-section">
                  <div class="section-label">许可证</div>
                  <div class="section-value">
                    {{ selectedSkill.license || 'Unknown' }}
                  </div>
                </div>

                <div class="detail-section" v-if="selectedSkill.metadata?.hermes?.tags?.length">
                  <div class="section-label">标签</div>
                  <div class="section-value">
                    <a-tag 
                      v-for="tag in selectedSkill.metadata.hermes.tags" 
                      :key="tag"
                      color="blue"
                      style="margin-bottom: 4px;"
                    >
                      {{ tag }}
                    </a-tag>
                  </div>
                </div>

                <div class="detail-section" v-if="selectedSkill.usage_count !== undefined">
                  <div class="section-label">使用次数</div>
                  <div class="section-value">
                    {{ selectedSkill.usage_count }} 次
                  </div>
                </div>

                <div class="detail-section" v-if="selectedSkill.updated_at">
                  <div class="section-label">更新时间</div>
                  <div class="section-value">
                    {{ selectedSkill.updated_at }}
                  </div>
                </div>

                <div class="detail-section" v-if="selectedSkill.content">
                  <div class="section-label">技能内容</div>
                  <div class="section-value content-box">
                    <a-input-textarea 
                      v-model:value="selectedSkill.content" 
                      :rows="12"
                      readonly
                      class="content-textarea"
                    />
                  </div>
                </div>
              </div>

              <div class="detail-actions">
                <a-button 
                  v-if="selectedSkill.is_installed && !selectedSkill.is_bundled"
                  type="default" 
                  @click="handleUpdateSkill(selectedSkill)"
                  :loading="actionLoading"
                >
                  <ReloadOutlined /> 更新
                </a-button>
                <a-button 
                  v-if="selectedSkill.is_installed && !selectedSkill.is_bundled"
                  type="default" 
                  danger
                  @click="handleUninstallSkill(selectedSkill)"
                  :loading="actionLoading"
                >
                  <DeleteOutlined /> 卸载
                </a-button>
                <a-button 
                  v-else-if="!selectedSkill.is_installed"
                  type="primary" 
                  @click="handleInstallSkill(selectedSkill)"
                  :loading="actionLoading"
                >
                  <CloudDownloadOutlined /> 安装
                </a-button>
              </div>
            </div>
            <div v-else class="detail-empty">
              <ToolOutlined class="empty-detail-icon" />
              <div class="empty-detail-text">点击左侧技能卡片查看详情</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <a-modal
      v-model:open="createModalVisible"
      title="创建新技能"
      width="600px"
      :footer="null"
    >
      <a-form
        :model="createForm"
        :label-col="{ span: 5 }"
        :wrapper-col="{ span: 19 }"
        layout="vertical"
      >
        <a-form-item label="技能名称" required>
          <a-input v-model:value="createForm.name" placeholder="输入技能名称" />
        </a-form-item>
        <a-form-item label="描述" required>
          <a-textarea v-model:value="createForm.description" placeholder="输入技能描述" :rows="2" />
        </a-form-item>
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="分类">
              <a-select v-model:value="createForm.category" placeholder="选择分类" allow-clear>
                <a-select-option v-for="cat in skillList?.categories || []" :key="cat.name" :value="cat.name">
                  {{ cat.display_name }}
                </a-select-option>
                <a-select-option value="custom">自定义</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="版本">
              <a-input v-model:value="createForm.version" placeholder="1.0.0" />
            </a-form-item>
          </a-col>
        </a-row>
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="作者">
              <a-input v-model:value="createForm.author" placeholder="输入作者名称" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="许可证">
              <a-input v-model:value="createForm.license" placeholder="MIT, Apache-2.0 等" />
            </a-form-item>
          </a-col>
        </a-row>
        <a-form-item label="标签">
          <a-select 
            v-model:value="createForm.tags" 
            mode="tags"
            style="width: 100%"
            placeholder="输入标签后按回车添加"
          />
        </a-form-item>
        <a-form-item label="技能内容" required>
          <a-textarea 
            v-model:value="createForm.content" 
            placeholder="输入技能内容（Markdown 格式）"
            :rows="10"
            :show-count="true"
          />
        </a-form-item>
      </a-form>
      <template #footer>
        <div class="modal-footer">
          <a-button @click="createModalVisible = false">取消</a-button>
          <a-button type="primary" @click="handleSubmitCreate" :loading="createLoading">创建</a-button>
        </div>
      </template>
    </a-modal>

    <a-modal
      v-model:open="availableModalVisible"
      title="浏览可用技能"
      width="800px"
      :footer="null"
    >
      <div class="available-skills-header">
        <a-input-search 
          v-model:value="availableSearchKeyword" 
          placeholder="搜索可用技能..."
          style="width: 300px;"
          @search="searchAvailableSkills"
        />
        <a-button @click="refreshAvailableSkills" :loading="availableLoading">
          <ReloadOutlined /> 刷新
        </a-button>
      </div>
      <div class="available-skills-list" v-if="availableLoading">
        <a-spin size="large" />
      </div>
      <div class="available-skills-list" v-else-if="availableSkills.length === 0">
        <a-empty description="暂无可用技能" />
      </div>
      <div class="available-skills-list" v-else>
        <a-card 
          v-for="skill in filteredAvailableSkills" 
          :key="skill.name"
          :bordered="false"
          class="available-skill-card"
        >
          <div class="available-skill-header">
            <div class="available-skill-icon">
              <ToolOutlined />
            </div>
            <div class="available-skill-info">
              <div class="available-skill-name">{{ skill.name }}</div>
              <div class="available-skill-meta">
                <span class="available-skill-version">v{{ skill.version }}</span>
                <span class="available-skill-divider">•</span>
                <span class="available-skill-author">{{ skill.author }}</span>
              </div>
            </div>
            <div class="available-skill-action">
              <a-tag v-if="skill.is_installed" color="green">已安装</a-tag>
              <a-button 
                v-else
                type="primary" 
                size="small"
                @click="handleInstallAvailableSkill(skill)"
              >
                <CloudDownloadOutlined /> 安装
              </a-button>
            </div>
          </div>
          <div class="available-skill-description">
            {{ skill.description }}
          </div>
          <div class="available-skill-category">
            <FolderOutlined /> {{ skill.category }}
          </div>
        </a-card>
      </div>
    </a-modal>
  </MainLayout>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import {
  ToolOutlined,
  ReloadOutlined,
  PlusOutlined,
  AppstoreOutlined,
  ThunderboltOutlined,
  InfoCircleOutlined,
  CloudDownloadOutlined,
  DeleteOutlined,
  FolderOutlined,
  CloseOutlined,
} from '@ant-design/icons-vue'
import type { 
  Skill, 
  SkillListResponse,
  AvailableSkill,
  SkillCreateParams
} from '@/types'
import MainLayout from '@/components/MainLayout.vue'
import { hermesApi } from '@/api/hermes'

const loading = ref(false)
const actionLoading = ref(false)
const createLoading = ref(false)
const availableLoading = ref(false)

const skillList = ref<SkillListResponse | null>(null)
const selectedCategory = ref('')
const searchKeyword = ref('')
const selectedSkill = ref<Skill | null>(null)

const createModalVisible = ref(false)
const createForm = ref<SkillCreateParams>({
  name: '',
  description: '',
  content: '',
  category: '',
  version: '1.0.0',
  author: '',
  license: 'MIT',
  tags: [],
})

const availableModalVisible = ref(false)
const availableSearchKeyword = ref('')
const availableSkills = ref<AvailableSkill[]>([])

const totalSkillsCount = computed(() => {
  if (!skillList.value?.categories) return 0
  return skillList.value.categories.reduce((sum, cat) => sum + cat.skill_count, 0)
})

const filteredSkills = computed<Skill[]>(() => {
  if (!skillList.value?.skills) return []
  
  let skills = [...skillList.value.skills]
  
  if (selectedCategory.value) {
    skills = skills.filter(s => s.category === selectedCategory.value)
  }
  
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    skills = skills.filter(s => 
      s.name.toLowerCase().includes(keyword) ||
      s.description.toLowerCase().includes(keyword) ||
      s.metadata?.hermes?.tags?.some(t => t.toLowerCase().includes(keyword))
    )
  }
  
  skills.sort((a, b) => {
    const aInstalled = a.is_installed ? 0 : 1
    const bInstalled = b.is_installed ? 0 : 1
    if (aInstalled !== bInstalled) {
      return aInstalled - bInstalled
    }
    
    const aBundled = a.is_bundled ? 0 : 1
    const bBundled = b.is_bundled ? 0 : 1
    if (aBundled !== bBundled) {
      return aBundled - bBundled
    }
    
    return (a.name || '').localeCompare(b.name || '')
  })
  
  return skills
})

const installedCount = computed(() => {
  return filteredSkills.value.filter(s => s.is_installed).length
})

const filteredAvailableSkills = computed(() => {
  if (!availableSearchKeyword.value) return availableSkills.value
  const keyword = availableSearchKeyword.value.toLowerCase()
  return availableSkills.value.filter(s => 
    s.name.toLowerCase().includes(keyword) ||
    s.description.toLowerCase().includes(keyword)
  )
})

const fetchSkills = async () => {
  loading.value = true
  try {
    const res = await hermesApi.getSkills({
      category: selectedCategory.value || undefined,
      search: searchKeyword.value || undefined,
    })
    if (res.code === 200) {
      skillList.value = res.data
    } else {
      message.error(res.message || '获取技能列表失败')
    }
  } catch (error) {
    console.error('Failed to fetch skills:', error)
    message.error('获取技能列表失败')
  } finally {
    loading.value = false
  }
}

const handleRefresh = () => {
  fetchSkills()
}

const handleSelectSkill = (skill: Skill) => {
  selectedSkill.value = skill
}

const handleSearch = () => {
  fetchSkills()
}

const handleCreateSkill = () => {
  createForm.value = {
    name: '',
    description: '',
    content: '',
    category: '',
    version: '1.0.0',
    author: '',
    license: 'MIT',
    tags: [],
  }
  createModalVisible.value = true
}

const handleSubmitCreate = async () => {
  if (!createForm.value.name || !createForm.value.description || !createForm.value.content) {
    message.warning('请填写必填字段')
    return
  }
  
  createLoading.value = true
  try {
    const res = await hermesApi.createSkill(createForm.value)
    if (res.code === 200) {
      message.success('技能创建成功')
      createModalVisible.value = false
      fetchSkills()
    } else {
      message.error(res.message || '创建失败')
    }
  } catch (error) {
    console.error('Failed to create skill:', error)
    message.error('创建技能失败')
  } finally {
    createLoading.value = false
  }
}

const handleInstallSkill = async (skill: Skill) => {
  actionLoading.value = true
  try {
    const res = await hermesApi.installSkill({
      skill_name: skill.name,
      category: skill.category,
      version: skill.version,
    })
    if (res.code === 200) {
      message.success('安装成功')
      fetchSkills()
    } else {
      message.error(res.message || '安装失败')
    }
  } catch (error) {
    console.error('Failed to install skill:', error)
    message.error('安装技能失败')
  } finally {
    actionLoading.value = false
  }
}

const handleUninstallSkill = async (skill: Skill) => {
  message.confirm({
    title: '确认卸载',
    content: `确定要卸载技能 "${skill.name}" 吗？`,
    okText: '卸载',
    okType: 'danger',
    cancelText: '取消',
    async onOk() {
      actionLoading.value = true
      try {
        const res = await hermesApi.uninstallSkill(skill.name)
        if (res.code === 200) {
          message.success('卸载成功')
          if (selectedSkill.value?.name === skill.name) {
            selectedSkill.value = null
          }
          fetchSkills()
        } else {
          message.error(res.message || '卸载失败')
        }
      } catch (error) {
        console.error('Failed to uninstall skill:', error)
        message.error('卸载技能失败')
      } finally {
        actionLoading.value = false
      }
    },
  })
}

const handleUpdateSkill = async (skill: Skill) => {
  actionLoading.value = true
  try {
    const res = await hermesApi.updateSkill(skill.name)
    if (res.code === 200) {
      message.success('更新成功')
      fetchSkills()
    } else {
      message.error(res.message || '更新失败')
    }
  } catch (error) {
    console.error('Failed to update skill:', error)
    message.error('更新技能失败')
  } finally {
    actionLoading.value = false
  }
}

const handleBrowseAvailable = () => {
  availableModalVisible.value = true
  refreshAvailableSkills()
}

const refreshAvailableSkills = async () => {
  availableLoading.value = true
  try {
    const res = await hermesApi.browseAvailableSkills()
    if (res.code === 200) {
      availableSkills.value = (res.data as AvailableSkill[]) || []
    }
  } catch (error) {
    console.error('Failed to browse available skills:', error)
    message.error('获取可用技能列表失败')
  } finally {
    availableLoading.value = false
  }
}

const searchAvailableSkills = () => {
}

const handleInstallAvailableSkill = async (skill: AvailableSkill) => {
  try {
    const res = await hermesApi.installSkill({
      skill_name: skill.name,
      category: skill.category,
      version: skill.version,
    })
    if (res.code === 200) {
      message.success('安装成功')
      refreshAvailableSkills()
      fetchSkills()
    } else {
      message.error(res.message || '安装失败')
    }
  } catch (error) {
    console.error('Failed to install skill:', error)
    message.error('安装技能失败')
  }
}

watch(selectedCategory, () => {
  fetchSkills()
})

onMounted(() => {
  fetchSkills()
})
</script>

<style scoped>
.hermes-page {
  min-height: 100%;
  padding: 24px;
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

.header-right {
  display: flex;
  gap: 12px;
}

.page-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.content-layout {
  display: flex;
  gap: 24px;
  min-height: calc(100vh - 200px);
}

.sidebar {
  width: 260px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.sidebar-card {
  margin-bottom: 0;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #1d2129;
  margin-bottom: 12px;
}

.section-icon {
  font-size: 16px;
  color: #165DFF;
}

.category-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.category-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.category-item:hover {
  background: #f2f3f5;
}

.category-item.active {
  background: #e8f3ff;
  color: #165DFF;
}

.category-name {
  font-size: 14px;
  color: inherit;
}

.category-count {
  font-size: 12px;
  color: #86909c;
  background: #f2f3f5;
  padding: 2px 8px;
  border-radius: 10px;
}

.category-item.active .category-count {
  background: rgba(22, 93, 255, 0.15);
  color: #165DFF;
}

.action-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.action-list :deep(.ant-btn) {
  justify-content: flex-start;
  text-align: left;
}

.main-area {
  flex: 1;
  min-width: 0;
}

.content-card {
  margin-bottom: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.card-title-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.card-icon {
  font-size: 18px;
  color: #165DFF;
}

.skill-stats {
  font-size: 13px;
  color: #86909c;
  font-weight: normal;
  margin-left: 8px;
}

.card-title-right {
  display: flex;
  align-items: center;
}

.loading-container,
.empty-container {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 60px 0;
}

.skills-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
}

.skill-card {
  padding: 16px;
  border-radius: 12px;
  border: 1px solid #e5e6eb;
  cursor: pointer;
  transition: all 0.2s;
  background: #fff;
}

.skill-card:hover {
  border-color: #165DFF;
  box-shadow: 0 4px 16px rgba(22, 93, 255, 0.1);
}

.skill-card.selected {
  border-color: #165DFF;
  background: linear-gradient(135deg, rgba(22, 93, 255, 0.03) 0%, rgba(114, 46, 209, 0.02) 100%);
}

.skill-card.skill-installed {
  border-left: 3px solid #00b42a;
}

.skill-header {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 12px;
}

.skill-icon-wrapper {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: linear-gradient(135deg, #e8f3ff 0%, #d6e8ff 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.skill-icon {
  font-size: 20px;
  color: #165DFF;
}

.skill-title {
  flex: 1;
  min-width: 0;
}

.skill-name {
  font-size: 15px;
  font-weight: 600;
  color: #1d2129;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.skill-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #86909c;
}

.skill-divider {
  color: #c9cdd4;
}

.skill-badges {
  flex-shrink: 0;
}

.skill-description {
  font-size: 13px;
  color: #4e5969;
  line-height: 1.5;
  margin-bottom: 12px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.skill-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-bottom: 12px;
}

.more-tags {
  font-size: 12px;
  color: #86909c;
  padding: 0 4px;
}

.skill-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 12px;
  border-top: 1px solid #f2f3f5;
}

.skill-category {
  font-size: 12px;
  color: #86909c;
  display: flex;
  align-items: center;
  gap: 4px;
}

.skill-actions {
  display: flex;
  gap: 8px;
}

.detail-panel {
  width: 0;
  overflow: hidden;
  transition: width 0.3s ease;
  border-left: 0;
}

.detail-panel.expanded {
  width: 380px;
  flex-shrink: 0;
  border-left: 1px solid #e5e6eb;
  margin-left: -1px;
}

.detail-content {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 20px;
  background: #fff;
}

.detail-header {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  padding-bottom: 20px;
  border-bottom: 1px solid #f2f3f5;
  position: relative;
}

.detail-icon-wrapper {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  background: linear-gradient(135deg, #e8f3ff 0%, #d6e8ff 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.detail-icon {
  font-size: 28px;
  color: #165DFF;
}

.detail-header-info {
  flex: 1;
  min-width: 0;
}

.detail-name {
  font-size: 18px;
  font-weight: 700;
  color: #1d2129;
  margin-bottom: 8px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.detail-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.detail-version {
  font-size: 13px;
  color: #86909c;
}

.detail-close {
  position: absolute;
  top: 0;
  right: 0;
  padding: 4px;
}

.detail-body {
  flex: 1;
  overflow-y: auto;
  padding: 20px 0;
}

.detail-section {
  margin-bottom: 20px;
}

.section-label {
  font-size: 13px;
  color: #86909c;
  margin-bottom: 8px;
}

.section-value {
  font-size: 14px;
  color: #1d2129;
  line-height: 1.5;
}

.content-box {
  background: #f7f8fa;
  border-radius: 8px;
  padding: 12px;
}

.content-textarea {
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 12px;
  background: transparent;
  border: none;
}

.detail-actions {
  display: flex;
  gap: 12px;
  padding-top: 20px;
  border-top: 1px solid #f2f3f5;
}

.detail-empty {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  height: 100%;
  background: #fff;
  padding: 20px;
}

.empty-detail-icon {
  font-size: 64px;
  color: #c9cdd4;
  margin-bottom: 16px;
}

.empty-detail-text {
  font-size: 14px;
  color: #86909c;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding-top: 16px;
}

.available-skills-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.available-skills-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: 500px;
  overflow-y: auto;
}

.available-skill-card {
  background: #f7f8fa;
  border-radius: 12px;
  padding: 16px;
  transition: all 0.2s;
}

.available-skill-card:hover {
  background: #e8f3ff;
}

.available-skill-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 8px;
}

.available-skill-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  color: #fa8c16;
  flex-shrink: 0;
}

.available-skill-info {
  flex: 1;
  min-width: 0;
}

.available-skill-name {
  font-size: 15px;
  font-weight: 600;
  color: #1d2129;
  margin-bottom: 4px;
}

.available-skill-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #86909c;
}

.available-skill-divider {
  color: #c9cdd4;
}

.available-skill-action {
  flex-shrink: 0;
}

.available-skill-description {
  font-size: 13px;
  color: #4e5969;
  line-height: 1.5;
  margin-bottom: 8px;
}

.available-skill-category {
  font-size: 12px;
  color: #86909c;
  display: flex;
  align-items: center;
  gap: 4px;
}
</style>
