/** C 端内容运营 — 钩子类型与 Tab 说明（创作页 / 钩子库共用） */

export const HOOK_TYPE_OPTIONS = [
  {
    value: 'opening',
    label: '开场钩子',
    hint: '第 1 集开头抓眼球，如身份反差、冲突预告',
  },
  {
    value: 'reversal',
    label: '反转钩子',
    hint: '剧情拐点，如真相反转、关系逆转',
  },
  {
    value: 'suspense',
    label: '悬念钩子',
    hint: '集末留坑，引导观众点下一集',
  },
  {
    value: 'golden',
    label: '金句钩子',
    hint: '可传播的记忆点台词',
  },
  {
    value: 'climax',
    label: '高潮钩子',
    hint: '大场面、情绪爆发前的铺垫句',
  },
  {
    value: 'ending',
    label: '结尾钩子',
    hint: '全剧或篇章收束时的余韵句',
  },
]

export const CREATION_FORM_TAB_HINTS = {
  entries: '五种创作入口各自显示哪些输入框、标题与说明（与 C 端顶部 Tab 一一对应）',
  themes: '题材卡片名称、图标与是否启用',
  params: '预算档位、目标平台、集数滑块规则、竖屏/横屏等格式文案',
  copy: '与入口无关的通用区块标题（如「选择题材」「项目参数」）',
}

export const CREATION_FORM_TAB_SUMMARY = [
  {
    key: 'entries',
    title: '创作入口',
    desc: '用户选「从大纲写」「从小说改」等时，看到哪些字段',
  },
  {
    key: 'themes',
    title: '题材',
    desc: '都市、古装等卡片在 C 端的名称与样式',
  },
  {
    key: 'params',
    title: '项目参数',
    desc: '预算、平台、集数、格式等选项文案',
  },
  {
    key: 'copy',
    title: '区块标题',
    desc: '各表单区域的标题 / 副标题（全局）',
  },
]
