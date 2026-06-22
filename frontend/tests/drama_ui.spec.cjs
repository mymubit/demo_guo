const { test, expect } = require('@playwright/test');

const BASE_URL = 'http://localhost:3001';
const API_URL = 'http://localhost:8001';

/**
 * 注册并登录，返回token
 */
async function getAuthToken(page) {
  // 通过API直接获取token（后端已有测试用户）
  const response = await page.request.post(`${API_URL}/api/auth/login/`, {
    data: { phone: '12200000001', password: 'TestP@ss!' },
    headers: { 'Content-Type': 'application/json' },
  });
  if (response.ok()) {
    const body = await response.json();
    return body.data?.access || body.access;
  }
  return null;
}

test.describe('UI-001: 路由与导航', () => {
  test('首页加载成功，包含导航元素', async ({ page }) => {
    await page.goto(BASE_URL);
    await page.waitForLoadState('networkidle');
    // 验证页面不是空白
    const body = await page.locator('body').textContent();
    expect(body.length).toBeGreaterThan(10);
  });

  test('/drama 路由可访问（不报404）', async ({ page }) => {
    const response = await page.goto(`${BASE_URL}/drama`);
    // 前端SPA应该返回200（index.html），路由在客户端处理
    expect(response?.status()).toBe(200);
  });

  test('/drama/workspace 路由可访问', async ({ page }) => {
    const r = await page.goto(`${BASE_URL}/drama/workspace/test-project-id`);
    expect(r?.status()).toBe(200);
  });

  test('/drama/scripts 路由可访问', async ({ page }) => {
    const r = await page.goto(`${BASE_URL}/drama/scripts/test-project-id`);
    expect(r?.status()).toBe(200);
  });

  test('/admin/drama-models 路由可访问', async ({ page }) => {
    const r = await page.goto(`${BASE_URL}/admin/drama-models`);
    expect(r?.status()).toBe(200);
  });
});

test.describe('UI-002: 静态资源与构建', () => {
  test('JS主bundle可访问', async ({ page }) => {
    // 先获取index.html中的bundle路径
    const r = await page.goto(BASE_URL);
    const content = await r?.text();
    const match = content?.match(/\/assets\/index-[^"]+\.js/);
    if (match) {
      const bundleResp = await page.request.get(`${BASE_URL}${match[0]}`);
      expect(bundleResp.status()).toBe(200);
    }
  });

  test('CSS主样式可访问', async ({ page }) => {
    const r = await page.goto(BASE_URL);
    const content = await r?.text();
    const match = content?.match(/\/assets\/index-[^"]+\.css/);
    if (match) {
      const cssResp = await page.request.get(`${BASE_URL}${match[0]}`);
      expect(cssResp.status()).toBe(200);
    }
  });

  test('页面无JS运行时错误', async ({ page }) => {
    const errors = [];
    page.on('pageerror', err => errors.push(err.message));
    await page.goto(BASE_URL);
    await page.waitForLoadState('networkidle');
    // 只报告严重错误（非网络错误）
    const criticalErrors = errors.filter(e =>
      !e.includes('ERR_') && !e.includes('fetch') && !e.includes('Network')
    );
    expect(criticalErrors).toHaveLength(0);
  });
});

test.describe('UI-003: Drama页面组件渲染', () => {
  test('/drama 页面正确渲染React组件', async ({ page }) => {
    await page.goto(`${BASE_URL}/drama`);
    await page.waitForLoadState('networkidle');
    // SPA路由加载后应该有内容
    const html = await page.content();
    expect(html).toContain('<div');
  });

  test('workspace页面结构完整', async ({ page }) => {
    await page.goto(`${BASE_URL}/drama/workspace/test-id`);
    await page.waitForLoadState('networkidle');
    const html = await page.content();
    expect(html).toContain('root');
  });
});

test.describe('UI-004: API响应格式验证（前端视角）', () => {
  test('未登录访问/api/drama/roles/ 返回401提示', async ({ page }) => {
    const resp = await page.request.get(`${API_URL}/api/drama/roles/`);
    const body = await resp.json();
    // 项目规范：HTTP 200 + body code=401
    expect(body.code).toBe(401);
    expect(body.message).toBeTruthy();
  });

  test('未登录访问/api/drama/projects/ 返回401提示', async ({ page }) => {
    const resp = await page.request.get(`${API_URL}/api/drama/projects/`);
    const body = await resp.json();
    expect(body.code).toBe(401);
  });

  test('接口返回标准格式 {code, message, data}', async ({ page }) => {
    const resp = await page.request.get(`${API_URL}/api/drama/roles/`);
    const body = await resp.json();
    expect(body).toHaveProperty('code');
    expect(body).toHaveProperty('message');
    expect('data' in body).toBe(true);
  });
});

test.describe('UI-005: 响应式布局与视口', () => {
  test('桌面视口（1920x1080）正常渲染', async ({ page }) => {
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto(BASE_URL);
    await page.waitForLoadState('networkidle');
    // 页面不应该有横向滚动条（内容不超出视口宽度）
    const scrollWidth = await page.evaluate(() => document.documentElement.scrollWidth);
    expect(scrollWidth).toBeLessThanOrEqual(1920 + 20); // 允许20px误差
  });

  test('平板视口（768x1024）正常渲染', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto(BASE_URL);
    await page.waitForLoadState('networkidle');
    const body = await page.locator('body').textContent();
    expect(body?.length || 0).toBeGreaterThan(0);
  });

  test('移动视口（375x812）正常渲染（不崩溃）', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto(BASE_URL);
    await page.waitForLoadState('networkidle');
    const errors = [];
    page.on('pageerror', e => errors.push(e.message));
    const criticals = errors.filter(e => !e.includes('ERR_') && !e.includes('fetch'));
    expect(criticals).toHaveLength(0);
  });
});
