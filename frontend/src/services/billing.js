import { request } from './http'
import { PAYMENT_METHOD } from './constants/businessEnums'
import { normalizeListResult } from './adapters/listAdapter'
import { getConfigValue } from './config/configStore'

export const DEFAULT_PAYMENT_METHOD = PAYMENT_METHOD.MOCK

export function resolvePaymentMethod(catalog) {
  return catalog?.payment_method || getConfigValue('payment.default_method', DEFAULT_PAYMENT_METHOD)
}

export const billing = {
  wallet() {
    return request('GET', '/api/billing/wallet/')
  },
  catalog() {
    return request('GET', '/api/billing/catalog/')
  },
  rechargePackages() {
    return request('GET', '/api/billing/recharge/packages/')
  },
  createRechargeOrder(packageId, paymentMethod) {
    return request('POST', '/api/billing/recharge/orders/', {
      data: { package_id: packageId, payment_method: paymentMethod || resolvePaymentMethod() },
    })
  },
  mockPayRecharge(orderNo) {
    return request('POST', `/api/billing/recharge/orders/${orderNo}/mock_pay/`)
  },
  async ledger(page = 1, entryType = '') {
    const data = await request('GET', '/api/billing/ledger/', {
      params: { page, page_size: 20, entry_type: entryType || undefined },
    })
    return normalizeListResult(data)
  },
}
