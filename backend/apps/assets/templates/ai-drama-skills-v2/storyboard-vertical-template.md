# 竖屏分镜表标准模板

> 适用场景：抖音/快手/微信小程序短剧、竖屏漫剧、短视频内容制作
> 画幅比例：9:16（1080x1920 / 720x1280）

---

## 一、竖屏分镜表基础结构

### 1.1 标准分镜表模板

| 镜号 | 景别 | 机位 | 画面内容 | 台词 | AI提示词 | 角色锚定 | 时长 | 备注 |
|------|------|------|----------|------|----------|----------|------|------|
| S01 | | | | | | | | |
| S02 | | | | | | | | |
| S03 | | | | | | | | |

### 1.2 字段说明

| 字段 | 说明 | 填写规范 |
|------|------|----------|
| **镜号** | 镜头编号 | 格式：S01、S02...按顺序递增 |
| **景别** | 镜头景别 | 特写/近景/中景/全景（详见景别对照表） |
| **机位** | 拍摄角度 | 平视/俯视/仰视/侧拍/斜拍 |
| **画面内容** | 场景描述 | 包含人物动作、表情、环境要素 |
| **台词** | 角色对白 | 格式：角色名：台词内容 |
| **AI提示词** | 生成提示词 | Midjourney/SD格式（详见AI参数栏） |
| **角色锚定** | 角色一致性标识 | 角色ID+特征描述（详见角色锚定系统） |
| **时长** | 镜头时长 | 格式：X秒（建议单镜2-8秒） |
| **备注** | 特殊说明 | 音效、转场、特效等补充信息 |

---

## 二、竖屏专属参数

### 2.1 画幅规格

```
┌─────────────────────┐
│      顶部安全区      │  ← 预留80px（状态栏/标题）
├─────────────────────┤
│                     │
│                     │
│      画面主体区      │  ← 核心内容区域
│                     │
│                     │
├─────────────────────┤
│    字幕预留区        │  ← 预留120px（字幕/互动按钮）
└─────────────────────┘

标准尺寸：1080 x 1920px（9:16）
安全区域：顶部80px + 底部120px
有效画面：1080 x 1720px
```

### 2.2 安全区域标注

| 区域 | 位置 | 预留高度 | 用途 |
|------|------|----------|------|
| 顶部安全区 | 0-80px | 80px | 状态栏、账号信息、标题 |
| 画面主体区 | 80-1800px | 1720px | 核心画面内容 |
| 字幕预留区 | 1800-1920px | 120px | 字幕、互动按钮、进度条 |

### 2.3 人物站位建议

#### 单人构图

```
┌─────────────────────┐
│      顶部安全区      │
├─────────────────────┤
│                     │
│    ┌─────────┐      │
│    │         │      │
│    │  人物   │      │  ← 居中/偏左/偏右
│    │         │      │
│    └─────────┘      │
│                     │
├─────────────────────┤
│    字幕预留区        │
└─────────────────────┘
```

#### 双人对角构图

```
┌─────────────────────┐
│      顶部安全区      │
├─────────────────────┤
│  ┌───┐              │
│  │ A │              │  ← 人物A（左上）
│  └───┘              │
│              ┌───┐  │
│              │ B │  │  ← 人物B（右下）
│              └───┘  │
├─────────────────────┤
│    字幕预留区        │
└─────────────────────┘
```

#### 三角形构图

```
┌─────────────────────┐
│      顶部安全区      │
├─────────────────────┤
│      ┌───┐          │
│      │ A │          │  ← 主角（中心偏上）
│      └───┘          │
│  ┌───┐    ┌───┐     │
│  │ B │    │ C │     │  ← 配角（两侧下方）
│  └───┘    └───┘     │
├─────────────────────┤
│    字幕预留区        │
└─────────────────────┘
```

### 2.4 竖屏构图原则

| 构图类型 | 适用场景 | 要点说明 |
|----------|----------|----------|
| **居中构图** | 单人特写、情感戏 | 人物居中，头顶预留空间 |
| **三分构图** | 对话场景、互动 | 人物位于画面1/3处 |
| **对角构图** | 冲突场景、追逐 | 增加画面动感与张力 |
| **前景遮挡** | 偷窥视角、悬念 | 利用前景增加层次感 |
| **留白构图** | 情绪渲染、独白 | 大面积留白强化氛围 |

---

## 三、AI生成参数栏

### 3.1 Midjourney提示词格式

```
[主体描述] + [动作/表情] + [场景环境] + [光影效果] + [风格参数] + [画幅参数]
```

#### 标准格式模板

```
A young woman with long black hair, crying, sitting alone in a dark room, dim lighting, cinematic style, dramatic atmosphere --ar 9:16 --v 6.0 --style raw --s 250
```

#### Midjourney参数说明

| 参数 | 说明 | 推荐值 |
|------|------|--------|
| `--ar 9:16` | 竖屏画幅比例 | 必填 |
| `--v 6.0` | 版本号 | v6.0（最新） |
| `--style raw` | 风格模式 | 写实风格使用 |
| `--s 250` | 风格化程度 | 100-750（默认250） |
| `--c 15` | 混乱度 | 0-100（控制多样性） |
| `--seed` | 随机种子 | 保持一致性时固定 |

### 3.2 Stable Diffusion提示词格式

```
正向提示词: (主体), (动作), (场景), (光影), (画质词), (风格词)
负向提示词: (排除内容), (画质优化)
```

#### 标准格式模板

```
正向提示词:
(best quality), (masterpiece), (highres), 
1girl, long black hair, crying, sitting alone, 
dark room, dim lighting, cinematic lighting, 
dramatic atmosphere, emotional, 
vertical composition, 9:16 aspect ratio

负向提示词:
(worst quality), (low quality), (normal quality),
(lowres), (bad anatomy), (text), (watermark),
(horizontal), (wide shot)
```

### 3.3 AI参数记录表

| 参数项 | Midjourney | Stable Diffusion |
|--------|------------|------------------|
| **画幅比例** | --ar 9:16 | 512x896 / 768x1344 |
| **Seed值** | --seed XXXXX | Seed: XXXXX |
| **模型** | --v 6.0 | Model: XXX.safetensors |
| **LoRA** | 不支持 | <lora:XXX:0.8> |
| **采样器** | - | Euler a / DPM++ 2M |
| **采样步数** | - | 20-30 steps |
| **CFG Scale** | - | 7-12 |

### 3.4 角色锚定系统

#### 角色锚定编码规则

```
格式：[角色ID]_[性别]_[年龄段]_[发型]_[服装色]_[特征]

示例：
- PRO_M_25s_blackhair_suit_glasses  （男主：25岁短发黑西装戴眼镜）
- HER_F_22l_brownhair_dress_scar    （女主：22岁长发棕色连衣裙有疤痕）
```

#### 角色锚定表模板

| 角色ID | 角色名 | 性别 | 年龄 | 发型 | 服装 | 特征 | 参考图Seed |
|--------|--------|------|------|------|------|------|------------|
| PRO001 | 林晨 | 男 | 28 | 短发黑 | 黑西装 | 戴眼镜 | 12345678 |
| HER001 | 苏婉 | 女 | 24 | 长发棕 | 白连衣裙 | 左眼角痣 | 87654321 |
| SUP001 | 王总 | 男 | 45 | 秃顶 | 灰西装 | 胖 | 11223344 |

---

## 四、景别与机位对照表

### 4.1 竖屏适用景别

| 景别 | 取景范围 | 竖屏特点 | 适用场景 | 时长建议 |
|------|----------|----------|----------|----------|
| **大特写** | 眼睛/嘴唇/局部 | 极具冲击力 | 情绪高潮、关键道具 | 1-2秒 |
| **特写** | 面部为主 | 情感传达强 | 情绪戏、对话反应 | 2-4秒 |
| **近景** | 胸部以上 | 适合单人 | 日常对话、独白 | 3-5秒 |
| **中景** | 腰部以上 | 展示上半身动作 | 互动、手势动作 | 3-6秒 |
| **中全景** | 膝盖以上 | 兼顾人物与环境 | 走动、小范围动作 | 4-8秒 |
| **全景** | 全身 | 竖屏需注意构图 | 入场、全身展示 | 4-8秒 |
| **远景** | 环境为主 | 人物较小 | 场景交代、氛围 | 3-6秒 |

### 4.2 竖屏适用机位

| 机位 | 角度说明 | 视觉效果 | 适用场景 |
|------|----------|----------|----------|
| **平视** | 与视线平行 | 真实、自然 | 日常对话、叙事 |
| **俯视** | 从上往下拍 | 渺小、压抑、可爱 | 弱势角色、萌系 |
| **仰视** | 从下往上拍 | 高大、威严、压迫 | 强势角色、英雄 |
| **侧拍** | 90度侧面 | 轮廓清晰、艺术感 | 颜值展示、对话 |
| **斜拍** | 倾斜角度 | 不安、紧张、动感 | 冲突、悬疑 |
| **过肩** | 越过肩膀 | 代入感、对话 | 双人对话场景 |

### 4.3 景别-机位组合建议

| 场景类型 | 推荐组合 | 说明 |
|----------|----------|------|
| 情感独白 | 特写+平视 | 强化情感共鸣 |
| 对峙冲突 | 近景+仰视/俯视对比 | 强弱对比 |
| 悬疑揭秘 | 特写+斜拍 | 增加不安感 |
| 甜蜜互动 | 中景+平视/侧拍 | 自然温馨 |
| 追逐打斗 | 全景+斜拍 | 动感强烈 |
| 角色登场 | 全景+仰视 | 气场展示 |

---

## 五、完整示例：3分钟短剧场景分镜表

### 5.1 场景信息

| 项目 | 内容 |
|------|------|
| **剧名** | 《错位时空》 |
| **集数** | 第3集 |
| **场景** | S03-雨夜告白 |
| **时长** | 3分钟 |
| **角色** | 林晨（男主）、苏婉（女主） |
| **地点** | 公交站台（雨夜） |
| **氛围** | 虐心、浪漫、遗憾 |

### 5.2 角色锚定信息

| 角色ID | 角色名 | 外貌特征 | 服装 | Seed |
|--------|--------|----------|------|------|
| PRO001 | 林晨 | 男，28岁，短发，黑框眼镜 | 深蓝色风衣 | 24681357 |
| HER001 | 苏婉 | 女，24岁，长发微卷，左眼角泪痣 | 米白色针织衫 | 13579246 |

### 5.3 完整分镜表

| 镜号 | 景别 | 机位 | 画面内容 | 台词 | AI提示词 | 角色锚定 | 时长 | 备注 |
|------|------|------|----------|------|----------|----------|------|------|
| S01 | 远景 | 平视 | 雨夜城市街道，霓虹灯倒映在积水路面，公交站台孤零零立在路边 | （无） | Rainy night city street, neon lights reflecting on wet pavement, bus stop shelter standing alone, urban atmosphere, cinematic lighting, moody --ar 9:16 --v 6.0 --s 300 | - | 4秒 | 雨声+城市环境音 |
| S02 | 全景 | 平视 | 林晨站在公交站台下，撑着黑色雨伞，望向远方，雨水顺着伞沿滴落 | （无） | A man standing at bus stop under black umbrella, dark blue trench coat, black frame glasses, looking into distance, rain drops falling, melancholic atmosphere, cinematic --ar 9:16 --v 6.0 --seed 24681357 | PRO001 | 5秒 | 钢琴配乐渐入 |
| S03 | 中景 | 侧拍 | 林晨侧脸特写，眼镜上沾着水雾，眼神落寞 | 林晨（内心独白）：如果当初我没有放开她的手... | Side profile of Asian man, glasses with water mist, melancholic eyes, rain in background, emotional, cinematic portrait --ar 9:16 --v 6.0 --seed 24681357 | PRO001 | 4秒 | 独白配音 |
| S04 | 特写 | 平视 | 林晨的手紧紧握着一把旧钥匙，指节发白 | （无） | Close up of man's hand gripping an old key tightly, knuckles white, rain drops, emotional detail --ar 9:16 --v 6.0 --s 350 | - | 2秒 | 道具特写 |
| S05 | 全景 | 仰视 | 苏婉从雨幕中跑来，全身湿透，停在站台对面 | （脚步声+喘息声） | Young woman running through rain, wet hair and clothes, stopping at bus stop, dramatic entrance, rain pouring --ar 9:16 --v 6.0 --seed 13579246 | HER001 | 3秒 | 慢动作+雨声加强 |
| S06 | 近景 | 平视 | 林晨猛然抬头，眼中闪过震惊与不敢置信 | 林晨：苏...苏婉？ | Asian man looking up with shock and disbelief, dramatic lighting, emotional reaction --ar 9:16 --v 6.0 --seed 24681357 | PRO001 | 2秒 | 音乐高潮点 |
| S07 | 中景 | 平视 | 两人隔着雨幕对望，空气仿佛凝固 | （无） | Two people looking at each other across rain, emotional tension, cinematic composition, dramatic atmosphere --ar 9:16 --v 6.0 --s 400 | PRO001+HER001 | 4秒 | 音乐停顿 |
| S08 | 特写 | 平视 | 苏婉脸上雨水与泪水交织，嘴角微微颤抖 | 苏婉：好久不见...林晨 | Close up of young woman's face, rain and tears mixed, trembling lips, emotional crying, beauty shot --ar 9:16 --v 6.0 --seed 13579246 | HER001 | 3秒 | 情绪高潮 |
| S09 | 近景 | 侧拍 | 林晨向前迈出一步，却又停在原地，手微微抬起又放下 | 林晨：你...这些年过得好吗？ | Asian man stepping forward but stopping, hand reaching out then pulling back, hesitation, emotional conflict --ar 9:16 --v 6.0 --seed 24681357 | PRO001 | 4秒 | |
| S10 | 中景 | 平视 | 苏婉低下头，双手紧握在一起，身体微微颤抖 | 苏婉：不好...一点都不好... | Young woman looking down, hands clasped together, body trembling, sadness, rain falling --ar 9:16 --v 6.0 --seed 13579246 | HER001 | 3秒 | |
| S11 | 特写 | 仰视 | 苏婉抬起头，眼中含泪，直视林晨 | 苏婉：你明明说过会永远陪着我！ | Young woman looking up with tears in eyes, direct gaze, heartbroken expression, emotional outburst --ar 9:16 --v 6.0 --seed 13579246 | HER001 | 2秒 | 情绪爆发 |
| S12 | 近景 | 平视 | 林晨闭上眼睛，一滴泪水滑落 | 林晨：对不起... | Asian man closing eyes, single tear falling, regret, emotional moment --ar 9:16 --v 6.0 --seed 24681357 | PRO001 | 3秒 | 音乐悲伤高潮 |
| S13 | 全景 | 俯视 | 公交车灯光划破雨幕，缓缓驶来 | （公交车进站声） | Bus headlights cutting through rain, bus approaching bus stop, dramatic lighting, rainy night --ar 9:16 --v 6.0 --s 300 | - | 3秒 | 转场音效 |
| S14 | 中景 | 平视 | 苏婉转身看向公交车，又回头看了林晨最后一眼 | 苏婉：这趟车...我等了三年 | Young woman turning to look at bus, then looking back one last time, bittersweet expression --ar 9:16 --v 6.0 --seed 13579246 | HER001 | 4秒 | 双关台词 |
| S15 | 全景 | 平视 | 苏婉走上公交车，车门关闭，公交车驶离 | （无） | Young woman boarding bus, bus doors closing, bus driving away, rain, lonely figure left behind --ar 9:16 --v 6.0 --s 350 | HER001 | 5秒 | |
| S16 | 中景 | 侧拍 | 林晨独自站在站台上，雨伞滑落，任由雨水打湿全身 | （无） | Man standing alone at bus stop, umbrella fallen, rain soaking clothes, heartbreak, loneliness, dramatic --ar 9:16 --v 6.0 --seed 24681357 | PRO001 | 5秒 | 音乐渐弱 |
| S17 | 特写 | 平视 | 地上的旧钥匙被雨水冲刷，渐渐被水淹没 | （无） | Old key on wet ground, being washed by rain, symbolic, emotional, detail shot --ar 9:16 --v 6.0 --s 400 | - | 3秒 | 象征镜头 |
| S18 | 远景 | 平视 | 公交车尾灯消失在雨幕尽头，只剩空荡荡的街道 | （无） | Bus tail lights disappearing into rain, empty street, melancholic ending, rainy night city --ar 9:16 --v 6.0 --s 300 | - | 4秒 | 淡出+字幕 |

### 5.4 场景统计

| 统计项 | 数值 |
|--------|------|
| 总镜头数 | 18个 |
| 总时长 | 约60秒（核心场景） |
| 特写镜头 | 6个（33%） |
| 近景镜头 | 3个（17%） |
| 中景镜头 | 5个（28%） |
| 全景/远景 | 4个（22%） |
| 主要角色出镜 | 林晨12镜、苏婉9镜 |

---

## 六、使用说明

### 6.1 模板使用流程

1. **填写场景信息**：确定场景编号、角色、地点、氛围
2. **建立角色锚定**：为每个角色分配ID和Seed值
3. **编写分镜内容**：按镜头顺序填写各字段
4. **生成AI提示词**：根据画面内容编写提示词
5. **导出执行**：交付制作团队或AI生成

### 6.2 注意事项

- 竖屏构图需特别注意字幕预留区，避免重要内容被遮挡
- AI提示词需保持角色一致性，使用固定Seed值
- 单镜时长建议控制在2-8秒，保持节奏感
- 情绪高潮镜头优先使用特写+平视组合
- 转场镜头预留足够时长，便于后期剪辑

### 6.3 导出格式

| 格式 | 用途 | 说明 |
|------|------|------|
| Markdown | 文档存档 | 本模板格式 |
| Excel | 制作执行 | 便于批量生成 |
| PDF | 客户交付 | 正式文档格式 |

---

## 七、附录

### 7.1 常用AI提示词词汇库

#### 光影效果

```
cinematic lighting    电影感光效
dramatic lighting     戏剧性光效
soft lighting         柔和光效
rim lighting          轮廓光
backlighting          逆光
golden hour           黄金时刻
blue hour             蓝调时刻
neon lights           霓虹灯光
```

#### 情绪氛围

```
melancholic           忧郁的
romantic              浪漫的
tense                 紧张的
mysterious            神秘的
heartbreaking         心碎的
nostalgic             怀旧的
hopeful               充满希望的
```

#### 画质词

```
(best quality)        最佳画质
(masterpiece)         杰作级
(highres)             高分辨率
(8k)                  8K分辨率
(ultra detailed)      超精细
(photorealistic)      照片级真实
```

### 7.2 竖屏分镜检查清单

- [ ] 画幅比例设置为9:16
- [ ] 顶部安全区预留80px
- [ ] 底部字幕区预留120px
- [ ] 角色锚定Seed值已固定
- [ ] AI提示词包含画幅参数
- [ ] 单镜时长在2-8秒范围内
- [ ] 情绪高潮镜头使用特写
- [ ] 转场镜头时长充足
- [ ] 音效/配乐标注完整

---

**模板版本**：v1.0
**更新日期**：2024年
**适用范围**：竖屏短剧、漫剧、短视频制作
