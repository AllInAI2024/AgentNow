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
                    <span>{{ currentCategoryName }}</span>
                    <span class="skill-stats">
                      (共 <span class="stat-total">{{ currentCategoryTotal }}</span> 个)
                    </span>
                  </div>
                  <div class="card-title-right">
                    <a-input-search 
                      v-model:value="searchKeyword" 
                      placeholder="搜索技能名称、描述、标签..." 
                      style="width: 280px;"
                      @search="handleSearch"
                      @clear="handleSearch"
                      allow-clear
                    />
                  </div>
                </div>
              </template>

              <div v-if="loading" class="loading-container">
                <a-spin size="large" />
              </div>

              <div v-else-if="filteredSkills.length === 0" class="empty-container">
                <a-empty :description="searchKeyword ? '未找到匹配的技能' : '该分类暂无技能'">
                  <a-button v-if="!searchKeyword" type="primary" @click="handleCreateSkill">创建新技能</a-button>
                </a-empty>
              </div>

              <div v-else class="skills-grid">
                <div 
                  v-for="skill in filteredSkills" 
                  :key="skill.name"
                  :class="['skill-card', { 'skill-bundled': skill.is_bundled }]"
                  @click="handleViewSkill(skill)"
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
                        v-if="!skill.is_bundled"
                        type="text" 
                        size="small"
                        @click.stop="handleUpdateSkill(skill)"
                      >
                        <ReloadOutlined /> 更新
                      </a-button>
                    </div>
                  </div>
                </div>
              </div>
            </a-card>
          </div>
        </div>
      </div>
    </div>

    <a-modal
      v-model:open="detailModalVisible"
      :title="null"
      :footer="null"
      width="900px"
      :closable="true"
      class="skill-detail-modal"
    >
      <div v-if="selectedSkill" class="skill-detail-content">
        <div class="detail-header">
          <div class="detail-icon-wrapper">
            <ToolOutlined class="detail-icon" />
          </div>
          <div class="detail-header-info">
            <div class="detail-name">{{ selectedSkill.name }}</div>
            <div class="detail-meta">
              <a-tag v-if="selectedSkill.is_bundled" color="blue">内置技能</a-tag>
              <a-tag v-else color="green">自定义技能</a-tag>
              <span class="detail-version">v{{ selectedSkill.version }}</span>
              <span class="detail-author">{{ selectedSkill.author || 'Unknown' }}</span>
            </div>
          </div>
        </div>

        <a-tabs v-model:activeKey="activeTab" class="detail-tabs">
          <a-tab-pane key="content" tab="技能内容 (SKILL.md)">
            <div class="tab-content">
              <div v-if="selectedSkill.content" class="skill-md-content">
                <pre><code>{{ selectedSkill.content }}</code></pre>
              </div>
              <div v-else class="empty-content">
                <a-empty description="该技能暂无内容" />
              </div>
            </div>
          </a-tab-pane>

          <a-tab-pane key="info" tab="基本信息">
            <div class="tab-content info-tab">
              <div class="info-section">
                <div class="info-item">
                  <div class="info-label">描述</div>
                  <div class="info-value">{{ selectedSkill.description || '暂无描述' }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">分类</div>
                  <div class="info-value">
                    <a-tag>{{ selectedSkill.category_name || selectedSkill.category }}</a-tag>
                  </div>
                </div>
                <div class="info-item">
                  <div class="info-label">版本</div>
                  <div class="info-value">{{ selectedSkill.version }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">作者</div>
                  <div class="info-value">{{ selectedSkill.author || 'Unknown' }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">许可证</div>
                  <div class="info-value">{{ selectedSkill.license || 'Unknown' }}</div>
                </div>
                <div class="info-item" v-if="selectedSkill.updated_at">
                  <div class="info-label">更新时间</div>
                  <div class="info-value">{{ selectedSkill.updated_at }}</div>
                </div>
              </div>
            </div>
          </a-tab-pane>

          <a-tab-pane key="related" tab="相关技能" v-if="hasRelatedSkills">
            <div class="tab-content">
              <div class="related-skills">
                <a-tag 
                  v-for="skill in relatedSkillNames" 
                  :key="skill"
                  color="blue"
                  class="related-tag"
                >
                  {{ skill }}
                </a-tag>
              </div>
              <div v-if="!hasRelatedSkills" class="empty-content">
                <a-empty description="该技能没有相关技能" />
              </div>
            </div>
          </a-tab-pane>

          <a-tab-pane key="versions" tab="版本管理">
            <div class="tab-content versions-tab">
              <div class="version-info">
                <div class="current-version">
                  <div class="version-label">当前版本</div>
                  <div class="version-number">v{{ selectedSkill.version }}</div>
                </div>
                <div class="version-divider"></div>
                <div class="latest-version" :class="{ 'has-update': hasUpdate }">
                  <div class="version-label">最新版本</div>
                  <div class="version-number">
                    <span v-if="hasUpdate" class="update-available">
                      v{{ latestVersion }}
                      <Tag color="orange">有更新</Tag>
                    </span>
                    <span v-else>v{{ selectedSkill.version }} (已是最新)</span>
                  </div>
                </div>
              </div>

              <div class="version-actions">
                <a-button 
                  type="primary" 
                  @click="handleUpgradeSkill"
                  :loading="actionLoading"
                  :disabled="!hasUpdate"
                >
                  <CloudDownloadOutlined /> 升级到最新版本
                </a-button>
                <a-button 
                  @click="handleCheckUpdate"
                  :loading="checkingUpdate"
                >
                  <ReloadOutlined /> 检查更新
                </a-button>
              </div>

              <div class="update-history" v-if="updateHistory.length > 0">
                <div class="history-title">更新历史</div>
                <div class="history-list">
                  <div v-for="item in updateHistory" :key="item.version" class="history-item">
                    <div class="history-version">v{{ item.version }}</div>
                    <div class="history-date">{{ item.date }}</div>
                    <div class="history-changes">{{ item.changes }}</div>
                  </div>
                </div>
              </div>
            </div>
          </a-tab-pane>
        </a-tabs>

        <div class="detail-actions">
          <a-button 
            v-if="!selectedSkill.is_bundled"
            type="default" 
            @click="handleUpgradeSkill"
            :loading="actionLoading"
            :disabled="!hasUpdate"
          >
            <ReloadOutlined /> 升级
          </a-button>
          <a-button 
            v-if="!selectedSkill.is_bundled"
            type="default" 
            danger
            @click="handleUninstallSkill"
            :loading="actionLoading"
          >
            <DeleteOutlined /> 卸载
          </a-button>
          <a-button 
            type="primary" 
            @click="handleEditSkill"
          >
            <EditOutlined /> 编辑
          </a-button>
        </div>
      </div>
    </a-modal>

    <a-modal
      v-model:open="createModalVisible"
      title="创建新技能"
      width="600px"
      :footer="null"
    >
      <a-form
        :model="createForm"
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
            :rows="15"
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
import { message, Tag } from 'ant-design-vue'
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
  EditOutlined,
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
const checkingUpdate = ref(false)

const skillList = ref<SkillListResponse | null>(null)
const selectedCategory = ref('')
const searchKeyword = ref('')
const selectedSkill = ref<Skill | null>(null)
const detailModalVisible = ref(false)
const activeTab = ref('content')

const hasUpdate = ref(false)
const latestVersion = ref('')
const updateHistory = ref<{ version: string; date: string; changes: string }[]>([])

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

const currentCategoryName = computed(() => {
  if (!selectedCategory.value) return '技能列表'
  const cat = skillList.value?.categories?.find(c => c.name === selectedCategory.value)
  return cat?.display_name || selectedCategory.value
})

const currentCategoryTotal = computed(() => {
  if (!selectedCategory.value) return totalSkillsCount.value
  const cat = skillList.value?.categories?.find(c => c.name === selectedCategory.value)
  return cat?.skill_count || 0
})

const filteredSkills = computed<Skill[]>(() => {
  if (!skillList.value?.items) return []
  
  let skills = [...skillList.value.items]
  
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    skills = skills.filter(s => 
      s.name.toLowerCase().includes(keyword) ||
      s.description.toLowerCase().includes(keyword) ||
      s.metadata?.hermes?.tags?.some(t => t.toLowerCase().includes(keyword))
    )
  }
  
  skills.sort((a, b) => {
    const aBundled = a.is_bundled ? 0 : 1
    const bBundled = b.is_bundled ? 0 : 1
    if (aBundled !== bBundled) {
      return aBundled - bBundled
    }
    
    return (a.name || '').localeCompare(b.name || '')
  })
  
  return skills
})

const filteredAvailableSkills = computed(() => {
  if (!availableSearchKeyword.value) return availableSkills.value
  const keyword = availableSearchKeyword.value.toLowerCase()
  return availableSkills.value.filter(s => 
    s.name.toLowerCase().includes(keyword) ||
    s.description.toLowerCase().includes(keyword)
  )
})

const hasRelatedSkills = computed(() => {
  return selectedSkill.value?.metadata?.hermes?.related_skills?.length || 0
})

const relatedSkillNames = computed(() => {
  return selectedSkill.value?.metadata?.hermes?.related_skills || []
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

const handleViewSkill = (skill: Skill) => {
  selectedSkill.value = skill
  detailModalVisible.value = true
  activeTab.value = 'content'
  hasUpdate.value = false
  latestVersion.value = skill.version || ''
}

const handleSearch = () => {
  fetchSkills()
}

const handleCreateSkill = () => {
  createForm.value = {
    name: '',
    description: '',
    content: '',
    category: selectedCategory.value || '',
    version: '1.0.0',
    author: '',
    license: 'MIT',
    tags: [],
  }
  createModalVisible.value = true
}

const handleEditSkill = () => {
  if (!selectedSkill.value) return
  
  createForm.value = {
    name: selectedSkill.value.name,
    description: selectedSkill.value.description || '',
    content: selectedSkill.value.content || '',
    category: selectedSkill.value.category || '',
    version: selectedSkill.value.version || '1.0.0',
    author: selectedSkill.value.author || '',
    license: selectedSkill.value.license || 'MIT',
    tags: selectedSkill.value.metadata?.hermes?.tags || [],
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

const handleUninstallSkill = async () => {
  if (!selectedSkill.value) return
  
  message.confirm({
    title: '确认卸载',
    content: `确定要卸载技能 "${selectedSkill.value.name}" 吗？`,
    okText: '卸载',
    okType: 'danger',
    cancelText: '取消',
    async onOk() {
      actionLoading.value = true
      try {
        const res = await hermesApi.uninstallSkill(selectedSkill.value!.name)
        if (res.code === 200) {
          message.success('卸载成功')
          detailModalVisible.value = false
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

const handleUpgradeSkill = async () => {
  if (!selectedSkill.value) return
  await handleUpdateSkill(selectedSkill.value)
}

const handleCheckUpdate = async () => {
  if (!selectedSkill.value) return
  
  checkingUpdate.value = true
  try {
    hasUpdate.value = false
    latestVersion.value = selectedSkill.value.version || ''
    
    message.info('版本检查功能开发中...')
  } catch (error) {
    console.error('Failed to check update:', error)
  } finally {
    checkingUpdate.value = false
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

watch([selectedCategory, searchKeyword], () => {
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

.stat-total {
  color: #86909c;
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
  grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
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

.skill-card.skill-bundled {
  border-left: 3px solid #165DFF;
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

:deep(.skill-detail-modal .ant-modal-body) {
  padding: 0;
}

.skill-detail-content {
  display: flex;
  flex-direction: column;
  max-height: 70vh;
}

.detail-header {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 24px 24px 16px;
  border-bottom: 1px solid #f2f3f5;
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
  font-size: 20px;
  font-weight: 700;
  color: #1d2129;
  margin-bottom: 8px;
}

.detail-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.detail-version {
  font-size: 14px;
  color: #4e5969;
}

.detail-author {
  font-size: 14px;
  color: #4e5969;
}

.detail-tabs {
  flex: 1;
  overflow: hidden;
}

.tab-content {
  max-height: 400px;
  overflow-y: auto;
  padding: 16px;
}

.skill-md-content {
  background: #1e1e1e;
  border-radius: 8px;
  padding: 16px;
}

.skill-md-content pre {
  margin: 0;
  padding: 0;
}

.skill-md-content code {
  color: #d4d4d4;
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 13px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}

.empty-content {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 40px 0;
}

.info-tab {
  padding: 16px 24px;
}

.info-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.info-label {
  font-size: 13px;
  color: #86909c;
  font-weight: 500;
}

.info-value {
  font-size: 14px;
  color: #1d2129;
}

.related-skills {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.related-tag {
  cursor: pointer;
}

.versions-tab {
  padding: 16px 24px;
}

.version-info {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 32px;
  padding: 24px 0;
  background: #f7f8fa;
  border-radius: 12px;
  margin-bottom: 24px;
}

.current-version,
.latest-version {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.version-label {
  font-size: 13px;
  color: #86909c;
}

.version-number {
  font-size: 24px;
  font-weight: 700;
  color: #1d2129;
}

.update-available {
  color: #fa8c16;
}

.version-divider {
  width: 2px;
  height: 40px;
  background: #e5e6eb;
}

.version-actions {
  display: flex;
  justify-content: center;
  gap: 12px;
  margin-bottom: 24px;
}

.update-history {
  border-top: 1px solid #f2f3f5;
  padding-top: 20px;
}

.history-title {
  font-size: 14px;
  font-weight: 600;
  color: #1d2129;
  margin-bottom: 12px;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.history-item {
  padding: 12px;
  background: #f7f8fa;
  border-radius: 8px;
}

.history-version {
  font-size: 14px;
  font-weight: 600;
  color: #165DFF;
  margin-bottom: 4px;
}

.history-date {
  font-size: 12px;
  color: #86909c;
  margin-bottom: 8px;
}

.history-changes {
  font-size: 13px;
  color: #4e5969;
}

.detail-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 24px;
  border-top: 1px solid #f2f3f5;
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
