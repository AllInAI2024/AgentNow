<template>
  <a-config-provider :theme="themeConfig">
    <router-view />
  </a-config-provider>
</template>

<script setup lang="ts">
import { theme } from 'ant-design-vue'

const themeConfig = {
  algorithm: theme.defaultAlgorithm,
  token: {
    colorPrimary: '#165DFF',
    colorSuccess: '#00B42A',
    colorWarning: '#FF7D00',
    colorError: '#F53F3F',
    colorInfo: '#165DFF',
    
    colorTextBase: '#1d2129',
    colorText: '#1d2129',
    colorTextSecondary: '#4e5969',
    colorTextTertiary: '#86909c',
    colorTextQuaternary: '#c9cdd4',
    
    colorFillAlter: '#f7f8fa',
    colorFillContent: '#f2f3f5',
    colorFillContentHover: '#e5e6eb',
    colorFill: '#c9cdd4',
    colorFillHover: '#86909c',
    
    colorBgBase: '#ffffff',
    colorBgContainer: '#ffffff',
    colorBgElevated: '#ffffff',
    colorBgLayout: '#f7f8fa',
    colorBgSpotlight: '#1d2129',
    colorBgBlur: 'rgba(255, 255, 255, 0.85)',
    
    colorBorder: '#e5e6eb',
    colorBorderSecondary: '#f2f3f5',
    
    colorPrimaryBg: '#E8F3FF',
    colorPrimaryBgHover: '#D0E8FF',
    colorPrimaryBorder: '#91CAFF',
    colorPrimaryBorderHover: '#4080FF',
    colorPrimaryHover: '#4080FF',
    colorPrimaryActive: '#0E42D2',
    colorPrimaryTextHover: '#4080FF',
    colorPrimaryText: '#165DFF',
    colorPrimaryTextActive: '#0E42D2',
    
    colorSuccessBg: '#E8FFEA',
    colorSuccessBgHover: '#D3FFD7',
    colorSuccessBorder: '#95E5A0',
    colorSuccessBorderHover: '#51D561',
    colorSuccessHover: '#23C343',
    colorSuccessActive: '#009A29',
    colorSuccessTextHover: '#23C343',
    colorSuccessText: '#00B42A',
    colorSuccessTextActive: '#009A29',
    
    colorWarningBg: '#FFF7E8',
    colorWarningBgHover: '#FFECC8',
    colorWarningBorder: '#FFD591',
    colorWarningBorderHover: '#FFB55C',
    colorWarningHover: '#FF9A2E',
    colorWarningActive: '#E46B00',
    colorWarningTextHover: '#FF9A2E',
    colorWarningText: '#FF7D00',
    colorWarningTextActive: '#E46B00',
    
    colorErrorBg: '#FFF1F0',
    colorErrorBgHover: '#FFD9D8',
    colorErrorBorder: '#FFA8A3',
    colorErrorBorderHover: '#FF7D78',
    colorErrorHover: '#FF6565',
    colorErrorActive: '#CB2634',
    colorErrorTextHover: '#FF6565',
    colorErrorText: '#F53F3F',
    colorErrorTextActive: '#CB2634',
    
    colorInfoBg: '#E8F3FF',
    colorInfoBgHover: '#D0E8FF',
    colorInfoBorder: '#91CAFF',
    colorInfoBorderHover: '#4080FF',
    colorInfoHover: '#4080FF',
    colorInfoActive: '#0E42D2',
    colorInfoTextHover: '#4080FF',
    colorInfoText: '#165DFF',
    colorInfoTextActive: '#0E42D2',
    
    borderRadius: 8,
    borderRadiusXS: 4,
    borderRadiusSM: 6,
    borderRadiusLG: 12,
    borderRadiusOuter: 8,
    
    fontSize: 14,
    fontSizeSM: 12,
    fontSizeLG: 16,
    fontSizeXL: 18,
    fontSizeHeading1: 38,
    fontSizeHeading2: 30,
    fontSizeHeading3: 24,
    fontSizeHeading4: 20,
    fontSizeHeading5: 16,
    
    fontWeightStrong: 600,
    
    controlHeight: 40,
    controlHeightSM: 32,
    controlHeightLG: 48,
    
    controlOutline: 'rgba(22, 93, 255, 0.1)',
    controlOutlineWidth: 3,
    
    motionDurationFast: '0.15s',
    motionDurationMid: '0.2s',
    motionDurationSlow: '0.3s',
    
    motionEaseInOut: 'cubic-bezier(0.645, 0.045, 0.355, 1)',
    motionEaseOut: 'cubic-bezier(0.215, 0.61, 0.355, 1)',
    motionEaseIn: 'cubic-bezier(0.55, 0.055, 0.675, 0.19)',
    motionEaseOutBack: 'cubic-bezier(0.12, 0.4, 0.29, 1.46)',
    
    wireframe: false,
  },
  components: {
    Button: {
      borderRadius: 8,
      controlHeight: 40,
      controlHeightLG: 48,
      controlHeightSM: 32,
      primaryShadow: '0 4px 16px rgba(22, 93, 255, 0.35)',
      dangerShadow: '0 4px 16px rgba(245, 63, 63, 0.35)',
    },
    Input: {
      borderRadius: 8,
      controlHeight: 40,
      controlHeightLG: 48,
      controlHeightSM: 32,
      hoverBorderColor: '#c9cdd4',
      activeBorderColor: '#165DFF',
      activeShadow: '0 0 0 3px rgba(22, 93, 255, 0.1)',
    },
    InputNumber: {
      borderRadius: 8,
      controlHeight: 40,
    },
    Select: {
      borderRadius: 8,
      controlHeight: 40,
      controlHeightLG: 48,
      controlHeightSM: 32,
      optionSelectedBg: '#E8F3FF',
    },
    DatePicker: {
      borderRadius: 8,
      controlHeight: 40,
    },
    TimePicker: {
      borderRadius: 8,
      controlHeight: 40,
    },
    Card: {
      borderRadiusLG: 16,
      borderRadius: 12,
      borderRadiusSM: 8,
      boxShadow: '0 2px 8px rgba(0, 0, 0, 0.04)',
      boxShadowSecondary: '0 2px 8px rgba(0, 0, 0, 0.04)',
    },
    Modal: {
      borderRadiusLG: 16,
      borderRadius: 12,
      boxShadow: '0 8px 32px rgba(0, 0, 0, 0.12)',
    },
    Dropdown: {
      borderRadiusLG: 12,
      borderRadius: 10,
      boxShadow: '0 8px 32px rgba(0, 0, 0, 0.12)',
    },
    Menu: {
      borderRadius: 8,
      itemBorderRadius: 8,
      subMenuItemBorderRadius: 8,
    },
    Table: {
      borderRadius: 12,
      borderRadiusLG: 16,
      borderRadiusSM: 8,
      headerBg: '#f7f8fa',
      headerColor: '#4e5969',
      headerSortActiveBg: '#E8F3FF',
      headerSortHoverBg: '#f2f3f5',
      rowHoverBg: '#f7f8fa',
      borderColor: '#e5e6eb',
    },
    Tabs: {
      borderRadius: 8,
      horizontalItemPadding: '16px 0',
      horizontalMargin: '0 0 0 24px',
      verticalItemPadding: '12px 16px',
      verticalMargin: '0',
      itemActiveColor: '#165DFF',
      itemHoverColor: '#4080FF',
      itemSelectedColor: '#165DFF',
      inkBarColor: '#165DFF',
    },
    Alert: {
      borderRadiusLG: 12,
      borderRadius: 10,
      borderRadiusSM: 8,
      successBgColor: '#E8FFEA',
      infoBgColor: '#E8F3FF',
      warningBgColor: '#FFF7E8',
      errorBgColor: '#FFF1F0',
      successBorderColor: '#95E5A0',
      infoBorderColor: '#91CAFF',
      warningBorderColor: '#FFD591',
      errorBorderColor: '#FFA8A3',
    },
    Message: {
      borderRadius: 8,
      contentBg: '#ffffff',
    },
    Notification: {
      borderRadiusLG: 16,
      borderRadius: 12,
    },
    Tag: {
      borderRadiusSM: 4,
      borderRadius: 6,
      borderRadiusLG: 8,
    },
    Avatar: {
      borderRadius: 8,
      borderRadiusLG: 12,
      borderRadiusSM: 6,
    },
    Badge: {
      borderRadius: 6,
      borderRadiusLG: 8,
      statusSize: 6,
    },
    Tooltip: {
      borderRadius: 8,
      borderRadiusLG: 12,
      colorBgSpotlight: '#1d2129',
    },
    Popover: {
      borderRadiusLG: 12,
      borderRadius: 10,
    },
    Progress: {
      borderRadius: 4,
    },
    Switch: {
      borderRadius: 100,
    },
    Checkbox: {
      borderRadius: 6,
    },
    Radio: {
      buttonBorderRadius: 8,
    },
    Form: {
      labelColor: '#4e5969',
      labelRequiredMarkColor: '#F53F3F',
    },
    Pagination: {
      borderRadius: 8,
      itemActiveBg: '#165DFF',
      itemActiveColorDisabled: '#ffffff',
      itemActiveBgDisabled: '#c9cdd4',
    },
    Upload: {
      borderRadius: 8,
    },
    Empty: {
      colorTextBase: '#86909c',
    },
    Result: {
      titleFontSize: 24,
      subtitleFontSize: 14,
      iconFontSize: 72,
    },
    Statistic: {
      titleFontSize: 14,
      titleColor: '#86909c',
      contentFontSize: 30,
      contentColor: '#1d2129',
    },
    Timeline: {
      dotBg: '#165DFF',
    },
    Divider: {
      colorSplit: '#e5e6eb',
    },
    Spin: {
      colorPrimary: '#165DFF',
    },
    Collapse: {
      headerBg: '#f7f8fa',
      headerPadding: '16px 24px',
      contentPadding: '16px 24px',
      borderRadiusLG: 12,
    },
    Drawer: {
      borderRadiusLG: 16,
      borderRadius: 12,
    },
    List: {
      borderRadiusLG: 12,
    },
    Descriptions: {
      labelBg: '#f7f8fa',
    },
    Cascader: {
      borderRadius: 8,
      controlHeight: 40,
    },
    TreeSelect: {
      borderRadius: 8,
      controlHeight: 40,
    },
    Transfer: {
      borderRadiusLG: 12,
    },
    Steps: {
      titleFontSize: 14,
      descriptionFontSize: 12,
    },
    Rate: {
      starColor: '#FF7D00',
      starBg: '#e5e6eb',
    },
    Slider: {
      borderRadius: 6,
      handleSize: 14,
      trackBg: '#e5e6eb',
      trackHeight: 4,
    },
    Image: {
      borderRadiusLG: 16,
      borderRadius: 12,
      borderRadiusSM: 8,
    },
    QRCode: {
      borderRadius: 8,
    },
    Tour: {
      borderRadiusLG: 16,
    },
    Calendar: {
      borderRadiusLG: 16,
    },
    Popconfirm: {
      borderRadiusLG: 12,
    },
  },
}
</script>

<style>
html, body, #app {
  margin: 0;
  padding: 0;
  height: 100%;
  width: 100%;
}

:root {
  --primary-color: #165DFF;
  --success-color: #00B42A;
  --warning-color: #FF7D00;
  --error-color: #F53F3F;
  --info-color: #165DFF;
}

* {
  scrollbar-width: thin;
  scrollbar-color: #c9cdd4 transparent;
}

*::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

*::-webkit-scrollbar-track {
  background: transparent;
}

*::-webkit-scrollbar-thumb {
  background: #c9cdd4;
  border-radius: 3px;
  transition: background 0.2s ease;
}

*::-webkit-scrollbar-thumb:hover {
  background: #86909c;
}

::selection {
  background-color: #E8F3FF;
  color: #165DFF;
}

.ant-btn-primary {
  background: linear-gradient(135deg, #165DFF 0%, #0E42D2 100%);
  border: none;
  box-shadow: 0 4px 16px rgba(22, 93, 255, 0.35);
  transition: all 0.25s ease;
}

.ant-btn-primary:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(22, 93, 255, 0.45);
  background: linear-gradient(135deg, #4080FF 0%, #165DFF 100%);
}

.ant-btn-primary:active:not(:disabled) {
  transform: translateY(0);
  box-shadow: 0 2px 8px rgba(22, 93, 255, 0.3);
}

.ant-btn-default {
  border-color: #e5e6eb;
  transition: all 0.2s ease;
}

.ant-btn-default:hover:not(:disabled) {
  color: #165DFF;
  border-color: #165DFF;
}

.ant-input-affix-wrapper,
.ant-input {
  transition: all 0.2s ease;
}

.ant-input-affix-wrapper:hover,
.ant-input:hover {
  border-color: #c9cdd4;
}

.ant-input-affix-wrapper-focused,
.ant-input:focus {
  border-color: #165DFF !important;
  box-shadow: 0 0 0 3px rgba(22, 93, 255, 0.1) !important;
}

.ant-card {
  transition: all 0.3s ease;
}

.ant-card-hoverable:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
}

.ant-dropdown-menu {
  padding: 8px;
}

.ant-dropdown-menu-item,
.ant-dropdown-menu-submenu-title {
  border-radius: 8px;
  margin: 4px 0;
  padding: 8px 12px;
}

.ant-modal-content {
  overflow: hidden;
}

.ant-modal-header {
  padding: 20px 24px;
  border-bottom: 1px solid #e5e6eb;
}

.ant-modal-body {
  padding: 24px;
}

.ant-modal-footer {
  padding: 16px 24px;
  border-top: 1px solid #e5e6eb;
}

.ant-message-notice-content {
  padding: 12px 16px;
  border-radius: 10px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
}

.ant-alert {
  border-radius: 10px;
  border: none;
}

.ant-alert-with-description {
  padding: 16px;
}

.ant-tag {
  border-radius: 6px;
}

.ant-tooltip-inner {
  border-radius: 8px;
  padding: 8px 12px;
  font-size: 13px;
}

.ant-popover-inner {
  border-radius: 10px;
}

.ant-popover-inner-content {
  padding: 16px;
}

.ant-progress-bg {
  border-radius: 4px;
}

.ant-switch {
  border-radius: 100px;
}

.ant-select-selector {
  transition: all 0.2s ease;
}

.ant-select-selector:hover {
  border-color: #c9cdd4 !important;
}

.ant-select-focused .ant-select-selector {
  border-color: #165DFF !important;
  box-shadow: 0 0 0 3px rgba(22, 93, 255, 0.1) !important;
}

.ant-table {
  border-radius: 12px;
  overflow: hidden;
}

.ant-table-thead > tr > th {
  background: #f7f8fa;
  font-weight: 600;
  color: #4e5969;
}

.ant-table-tbody > tr:hover > td {
  background: #f7f8fa;
}

.ant-pagination-item {
  border-radius: 8px;
  transition: all 0.2s ease;
}

.ant-pagination-item:hover {
  border-color: #165DFF;
}

.ant-pagination-item-active {
  background: linear-gradient(135deg, #165DFF 0%, #0E42D2 100%);
  border-color: transparent;
}

.ant-pagination-item-active a {
  color: white;
}

.ant-empty-image {
  margin-bottom: 12px;
}

.ant-empty-description {
  color: #86909c;
}

.ant-avatar {
  display: flex;
  align-items: center;
  justify-content: center;
}

.ant-avatar.ant-avatar-icon {
  font-size: 18px;
}

.ant-dropdown-open .ant-dropdown-trigger {
  background: #f2f3f5;
}

.ant-menu-item {
  transition: all 0.2s ease;
}

.ant-menu-item:not(.ant-menu-item-selected):hover {
  background: #f7f8fa;
}

.ant-menu-item-selected {
  background: #E8F3FF !important;
  color: #165DFF !important;
}

.ant-tabs-tab:hover {
  color: #4080FF;
}

.ant-tabs-tab-active {
  color: #165DFF;
}

.ant-tabs-ink-bar {
  background: #165DFF;
}

.ant-collapse-header {
  transition: all 0.2s ease;
}

.ant-collapse-header:hover {
  background: #f7f8fa;
}

.ant-checkbox-wrapper:hover .ant-checkbox-inner,
.ant-checkbox:hover .ant-checkbox-inner,
.ant-checkbox-input:focus + .ant-checkbox-inner {
  border-color: #165DFF;
}

.ant-checkbox-checked .ant-checkbox-inner {
  background-color: #165DFF;
  border-color: #165DFF;
}

.ant-radio-wrapper:hover .ant-radio-inner,
.ant-radio:hover .ant-radio-inner,
.ant-radio-input:focus + .ant-radio-inner {
  border-color: #165DFF;
}

.ant-radio-checked .ant-radio-inner {
  border-color: #165DFF;
}

.ant-radio-checked .ant-radio-inner::after {
  background-color: #165DFF;
}

.ant-switch-checked {
  background: #165DFF;
}

.ant-rate-star-full {
  color: #FF7D00;
}

.ant-rate-star-half .ant-rate-star-first {
  color: #FF7D00;
}

.ant-slider-track {
  background: #165DFF;
}

.ant-slider-handle::after {
  box-shadow: 0 0 0 2px #165DFF;
}

.ant-slider:hover .ant-slider-handle::after {
  box-shadow: 0 0 0 2px #165DFF;
}

.ant-upload-drag {
  border-radius: 12px;
  transition: all 0.2s ease;
}

.ant-upload-drag:hover {
  border-color: #165DFF;
}

.ant-upload-drag.ant-upload-drag-hover {
  border-color: #165DFF;
  background: #E8F3FF;
}

.ant-timeline-item-head {
  background-color: #165DFF;
}

.ant-result-success .ant-result-icon > .anticon {
  color: #00B42A;
}

.ant-result-error .ant-result-icon > .anticon {
  color: #F53F3F;
}

.ant-result-warning .ant-result-icon > .anticon {
  color: #FF7D00;
}

.ant-result-info .ant-result-icon > .anticon {
  color: #165DFF;
}

.ant-statistic-title {
  color: #86909c;
}

.ant-statistic-content {
  color: #1d2129;
}

.ant-descriptions-bordered .ant-descriptions-item-label {
  background-color: #f7f8fa;
}

.ant-drawer-content {
  border-radius: 16px 0 0 16px;
}

.ant-drawer-right .ant-drawer-content {
  border-radius: 16px 0 0 16px;
}

.ant-drawer-left .ant-drawer-content {
  border-radius: 0 16px 16px 0;
}

.ant-drawer-top .ant-drawer-content,
.ant-drawer-bottom .ant-drawer-content {
  border-radius: 0;
}

.ant-list-bordered {
  border-radius: 12px;
}

.ant-list-item:hover {
  background: #f7f8fa;
}

.ant-calendar-panel {
  border-radius: 16px;
}

.ant-calendar-today .ant-calendar-date {
  color: #165DFF;
  font-weight: 600;
}

.ant-calendar-selected-date .ant-calendar-date,
.ant-calendar-selected-start-date .ant-calendar-date,
.ant-calendar-selected-end-date .ant-calendar-date {
  background: #165DFF;
}

.ant-calendar-month-panel-selected-cell .ant-calendar-month-panel-month {
  background: #165DFF;
}

.ant-calendar-year-panel-selected-cell .ant-calendar-year-panel-year {
  background: #165DFF;
}

.ant-cascader-menu-item:hover {
  background: #f7f8fa;
}

.ant-cascader-menu-item-active {
  background: #E8F3FF;
  color: #165DFF;
}

.ant-tree-node-content-wrapper:hover {
  background-color: #f7f8fa;
}

.ant-tree-node-selected > .ant-tree-node-content-wrapper {
  background-color: #E8F3FF !important;
  color: #165DFF;
}

.ant-transfer-list {
  border-radius: 12px;
}

.ant-transfer-list-header {
  background: #f7f8fa;
  border-bottom: 1px solid #e5e6eb;
}

.ant-transfer-list-content-item:hover {
  background: #f7f8fa;
}

.ant-steps-item-finish .ant-steps-item-icon {
  background-color: #E8F3FF;
  border-color: #165DFF;
}

.ant-steps-item-finish .ant-steps-item-icon > .ant-steps-icon {
  color: #165DFF;
}

.ant-steps-item-process > .ant-steps-item-container > .ant-steps-item-icon {
  background: #165DFF;
  border-color: #165DFF;
}

.ant-steps-item-wait .ant-steps-item-icon {
  background-color: #ffffff;
  border-color: #c9cdd4;
}

.ant-steps-item-wait .ant-steps-item-icon > .ant-steps-icon {
  color: #c9cdd4;
}

.ant-badge-status-dot {
  width: 6px;
  height: 6px;
}

.ant-badge-status-success {
  background-color: #00B42A;
}

.ant-badge-status-warning {
  background-color: #FF7D00;
}

.ant-badge-status-error {
  background-color: #F53F3F;
}

.ant-badge-status-default {
  background-color: #86909c;
}

.ant-badge-status-processing {
  background-color: #165DFF;
}
</style>
