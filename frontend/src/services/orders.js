import { request } from './http'
import { DEFAULT_PAYMENT_METHOD } from './billing'
import { normalizeOrder } from './adapters/businessAdapters'
import { coerceUnwrappedArray } from './adapters/listAdapter'

export const orders = {
  /** 订单列表，可选按状态过滤 status: 'paid' | 'pending' | 'cancelled' */
  async list(status) {
    const data = await request('GET', '/api/orders/', {
      params: status ? { status } : undefined,
    })
    return coerceUnwrappedArray(data, normalizeOrder)
  },
  async detail(orderId) {
    const data = await request('GET', `/api/orders/${orderId}/`)
    return normalizeOrder(data)
  },
  async createOrder({ plan_id, payment_method = DEFAULT_PAYMENT_METHOD }) {
    const data = await request('POST', '/api/orders/create_order/', {
      data: { plan_id, payment_method },
    })
    return normalizeOrder(data.order)
  },
  async mockPay(orderNo) {
    const data = await request('POST', '/api/orders/mock_pay/', { data: { order_no: orderNo } })
    return normalizeOrder(data.order)
  },
  cancel(orderNo) {
    return request('POST', '/api/orders/cancel/', { data: { order_no: orderNo } })
  },
  async latest() {
    const data = await request('GET', '/api/orders/me/latest/')
    return data ? normalizeOrder(data) : null
  },
}
